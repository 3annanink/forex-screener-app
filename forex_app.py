import time
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="Hybrid SMC Screener",
    page_icon="🧠",
    layout="wide",
)

st.markdown("""
<style>
    .main { padding: 1rem; }
    .stButton>button {
        width: 100%; height: 56px; font-size: 18px; font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; border-radius: 10px;
    }
    .stButton>button:hover { filter: brightness(1.08); }
    .card { padding: 18px; border-radius: 14px; margin: 14px 0; box-shadow: 0 8px 20px rgba(0,0,0,0.18); }
    .buy  { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; }
    .sell { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); color: white; }
    .hold { background: linear-gradient(135deg, #e5e7eb 0%, #cbd5e1 100%); color: #111827; }
    .box  { background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.20);
            padding: 12px; border-radius: 12px; margin: 10px 0; }
    .badge { display:inline-block; padding:3px 9px; border-radius:999px;
             font-size:11px; font-weight:800; margin-left:6px;
             vertical-align:middle; color:#0b1220; background:rgba(255,255,255,0.80); }
    .badge-crypto { background: linear-gradient(135deg,#fa709a,#fee140); color:#111827; }
    .badge-smc    { background: linear-gradient(135deg,#ffd700,#ffed4e); color:#111827; }
    .badge-mtf    { background: linear-gradient(135deg,#4facfe,#00f2fe); color:#0b1220; }
    .grid2 { display:grid; grid-template-columns:1fr 1fr; grid-gap:12px; }
    @media(max-width:900px){ .grid2{ grid-template-columns:1fr; } }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style='background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
            padding:24px;border-radius:16px;color:white;margin-bottom:16px;
            box-shadow:0 14px 28px rgba(0,0,0,0.25);text-align:center;'>
  <div style='font-size:32px;font-weight:900;'>🧠 HYBRID SMC SCREENER</div>
  <div style='font-size:14px;opacity:0.95;margin-top:6px;'>
    Order Blocks · Fair Value Gaps · BOS · Liquidity · Premium/Discount
    + RSI · MACD · MAs · ADX · MTF Confirmation
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPER MATH
# ─────────────────────────────────────────────────────────────────────────────

def _sdiv(a: pd.Series, b: pd.Series) -> pd.Series:
    """Safe division → NaN where b==0."""
    return a.where(b != 0, other=np.nan) / b.where(b != 0, other=np.nan)


def calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain  = delta.where(delta > 0, 0.0).rolling(period).mean()
    loss  = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs    = _sdiv(gain, loss)
    return 100 - (100 / (1 + rs))


def calc_ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    hl  = df["high"] - df["low"]
    hc  = (df["high"] - df["close"].shift()).abs()
    lc  = (df["low"]  - df["close"].shift()).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def calc_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Fully pandas-based ADX – avoids numpy array attribute errors."""
    up   = df["high"].diff()
    down = -df["low"].diff()

    plus_dm  = pd.Series(
        np.where((up > down) & (up > 0), up, 0.0), index=df.index
    )
    minus_dm = pd.Series(
        np.where((down > up) & (down > 0), down, 0.0), index=df.index
    )

    hl  = df["high"] - df["low"]
    hc  = (df["high"] - df["close"].shift()).abs()
    lc  = (df["low"]  - df["close"].shift()).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)

    atr14    = tr.rolling(period).mean()
    plus_di  = 100 * _sdiv(plus_dm.rolling(period).mean(),  atr14)
    minus_di = 100 * _sdiv(minus_dm.rolling(period).mean(), atr14)

    diff = (plus_di - minus_di).abs()
    summ = (plus_di + minus_di)
    dx   = 100 * _sdiv(diff, summ)
    return dx.rolling(period).mean()


def pivot_highs_lows(df: pd.DataFrame, window: int = 2, lookback: int = 100):
    d = df.tail(lookback).reset_index(drop=True)
    ph, pl = [], []
    for i in range(window, len(d) - window):
        hi = float(d.loc[i, "high"])
        lo = float(d.loc[i, "low"])
        if hi == float(d.loc[i - window : i + window, "high"].max()):
            if float((d.loc[i - window : i + window, "high"] == hi).sum()) <= 2:
                ph.append(hi)
        if lo == float(d.loc[i - window : i + window, "low"].min()):
            if float((d.loc[i - window : i + window, "low"] == lo).sum()) <= 2:
                pl.append(lo)
    return ph[-10:], pl[-10:]


def cluster_levels(levels, tol):
    if not levels:
        return []
    levels = sorted(levels)
    clusters, cur = [], [levels[0]]
    for x in levels[1:]:
        if abs(x - cur[-1]) <= tol:
            cur.append(x)
        else:
            clusters.append(float(np.mean(cur)))
            cur = [x]
    clusters.append(float(np.mean(cur)))
    return clusters


def premium_discount(df: pd.DataFrame, lookback: int = 120):
    d = df.tail(lookback)
    hi, lo = float(d["high"].max()), float(d["low"].min())
    cp = float(df.iloc[-1]["close"])
    rng = hi - lo
    if rng <= 0:
        return None
    pos = (cp - lo) / rng
    if pos < 0.382:
        zone = "DISCOUNT (DEEP)"
    elif pos < 0.5:
        zone = "DISCOUNT"
    elif pos > 0.618:
        zone = "PREMIUM (DEEP)"
    elif pos > 0.5:
        zone = "PREMIUM"
    else:
        zone = "EQUILIBRIUM"
    return {"hi": hi, "lo": lo, "pos": pos, "zone": zone}


# ─────────────────────────────────────────────────────────────────────────────
# YAHOO FETCH
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def yf_download(ticker: str, period: str, interval: str) -> pd.DataFrame:
    data = yf.download(ticker, period=period, interval=interval, progress=False)
    if data is None or data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    return data.dropna()


def to_ohlc(df_yf: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame({
        "timestamp": df_yf.index,
        "open":   df_yf["Open"].values.astype(float),
        "high":   df_yf["High"].values.astype(float),
        "low":    df_yf["Low"].values.astype(float),
        "close":  df_yf["Close"].values.astype(float),
        "volume": df_yf["Volume"].values.astype(float) if "Volume" in df_yf.columns else np.zeros(len(df_yf)),
    })
    return df.dropna().reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCREENER CLASS
# ─────────────────────────────────────────────────────────────────────────────

class HybridSMCScreener:
    TICKER_MAP = {
        "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "USDJPY=X",
        "AUD/USD": "AUDUSD=X", "USD/CAD": "USDCAD=X", "NZD/USD": "NZDUSD=X",
        "USD/CHF": "USDCHF=X", "XAU/USD": "GC=F", "XAG/USD": "SI=F",
        "BTC/USD": "BTC-USD",  "ETH/USD": "ETH-USD", "SOL/USD": "SOL-USD",
        "BNB/USD": "BNB-USD",
    }
    HTF_MAP = {"5m": "15m", "15m": "1h", "1h": "4h", "4h": "1d", "1d": None}

    def is_crypto(self, p): return any(x in p for x in ["BTC","ETH","SOL","BNB"])
    def is_metal(self, p):  return any(x in p for x in ["XAU","XAG"])

    def period_for(self, pair, interval):
        if interval == "1d":  return "2y"
        if interval == "4h":  return "180d"
        if interval == "1h":  return "120d"
        return "60d" if self.is_crypto(pair) else "30d"

    def fetch(self, pair, interval):
        t = self.TICKER_MAP.get(pair)
        if not t:
            return None
        period = self.period_for(pair, interval)
        raw = yf_download(t, period, interval)
        if raw.empty:
            if interval in ["5m","15m"]:
                raw = yf_download(t, period, "1h")
            if raw.empty:
                return None
        df = to_ohlc(raw)
        return df if len(df) >= 80 else None

    def indicators(self, df):
        df = df.copy()
        df["rsi"]        = calc_rsi(df["close"], 14)
        df["ma20"]       = df["close"].rolling(20).mean()
        df["ma50"]       = df["close"].rolling(50).mean()
        df["ema12"]      = calc_ema(df["close"], 12)
        df["ema26"]      = calc_ema(df["close"], 26)
        df["macd"]       = df["ema12"] - df["ema26"]
        df["macd_sig"]   = calc_ema(df["macd"], 9)
        df["atr"]        = calc_atr(df, 14)
        df["adx"]        = calc_adx(df, 14)   # ← fixed version
        return df

    # ── SMC ──────────────────────────────────────────────────────────────────

    def smc_bos(self, df):
        ph, pl = pivot_highs_lows(df, window=2, lookback=120)
        cp = float(df.iloc[-1]["close"])
        lh = max(ph) if ph else None
        ll = min(pl) if pl else None
        bos = {"bull": False, "bear": False, "lh": lh, "ll": ll}
        if lh and cp > lh:
            bos["bull"] = True
            bos["level"] = lh
        if ll and cp < ll:
            bos["bear"] = True
            bos["level"] = ll
        return bos

    def smc_fvg(self, df, lookback=40):
        d = df.tail(lookback).reset_index(drop=True)
        bull_fvg, bear_fvg = [], []
        for i in range(1, len(d) - 1):
            c1, c3 = d.loc[i-1], d.loc[i+1]
            # Bullish FVG: c3.low > c1.high
            if float(c3["low"]) > float(c1["high"]):
                bot, top = float(c1["high"]), float(c3["low"])
                # check not mitigated (simplified)
                bull_fvg.append({"top": top, "bot": bot, "mid": (top+bot)/2, "size": top-bot})
            # Bearish FVG: c3.high < c1.low
            if float(c3["high"]) < float(c1["low"]):
                bot, top = float(c3["high"]), float(c1["low"])
                bear_fvg.append({"top": top, "bot": bot, "mid": (top+bot)/2, "size": top-bot})

        cp = float(df.iloc[-1]["close"])
        bull_fvg = sorted(bull_fvg, key=lambda x: abs(cp - x["mid"]))[:2]
        bear_fvg = sorted(bear_fvg, key=lambda x: abs(cp - x["mid"]))[:2]
        return {"bull": bull_fvg, "bear": bear_fvg}

    def smc_liquidity(self, df):
        ph, pl = pivot_highs_lows(df, window=2, lookback=160)
        cp = float(df.iloc[-1]["close"])
        a  = float(df.iloc[-1]["atr"]) if not np.isnan(df.iloc[-1]["atr"]) else cp*0.001
        tol = max(a*0.25, cp*0.0007)

        eqh = cluster_levels(ph, tol)
        eql = cluster_levels(pl, tol)

        last_high = float(df.iloc[-1]["high"])
        last_low  = float(df.iloc[-1]["low"])
        swept_h = bool(eqh and last_high > max(eqh) + tol*0.25)
        swept_l = bool(eql and last_low  < min(eql) - tol*0.25)
        return {"eqh": eqh, "eql": eql, "swept_h": swept_h, "swept_l": swept_l}

    def smc_order_block(self, df):
        d = df.tail(160).reset_index(drop=True)
        bos = self.smc_bos(df)
        ob_bull, ob_bear = None, None

        if bos["bull"]:
            for i in range(len(d)-2, max(len(d)-22, 0), -1):
                c = d.loc[i]
                if float(c["close"]) < float(c["open"]):
                    ob_bull = {"top": float(c["high"]), "bot": float(c["low"]),
                               "mid": (float(c["high"])+float(c["low"]))/2}
                    break

        if bos["bear"]:
            for i in range(len(d)-2, max(len(d)-22, 0), -1):
                c = d.loc[i]
                if float(c["close"]) > float(c["open"]):
                    ob_bear = {"top": float(c["high"]), "bot": float(c["low"]),
                               "mid": (float(c["high"])+float(c["low"]))/2}
                    break

        return {"bull": ob_bull, "bear": ob_bear}

    # ── TRADITIONAL SCORE ───────────────────────────────────────────────────

    def trad_score(self, df):
        lt  = df.iloc[-1]
        prv = df.iloc[-2]
        sc  = 0
        rs  = []

        r = float(lt["rsi"]) if not np.isnan(lt["rsi"]) else 50.0
        if r < 30:
            sc += 2; rs.append("RSI Oversold")
        elif r > 70:
            sc -= 2; rs.append("RSI Overbought")

        m20 = float(lt["ma20"]) if not np.isnan(lt["ma20"]) else 0
        m50 = float(lt["ma50"]) if not np.isnan(lt["ma50"]) else 0
        cp  = float(lt["close"])
        if m20 and m50:
            if cp > m20 > m50:
                sc += 2; rs.append("MA Uptrend")
            elif cp < m20 < m50:
                sc -= 2; rs.append("MA Downtrend")

        macd    = float(lt["macd"])    if not np.isnan(lt["macd"])    else 0
        macd_s  = float(lt["macd_sig"]) if not np.isnan(lt["macd_sig"]) else 0
        pmacd   = float(prv["macd"])   if not np.isnan(prv["macd"])   else 0
        pmacd_s = float(prv["macd_sig"]) if not np.isnan(prv["macd_sig"]) else 0
        if macd > macd_s and pmacd <= pmacd_s:
            sc += 2; rs.append("MACD Bullish Cross")
        elif macd < macd_s and pmacd >= pmacd_s:
            sc -= 2; rs.append("MACD Bearish Cross")

        adx_val = float(lt["adx"]) if not np.isnan(lt["adx"]) else 0
        if adx_val >= 25:
            rs.append(f"ADX trending ({adx_val:.1f})")

        return {"score": sc, "reasons": rs, "rsi": r, "adx": adx_val}

    # ── MTF ─────────────────────────────────────────────────────────────────

    def mtf_check(self, pair, main_tf):
        htf = self.HTF_MAP.get(main_tf)
        if not htf:
            return {"htf": None, "align": None}

        df_h = self.fetch(pair, htf)
        if df_h is None:
            return {"htf": htf, "align": None}

        df_h = self.indicators(df_h)
        lt = df_h.iloc[-1]

        cp  = float(lt["close"])
        m20 = float(lt["ma20"]) if not np.isnan(lt["ma20"]) else 0
        m50 = float(lt["ma50"]) if not np.isnan(lt["ma50"]) else 0
        macd   = float(lt["macd"])    if not np.isnan(lt["macd"])    else 0
        macd_s = float(lt["macd_sig"]) if not np.isnan(lt["macd_sig"]) else 0

        score = 0
        if m20 and m50:
            if cp > m20 > m50: score += 1
            elif cp < m20 < m50: score -= 1
        if macd > macd_s: score += 1
        else: score -= 1

        htf_dir = "BUY" if score > 0 else "SELL" if score < 0 else "NEUTRAL"
        return {"htf": htf, "htf_dir": htf_dir, "align_score": score}

    # ── MAIN ANALYZE ────────────────────────────────────────────────────────

    def analyze(self, pair, tf, enable_mtf, enable_adx, adx_min,
                min_confluence, entry_mode,
                ob_on, fvg_on, bos_on, liq_on):

        df = self.fetch(pair, tf)
        if df is None:
            return {"pair": pair, "status": "NO_DATA"}

        df = self.indicators(df)

        lt   = df.iloc[-1]
        cp   = float(lt["close"])
        atr_val = float(lt["atr"]) if not np.isnan(lt["atr"]) else cp*0.001
        adx_val = float(lt["adx"]) if not np.isnan(lt["adx"]) else 0.0
        rsi_val = float(lt["rsi"]) if not np.isnan(lt["rsi"]) else 50.0

        # ADX filter
        if enable_adx and adx_val < adx_min:
            return {"pair": pair, "status": "FILTERED", "signal": "HOLD",
                    "reason": f"ADX {adx_val:.1f} < {adx_min}",
                    "price": cp, "adx": adx_val, "rsi": rsi_val, "tf": tf}

        # Traditional
        trad = self.trad_score(df)

        # MTF
        mtf_info = None
        if enable_mtf:
            mtf_info = self.mtf_check(pair, tf)
            main_trad_dir = "BUY" if trad["score"] > 0 else "SELL" if trad["score"] < 0 else "NEUTRAL"
            htf_dir = mtf_info.get("htf_dir")
            align_score = mtf_info.get("align_score", 0)
            if htf_dir is not None and htf_dir != "NEUTRAL":
                aligned = (htf_dir == main_trad_dir)
                if not aligned:
                    return {"pair": pair, "status": "FILTERED", "signal": "HOLD",
                            "reason": f"MTF not aligned (main {main_trad_dir} vs {mtf_info.get('htf')} {htf_dir})",
                            "price": cp, "adx": adx_val, "rsi": rsi_val, "tf": tf,
                            "mtf": mtf_info}

        # ── SMC ─────────────────────────────────────────────────────────────
        smc_sc  = 0
        smc_rs  = []
        smc_det = {}

        # Premium/Discount Zone
        pdz = premium_discount(df, 140)
        if pdz:
            smc_det["pdz"] = pdz
            if "DISCOUNT" in pdz["zone"]:
                smc_sc += 2; smc_rs.append(f"PDZ: {pdz['zone']} → BUY zone")
            elif "PREMIUM" in pdz["zone"]:
                smc_sc -= 2; smc_rs.append(f"PDZ: {pdz['zone']} → SELL zone")

        # BOS
        if bos_on:
            bos = self.smc_bos(df)
            smc_det["bos"] = bos
            if bos["bull"]:
                smc_sc += 3; smc_rs.append(f"BOS Bullish (broke {bos.get('level', ''):.5g})")
            if bos["bear"]:
                smc_sc -= 3; smc_rs.append(f"BOS Bearish (broke {bos.get('level', ''):.5g})")

        # Liquidity sweep
        if liq_on:
            liq = self.smc_liquidity(df)
            smc_det["liq"] = liq
            if liq["swept_l"]:
                smc_sc += 2; smc_rs.append("Swept Lows (bullish)")
            if liq["swept_h"]:
                smc_sc -= 2; smc_rs.append("Swept Highs (bearish)")

        # FVG
        if fvg_on:
            fvg = self.smc_fvg(df)
            smc_det["fvg"] = fvg
            if fvg["bull"]:
                nr = fvg["bull"][0]
                if abs(cp - nr["mid"]) <= max(atr_val*0.6, cp*0.001):
                    smc_sc += 2; smc_rs.append("Near Bullish FVG")
            if fvg["bear"]:
                nr = fvg["bear"][0]
                if abs(cp - nr["mid"]) <= max(atr_val*0.6, cp*0.001):
                    smc_sc -= 2; smc_rs.append("Near Bearish FVG")

        # Order Block
        if ob_on:
            ob = self.smc_order_block(df)
            smc_det["ob"] = ob
            if ob["bull"] and ob["bull"]["bot"] <= cp <= ob["bull"]["top"]:
                smc_sc += 3; smc_rs.append("Inside Bullish OB")
            if ob["bear"] and ob["bear"]["bot"] <= cp <= ob["bear"]["top"]:
                smc_sc -= 3; smc_rs.append("Inside Bearish OB")

        total = trad["score"] + smc_sc
        confluence = abs(total)

        # Below min confluence → HOLD (visible but no trade)
        if confluence < min_confluence:
            return {"pair": pair, "status": "HOLD", "signal": "HOLD",
                    "price": cp, "adx": adx_val, "rsi": rsi_val, "tf": tf,
                    "trad": trad, "smc_sc": smc_sc, "smc_rs": smc_rs,
                    "smc_det": smc_det, "total": total, "confluence": confluence,
                    "mtf": mtf_info,
                    "note": f"Confluence {confluence} < {min_confluence}"}

        direction = "BUY" if total > 0 else "SELL"

        # Entry using OB mid if inside OB
        entry = cp
        entry_src = "Market price"
        if direction == "BUY" and smc_det.get("ob", {}).get("bull"):
            b = smc_det["ob"]["bull"]
            if b["bot"] <= cp <= b["top"]:
                entry = b["mid"]; entry_src = "Bullish OB mid"
        if direction == "SELL" and smc_det.get("ob", {}).get("bear"):
            b = smc_det["ob"]["bear"]
            if b["bot"] <= cp <= b["top"]:
                entry = b["mid"]; entry_src = "Bearish OB mid"

        zone_m = {"Conservative": 0.30, "Moderate": 0.50, "Aggressive": 0.80}[entry_mode]

        if self.is_crypto(pair):
            sl_m, tp1_m, tp2_m = 1.0, 2.0, 3.2
        elif self.is_metal(pair):
            sl_m, tp1_m, tp2_m = 1.5, 2.5, 3.8
        else:
            sl_m, tp1_m, tp2_m = 2.0, 3.0, 5.0

        if direction == "BUY":
            sl  = entry - sl_m  * atr_val
            tp1 = entry + tp1_m * atr_val
            tp2 = entry + tp2_m * atr_val
            cls, emoji = "buy", "🟢"
        else:
            sl  = entry + sl_m  * atr_val
            tp1 = entry - tp1_m * atr_val
            tp2 = entry - tp2_m * atr_val
            cls, emoji = "sell", "🔴"

        label = ("STRONG " if confluence >= min_confluence + 4 else "") + direction

        return {
            "pair": pair, "status": "TRADE", "signal": label,
            "direction": direction, "emoji": emoji, "css": cls,
            "price": cp, "tf": tf,
            "entry": entry, "entry_src": entry_src,
            "entry_low":  entry - atr_val * zone_m,
            "entry_high": entry + atr_val * zone_m,
            "sl": sl, "tp1": tp1, "tp2": tp2,
            "rr": round(tp1_m / sl_m, 2),
            "atr": atr_val, "adx": adx_val, "rsi": rsi_val,
            "trad": trad, "smc_sc": smc_sc, "smc_rs": smc_rs,
            "smc_det": smc_det, "total": total, "confluence": confluence,
            "mtf": mtf_info,
        }


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Settings")

    forex_pairs  = st.multiselect("💱 Forex",
        ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","NZD/USD","USD/CHF"],
        default=["EUR/USD","GBP/USD","USD/JPY"])
    metal_pairs  = st.multiselect("🥇 Metals",  ["XAU/USD","XAG/USD"], default=["XAU/USD"])
    crypto_pairs = st.multiselect("₿ Crypto",
        ["BTC/USD","ETH/USD","SOL/USD","BNB/USD"],
        default=["BTC/USD","ETH/USD"])

    st.markdown("---")
    tf = st.selectbox("⏰ Timeframe", ["5m","15m","1h","4h","1d"], index=2)

    st.markdown("---")
    st.subheader("✅ Filters")
    enable_mtf = st.checkbox("MTF confirmation", value=True)
    enable_adx = st.checkbox("ADX filter", value=True)
    adx_min    = st.slider("ADX minimum", 10, 40, 20) if enable_adx else 0

    st.markdown("---")
    st.subheader("🧠 SMC Components")
    ob_on  = st.checkbox("Order Block (OB)",         value=True)
    fvg_on = st.checkbox("Fair Value Gap (FVG)",     value=True)
    bos_on = st.checkbox("Break of Structure (BOS)", value=True)
    liq_on = st.checkbox("Liquidity Sweep (EQH/EQL)",value=True)

    st.markdown("---")
    st.subheader("🎯 Signal Quality")
    min_conf   = st.slider("Min confluence", 4, 16, 10,
        help="Naikkan untuk sinyal lebih sedikit tapi lebih kuat")
    entry_mode = st.radio("Entry zone", ["Conservative","Moderate","Aggressive"], index=1)

    st.caption("Tips: Kalau sinyal kosong → turunkan Min confluence, atau matikan MTF/ADX, atau pakai TF lebih besar.")

# ─────────────────────────────────────────────────────────────────────────────
# RENDER CARD
# ─────────────────────────────────────────────────────────────────────────────

def decimals(pair):
    if "JPY" in pair: return 3
    if any(x in pair for x in ["XAU","XAG","BTC","ETH","SOL","BNB"]): return 2
    return 5


def render_card(r):
    dec   = decimals(r["pair"])
    is_cr = any(x in r["pair"] for x in ["BTC","ETH","SOL","BNB"])
    has_smc = bool(r.get("smc_rs"))
    has_mtf = r.get("mtf") and r["mtf"].get("htf_dir")

    badges = ""
    if is_cr:  badges += "<span class='badge badge-crypto'>CRYPTO</span>"
    if has_smc: badges += "<span class='badge badge-smc'>SMC</span>"
    if has_mtf: badges += f"<span class='badge badge-mtf'>MTF {r['mtf'].get('htf','')}</span>"

    entry_html = ""
    if r.get("entry") is not None and r.get("sl") is not None:
        entry_html = f"""
        <div class="box">
          <b>🎯 Entry Zone</b> ({entry_mode})<br/>
          Best entry : <b>{r['entry']:.{dec}f}</b>
          <span class='badge'>{r.get('entry_src','Market')}</span><br/>
          Zone       : {r['entry_low']:.{dec}f} → {r['entry_high']:.{dec}f}<br/>
          SL         : <b>{r['sl']:.{dec}f}</b> &nbsp;|&nbsp;
          TP1        : <b>{r['tp1']:.{dec}f}</b> &nbsp;|&nbsp;
          TP2        : <b>{r['tp2']:.{dec}f}</b><br/>
          R:R (TP1)  : <b>1:{r.get('rr','-')}</b>
        </div>"""

    pdz_txt = ""
    pdz = r.get("smc_det", {}).get("pdz")
    if pdz:
        pdz_txt = f"<br/><i>PDZ: {pdz.get('zone')} ({pdz.get('pos',0)*100:.0f}% of range)</i>"

    trad_txt = ", ".join(r.get("trad", {}).get("reasons", [])[:4]) or "—"
    smc_txt  = ", ".join(r.get("smc_rs", [])[:5]) or "No strong SMC confluence"
    mtf_txt  = ""
    if has_mtf:
        mtf_txt = f"HTF ({r['mtf'].get('htf')}): {r['mtf'].get('htf_dir')}"

    emoji   = r.get("emoji","🟡")
    sig     = r.get("signal","HOLD")
    css     = r.get("css","hold")
    conf    = r.get("confluence", "—")
    total   = r.get("total", "—")
    adx_v   = r.get("adx", 0)
    rsi_v   = r.get("rsi", 50)

    st.markdown(f"""
    <div class="card {css}">
      <div style="font-size:20px;font-weight:900;">{emoji} {r['pair']} — {sig} {badges}</div>
      <div style="margin-top:4px;opacity:0.93;">
        TF: {r.get('tf','—')} | Confluence: <b>{conf}</b> | Score: <b>{total:+}</b>
        | ADX: {adx_v:.1f} | RSI: {rsi_v:.1f}
      </div>
      {entry_html}
      <div class="grid2">
        <div class="box">
          <b>🧠 SMC</b> (score: {r.get('smc_sc',0):+}){pdz_txt}<br/>
          {smc_txt}
        </div>
        <div class="box">
          <b>📊 Traditional</b> (score: {r.get('trad',{}).get('score',0):+})<br/>
          {trad_txt}<br/>
          <span style="opacity:0.8;">{mtf_txt}</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN SCAN
# ─────────────────────────────────────────────────────────────────────────────

pairs = forex_pairs + metal_pairs + crypto_pairs
screener = HybridSMCScreener()

if st.button("🚀 SCAN NOW — Hybrid SMC"):
    if not pairs:
        st.warning("Pilih minimal 1 pair di sidebar.")
        st.stop()

    st.write(f"**Scan:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
             f"TF: **{tf}** | MTF: **{enable_mtf}** | "
             f"ADX ≥ **{adx_min}** | Min confluence: **{min_conf}**")

    prog   = st.progress(0)
    status = st.empty()
    results = []

    for i, pair in enumerate(pairs, start=1):
        status.text(f"Analyzing {pair} ({i}/{len(pairs)}) ...")
        res = screener.analyze(
            pair=pair, tf=tf,
            enable_mtf=enable_mtf, enable_adx=enable_adx, adx_min=float(adx_min),
            min_confluence=int(min_conf), entry_mode=entry_mode,
            ob_on=ob_on, fvg_on=fvg_on, bos_on=bos_on, liq_on=liq_on,
        )
        results.append(res)
        prog.progress(i / len(pairs))
        time.sleep(0.15)

    status.empty()
    prog.empty()

    trades   = [r for r in results if r.get("status") == "TRADE"]
    holds    = [r for r in results if r.get("status") == "HOLD"]
    filtered = [r for r in results if r.get("status") == "FILTERED"]
    nodata   = [r for r in results if r.get("status") == "NO_DATA"]
    buys     = [r for r in trades if r.get("direction") == "BUY"]
    sells    = [r for r in trades if r.get("direction") == "SELL"]

    # ── Dashboard metrics ──
    st.markdown("---")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total",    len(results))
    c2.metric("🟢 Buy",   len(buys))
    c3.metric("🔴 Sell",  len(sells))
    c4.metric("🟡 Hold",  len(holds))
    c5.metric("⛔ Filtered/ND", len(filtered)+len(nodata))

    # ── Tradeable ──
    st.markdown("---")
    st.subheader("🎯 Tradeable Signals")
    if trades:
        for r in sorted(trades, key=lambda x: x.get("confluence",0), reverse=True):
            render_card(r)
    else:
        st.warning(
            "⚠️ Tidak ada sinyal BUY/SELL yang lolos saat ini.\n\n"
            "**Coba:** turunkan Min confluence slider | matikan MTF/ADX sementara | "
            "pilih TF lebih besar (1h/4h/1d) | tambahkan lebih banyak pair."
        )

    # ── Hold ──
    st.markdown("---")
    with st.expander(f"🟡 HOLD ({len(holds)}) — setup lemah / confluence belum cukup"):
        for r in sorted(holds, key=lambda x: x.get("confluence",0), reverse=True):
            render_card(r)

    # ── Filtered ──
    with st.expander(f"⛔ FILTERED ({len(filtered)}) — diblokir ADX/MTF filter"):
        for r in filtered:
            st.write(f"**{r['pair']}** | {r.get('reason', r.get('filter_reason','Filtered'))} "
                     f"| ADX: {r.get('adx',0):.1f} | RSI: {r.get('rsi',50):.1f} | Price: {r.get('price'):.5g}")

    # ── No data ──
    with st.expander(f"⚠️ NO DATA ({len(nodata)}) — Yahoo tidak ada data untuk TF/pair ini"):
        for r in nodata:
            st.write(f"**{r['pair']}** — coba TF lebih besar (1h/4h/1d).")

    st.markdown("---")
    st.info("""
**Catatan SMC (Smart Money Concepts):**
- **OB (Order Block):** Last opposing candle sebelum impulse move — area entry institusional.
- **FVG (Fair Value Gap):** Imbalance 3-candle — harga cenderung kembali mengisi gap.
- **BOS (Break of Structure):** Konfirmasi arah trend terbaru.
- **Liquidity sweep:** Smart money sering "sapu" equal highs/lows sebelum reversal.
- **PDZ (Premium/Discount):** Beli di discount (<50%), jual di premium (>50%) sesuai range.

Tool ini bersifat *heuristic* — gunakan sebagai *watchlist screener*, lalu konfirmasi secara manual di chart sebelum entry.
""")

# footer
st.markdown("---")
st.caption("Hybrid SMC Screener v4.0 | Data: Yahoo Finance | Educational purposes only.")
