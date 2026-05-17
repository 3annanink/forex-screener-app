import time
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# =========================
# Streamlit Page Config
# =========================
st.set_page_config(
    page_title="Hybrid SMC Screener (Forex/Metals/Crypto)",
    page_icon="🧠",
    layout="wide",
)

# =========================
# UI Styles
# =========================
st.markdown(
    """
<style>
    .main { padding: 1rem; }
    .stButton>button {
        width: 100%;
        height: 56px;
        font-size: 18px;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
    }
    .stButton>button:hover { filter: brightness(1.05); }
    .card {
        padding: 18px;
        border-radius: 14px;
        margin: 14px 0;
        box-shadow: 0 10px 22px rgba(0,0,0,0.18);
    }
    .buy { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; }
    .sell { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); color: white; }
    .hold { background: linear-gradient(135deg, #e5e7eb 0%, #cbd5e1 100%); color: #111827; box-shadow: 0 6px 14px rgba(0,0,0,0.08); }
    .muted { opacity: 0.95; }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
        margin-left: 8px;
        vertical-align: middle;
        color: #0b1220;
        background: rgba(255,255,255,0.75);
    }
    .badge-s { background: rgba(255, 255, 255, 0.75); color: #0b1220; }
    .badge-crypto { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: #111827; }
    .badge-mtf { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: #0b1220; }
    .badge-smc { background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%); color: #111827; }
    .box {
        background: rgba(255,255,255,0.18);
        border: 1px solid rgba(255,255,255,0.20);
        padding: 12px;
        border-radius: 12px;
        margin: 10px 0;
    }
    .grid2 {
        display: grid;
        grid-template-columns: 1fr 1fr;
        grid-gap: 12px;
    }
    @media (max-width: 900px) {
        .grid2 { grid-template-columns: 1fr; }
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 24px; border-radius: 16px; color: white; margin-bottom: 16px;
            box-shadow: 0 14px 28px rgba(0,0,0,0.25); text-align:center;'>
  <div style='font-size: 34px; font-weight: 900;'>🧠 HYBRID SMC SCREENER</div>
  <div style='font-size: 15px; opacity: 0.95; margin-top:6px;'>
    Smart Money Concepts (OB/FVG/BOS/Liquidity/Premium-Discount) + Traditional (RSI/MAs/MACD/ADX) + MTF Confirmation
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# =========================
# Helpers (math/indicators)
# =========================
def _safe_div(a, b):
    return np.where(b == 0, np.nan, a / b)


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs = _safe_div(gain, loss)
    return 100 - (100 / (1 + rs))


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    # Simplified ADX (Wilder style approximation)
    up_move = df["high"].diff()
    down_move = -df["low"].diff()

    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

    tr = pd.concat(
        [
            (df["high"] - df["low"]),
            (df["high"] - df["close"].shift()).abs(),
            (df["low"] - df["close"].shift()).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr14 = tr.rolling(period).mean()
    plus_di = 100 * _safe_div(plus_dm.rolling(period).mean(), atr14)
    minus_di = 100 * _safe_div(minus_dm.rolling(period).mean(), atr14)
    dx = 100 * _safe_div((plus_di - minus_di).abs(), (plus_di + minus_di))
    return dx.rolling(period).mean()


def pivots(df: pd.DataFrame, window: int = 2, lookback: int = 80):
    """Return pivot highs/lows as lists of floats (recent)."""
    d = df.tail(lookback).reset_index(drop=True)
    ph = []
    pl = []
    for i in range(window, len(d) - window):
        h = d.loc[i, "high"]
        l = d.loc[i, "low"]
        if h == d.loc[i - window : i + window, "high"].max():
            # ensure strict-ish: not flat
            if (d.loc[i - window : i + window, "high"] == h).sum() <= 2:
                ph.append(float(h))
        if l == d.loc[i - window : i + window, "low"].min():
            if (d.loc[i - window : i + window, "low"] == l).sum() <= 2:
                pl.append(float(l))
    return ph[-10:], pl[-10:]


def cluster_levels(levels, tol):
    """Cluster price levels within tolerance."""
    if not levels:
        return []
    levels = sorted(levels)
    clusters = []
    cur = [levels[0]]
    for x in levels[1:]:
        if abs(x - cur[-1]) <= tol:
            cur.append(x)
        else:
            clusters.append(float(np.mean(cur)))
            cur = [x]
    clusters.append(float(np.mean(cur)))
    return clusters


def premium_discount_zone(df: pd.DataFrame, lookback: int = 120):
    d = df.tail(lookback)
    hi = float(d["high"].max())
    lo = float(d["low"].min())
    cp = float(df.iloc[-1]["close"])
    rng = hi - lo
    if rng <= 0:
        return None
    pos = (cp - lo) / rng
    # Common SMC framing: discount < 0.5, premium > 0.5
    zone = "DISCOUNT" if pos < 0.5 else "PREMIUM"
    # more strict: extreme zones
    if pos < 0.382:
        zone = "DISCOUNT (DEEP)"
    elif pos > 0.618:
        zone = "PREMIUM (DEEP)"
    return {"high": hi, "low": lo, "pos": pos, "zone": zone}


# =========================
# Yahoo Download (cached)
# =========================
@st.cache_data(ttl=300, show_spinner=False)
def yf_download(ticker: str, period: str, interval: str) -> pd.DataFrame:
    data = yf.download(ticker, period=period, interval=interval, progress=False)
    if data is None or len(data) == 0:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    data = data.dropna()
    return data


def to_ohlc(df_yf: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "timestamp": df_yf.index,
            "open": df_yf["Open"].values,
            "high": df_yf["High"].values,
            "low": df_yf["Low"].values,
            "close": df_yf["Close"].values,
            "volume": df_yf["Volume"].values if "Volume" in df_yf.columns else np.zeros(len(df_yf)),
        }
    )
    df = df.dropna().reset_index(drop=True)
    return df


# =========================
# Hybrid SMC Screener
# =========================
class HybridSMCScreener:
    def __init__(self):
        self.ticker_map = {
            # Forex
            "EUR/USD": "EURUSD=X",
            "GBP/USD": "GBPUSD=X",
            "USD/JPY": "USDJPY=X",
            "AUD/USD": "AUDUSD=X",
            "USD/CAD": "USDCAD=X",
            "NZD/USD": "NZDUSD=X",
            "USD/CHF": "USDCHF=X",
            # Metals (futures proxy)
            "XAU/USD": "GC=F",
            "XAG/USD": "SI=F",
            # Crypto
            "BTC/USD": "BTC-USD",
            "ETH/USD": "ETH-USD",
            "SOL/USD": "SOL-USD",
            "BNB/USD": "BNB-USD",
        }

    def is_crypto(self, pair: str) -> bool:
        return any(x in pair for x in ["BTC", "ETH", "SOL", "BNB"])

    def is_metal(self, pair: str) -> bool:
        return ("XAU" in pair) or ("XAG" in pair)

    def period_for(self, pair: str, interval: str) -> str:
        # Ensure enough candles for indicators + SMC detection
        if interval in ["1d"]:
            return "1y" if self.is_crypto(pair) else "1y"
        if interval in ["4h", "1h"]:
            return "180d" if self.is_crypto(pair) else "120d"
        # 15m/5m: Yahoo sometimes limits history; keep moderate
        return "60d" if self.is_crypto(pair) else "30d"

    def fetch_ohlc(self, pair: str, interval: str) -> pd.DataFrame | None:
        t = self.ticker_map.get(pair)
        if not t:
            return None
        period = self.period_for(pair, interval)
        df_yf = yf_download(t, period, interval)
        if df_yf.empty:
            # Fallback: some symbols fail on small intervals
            if interval in ["5m", "15m"]:
                df_yf = yf_download(t, period, "1h")
                if df_yf.empty:
                    return None
            else:
                return None
        df = to_ohlc(df_yf)
        return df if len(df) >= 80 else None

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["rsi"] = rsi(df["close"], 14)
        df["ma20"] = df["close"].rolling(20).mean()
        df["ma50"] = df["close"].rolling(50).mean()
        df["ema12"] = ema(df["close"], 12)
        df["ema26"] = ema(df["close"], 26)
        df["macd"] = df["ema12"] - df["ema26"]
        df["macd_signal"] = ema(df["macd"], 9)
        df["atr"] = atr(df, 14)
        df["adx"] = adx(df, 14)
        return df

    # ---------- SMC blocks ----------
    def smc_bos(self, df: pd.DataFrame):
        ph, pl = pivots(df, window=2, lookback=120)
        cp = float(df.iloc[-1]["close"])
        last_high = max(ph) if ph else None
        last_low = min(pl) if pl else None

        bos = {"bullish": False, "bearish": False, "last_high": last_high, "last_low": last_low}
        if last_high is not None and cp > last_high:
            bos["bullish"] = True
            bos["level"] = last_high
        if last_low is not None and cp < last_low:
            bos["bearish"] = True
            bos["level"] = last_low
        return bos

    def smc_fvg(self, df: pd.DataFrame, lookback: int = 35):
        # 3-candle FVG; keep nearest unmitigated
        d = df.tail(lookback).reset_index(drop=True)
        bullish = []
        bearish = []
        for i in range(1, len(d) - 1):
            c1 = d.loc[i - 1]
            c2 = d.loc[i]
            c3 = d.loc[i + 1]

            # Bullish gap: c3.low > c1.high
            if float(c3["low"]) > float(c1["high"]):
                top = float(c3["low"])
                bot = float(c1["high"])
                mid = (top + bot) / 2.0
                # unmitigated if later lows never go <= bot
                if float(d.loc[i + 1 :, "low"].min()) > bot:
                    bullish.append({"top": top, "bottom": bot, "mid": mid, "ts": c2["timestamp"], "size": top - bot})

            # Bearish gap: c3.high < c1.low
            if float(c3["high"]) < float(c1["low"]):
                top = float(c1["low"])
                bot = float(c3["high"])
                mid = (top + bot) / 2.0
                if float(d.loc[i + 1 :, "high"].max()) < top:
                    bearish.append({"top": top, "bottom": bot, "mid": mid, "ts": c2["timestamp"], "size": top - bot})

        cp = float(df.iloc[-1]["close"])
        # nearest to price
        bullish = sorted(bullish, key=lambda x: abs(cp - x["mid"]))[:2]
        bearish = sorted(bearish, key=lambda x: abs(cp - x["mid"]))[:2]
        return {"bullish": bullish, "bearish": bearish}

    def smc_liquidity(self, df: pd.DataFrame):
        # equal highs/lows clustering on pivots
        ph, pl = pivots(df, window=2, lookback=160)
        cp = float(df.iloc[-1]["close"])
        a = float(df.iloc[-1]["atr"]) if not np.isnan(df.iloc[-1]["atr"]) else cp * 0.001
        tol = max(a * 0.25, cp * 0.0007)  # adaptive tolerance

        eqh = cluster_levels(ph, tol)
        eql = cluster_levels(pl, tol)

        last_high = float(df.iloc[-1]["high"])
        last_low = float(df.iloc[-1]["low"])

        swept_highs = False
        swept_lows = False
        if eqh:
            if last_high > max(eqh) + tol * 0.25:
                swept_highs = True
        if eql:
            if last_low < min(eql) - tol * 0.25:
                swept_lows = True

        return {"eq_highs": sorted(eqh, reverse=True)[:3], "eq_lows": sorted(eql)[:3], "swept_highs": swept_highs, "swept_lows": swept_lows}

    def smc_order_block(self, df: pd.DataFrame):
        # Heuristic OB:
        # - if bullish BOS: last bearish candle before BOS becomes bullish OB
        # - if bearish BOS: last bullish candle before BOS becomes bearish OB
        d = df.tail(160).reset_index(drop=True)
        bos = self.smc_bos(df)
        if not (bos.get("bullish") or bos.get("bearish")):
            return {"bullish_ob": None, "bearish_ob": None}

        # find index where break happened (approx last candle)
        idx_break = len(d) - 1
        bullish_ob = None
        bearish_ob = None

        if bos.get("bullish"):
            # search back for last bearish candle
            for i in range(idx_break - 1, max(idx_break - 20, 0), -1):
                c = d.loc[i]
                if float(c["close"]) < float(c["open"]):
                    bullish_ob = {
                        "top": float(c["high"]),
                        "bottom": float(c["low"]),
                        "mid": (float(c["high"]) + float(c["low"])) / 2.0,
                        "ts": c["timestamp"],
                    }
                    break

        if bos.get("bearish"):
            for i in range(idx_break - 1, max(idx_break - 20, 0), -1):
                c = d.loc[i]
                if float(c["close"]) > float(c["open"]):
                    bearish_ob = {
                        "top": float(c["high"]),
                        "bottom": float(c["low"]),
                        "mid": (float(c["high"]) + float(c["low"])) / 2.0,
                        "ts": c["timestamp"],
                    }
                    break

        return {"bullish_ob": bullish_ob, "bearish_ob": bearish_ob}

    # ---------- Traditional scoring ----------
    def traditional_score(self, df: pd.DataFrame):
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        score = 0
        reasons = []

        r = float(latest["rsi"]) if not np.isnan(latest["rsi"]) else 50.0
        if r < 30:
            score += 2
            reasons.append("RSI oversold (<30)")
        elif r > 70:
            score -= 2
            reasons.append("RSI overbought (>70)")

        # MA bias
        if not np.isnan(latest["ma20"]) and not np.isnan(latest["ma50"]):
            if float(latest["close"]) > float(latest["ma20"]) > float(latest["ma50"]):
                score += 2
                reasons.append("MA uptrend (Close>MA20>MA50)")
            elif float(latest["close"]) < float(latest["ma20"]) < float(latest["ma50"]):
                score -= 2
                reasons.append("MA downtrend (Close<MA20<MA50)")

        # MACD cross
        if not np.isnan(latest["macd"]) and not np.isnan(latest["macd_signal"]):
            if float(latest["macd"]) > float(latest["macd_signal"]) and float(prev["macd"]) <= float(prev["macd_signal"]):
                score += 2
                reasons.append("MACD bullish cross")
            elif float(latest["macd"]) < float(latest["macd_signal"]) and float(prev["macd"]) >= float(prev["macd_signal"]):
                score -= 2
                reasons.append("MACD bearish cross")

        # ADX context only (filter applied outside)
        a = float(latest["adx"]) if not np.isnan(latest["adx"]) else 0.0
        if a >= 25:
            reasons.append(f"ADX trending ({a:.1f})")

        return {"score": score, "reasons": reasons, "rsi": r, "adx": a}

    # ---------- MTF ----------
    def mtf(self, pair: str, main_tf: str):
        # Keep it light: use 1 higher TF only
        hierarchy = {"5m": "15m", "15m": "1h", "1h": "4h", "4h": "1d", "1d": None}
        htf = hierarchy.get(main_tf)
        if not htf:
            return {"enabled": True, "htf": None, "align": None, "main_dir": None, "htf_dir": None}

        df_main = self.fetch_ohlc(pair, main_tf)
        df_htf = self.fetch_ohlc(pair, htf)
        if df_main is None or df_htf is None:
            return {"enabled": True, "htf": htf, "align": None, "main_dir": None, "htf_dir": None}

        df_main = self.add_indicators(df_main)
        df_htf = self.add_indicators(df_htf)

        # define direction by MA bias + MACD bias
        def dir_from(df):
            lt = df.iloc[-1]
            s = 0
            if not np.isnan(lt["ma20"]) and not np.isnan(lt["ma50"]):
                if float(lt["close"]) > float(lt["ma20"]) > float(lt["ma50"]):
                    s += 1
                elif float(lt["close"]) < float(lt["ma20"]) < float(lt["ma50"]):
                    s -= 1
            if not np.isnan(lt["macd"]) and not np.isnan(lt["macd_signal"]):
                s += 1 if float(lt["macd"]) > float(lt["macd_signal"]) else -1
            return "BUY" if s > 0 else "SELL" if s < 0 else "NEUTRAL"

        md = dir_from(df_main)
        hd = dir_from(df_htf)
        align = (md == hd) and (md != "NEUTRAL")
        return {"enabled": True, "htf": htf, "align": align, "main_dir": md, "htf_dir": hd}

    # ---------- HYBRID ANALYZE ----------
    def analyze_pair(
        self,
        pair: str,
        tf: str,
        enable_mtf: bool,
        enable_adx_filter: bool,
        adx_min: float,
        min_confluence: int,
        entry_mode: str,
        smc_enable_ob: bool,
        smc_enable_fvg: bool,
        smc_enable_bos: bool,
        smc_enable_liq: bool,
    ):
        df = self.fetch_ohlc(pair, tf)
        if df is None:
            return {"pair": pair, "status": "NO_DATA", "signal": "NO DATA"}

        df = self.add_indicators(df)
        latest = df.iloc[-1]
        cp = float(latest["close"])
        a = float(latest["atr"]) if not np.isnan(latest["atr"]) else cp * 0.001

        # ADX filter
        adx_val = float(latest["adx"]) if not np.isnan(latest["adx"]) else 0.0
        if enable_adx_filter and adx_val < adx_min:
            return {
                "pair": pair,
                "status": "FILTERED",
                "signal": "HOLD",
                "filter_reason": f"ADX too low ({adx_val:.1f} < {adx_min})",
                "price": cp,
                "adx": adx_val,
                "tf": tf,
            }

        # MTF confirm
        mtf_info = None
        if enable_mtf:
            mtf_info = self.mtf(pair, tf)
            # If we cannot compute align, don't block; if align is False, filter out
            if mtf_info and (mtf_info.get("align") is False):
                return {
                    "pair": pair,
                    "status": "FILTERED",
                    "signal": "HOLD",
                    "filter_reason": f"MTF not aligned (main:{mtf_info.get('main_dir')} vs {mtf_info.get('htf')}:{mtf_info.get('htf_dir')})",
                    "price": cp,
                    "adx": adx_val,
                    "tf": tf,
                    "mtf": mtf_info,
                }

        # Traditional
        trad = self.traditional_score(df)

        # SMC
        smc_score = 0
        smc_reasons = []
        smc_detail = {}

        # Premium/Discount
        pdz = premium_discount_zone(df, lookback=140)
        if pdz:
            smc_detail["pdz"] = pdz
            if "DISCOUNT" in pdz["zone"]:
                smc_score += 2
                smc_reasons.append(f"PDZ: {pdz['zone']} (buy area)")
            elif "PREMIUM" in pdz["zone"]:
                smc_score -= 2
                smc_reasons.append(f"PDZ: {pdz['zone']} (sell area)")

        # BOS
        bos = self.smc_bos(df) if smc_enable_bos else None
        if bos:
            smc_detail["bos"] = bos
            if bos.get("bullish"):
                smc_score += 3
                smc_reasons.append(f"BOS bullish (break {bos.get('level'):.5f if isinstance(bos.get('level'), float) else bos.get('level')})")
            if bos.get("bearish"):
                smc_score -= 3
                smc_reasons.append(f"BOS bearish (break {bos.get('level'):.5f if isinstance(bos.get('level'), float) else bos.get('level')})")

        # Liquidity sweep
        liq = self.smc_liquidity(df) if smc_enable_liq else None
        if liq:
            smc_detail["liq"] = liq
            if liq.get("swept_lows"):
                smc_score += 2
                smc_reasons.append("Liquidity: swept lows (bullish)")
            if liq.get("swept_highs"):
                smc_score -= 2
                smc_reasons.append("Liquidity: swept highs (bearish)")

        # FVG
        fvg = self.smc_fvg(df) if smc_enable_fvg else None
        if fvg:
            smc_detail["fvg"] = fvg
            # near FVG mid
            if fvg["bullish"]:
                nearest = fvg["bullish"][0]
                if abs(cp - nearest["mid"]) <= max(a * 0.5, cp * 0.001):
                    smc_score += 2
                    smc_reasons.append("FVG: near bullish gap (imbalance)")
            if fvg["bearish"]:
                nearest = fvg["bearish"][0]
                if abs(cp - nearest["mid"]) <= max(a * 0.5, cp * 0.001):
                    smc_score -= 2
                    smc_reasons.append("FVG: near bearish gap (imbalance)")

        # Order Block (only meaningful if BOS exists)
        ob = self.smc_order_block(df) if smc_enable_ob else None
        if ob:
            smc_detail["ob"] = ob
            if ob.get("bullish_ob"):
                bull = ob["bullish_ob"]
                if bull["bottom"] <= cp <= bull["top"]:
                    smc_score += 3
                    smc_reasons.append("OB: price inside bullish order block")
            if ob.get("bearish_ob"):
                bear = ob["bearish_ob"]
                if bear["bottom"] <= cp <= bear["top"]:
                    smc_score -= 3
                    smc_reasons.append("OB: price inside bearish order block")

        total_score = trad["score"] + smc_score
        confluence = abs(total_score)

        # Confluence threshold: if not enough, show HOLD (not filtered), so user still sees context
        if confluence < min_confluence:
            return {
                "pair": pair,
                "status": "HOLD",
                "signal": "HOLD",
                "price": cp,
                "tf": tf,
                "adx": trad["adx"],
                "rsi": trad["rsi"],
                "trad": trad,
                "smc_score": smc_score,
                "smc_reasons": smc_reasons,
                "smc_detail": smc_detail,
                "total_score": total_score,
                "confluence": confluence,
                "mtf": mtf_info,
                "note": f"Confluence below threshold ({confluence} < {min_confluence})",
            }

        # Decide direction
        if total_score >= min_confluence:
            direction = "BUY"
        elif total_score <= -min_confluence:
            direction = "SELL"
        else:
            direction = "HOLD"

        # Entry logic: try OB mid if available & matches direction
        entry = cp
        entry_source = "Market"
        if direction == "BUY" and ob and ob.get("bullish_ob"):
            bull = ob["bullish_ob"]
            entry = bull["mid"]
            entry_source = "Bullish OB (mid)"
        if direction == "SELL" and ob and ob.get("bearish_ob"):
            bear = ob["bearish_ob"]
            entry = bear["mid"]
            entry_source = "Bearish OB (mid)"

        zone_mult = {"Conservative": 0.30, "Moderate": 0.50, "Aggressive": 0.80}[entry_mode]

        # SL/TP multipliers (tweak)
        if self.is_crypto(pair):
            sl_mult, tp1_mult, tp2_mult = 1.0, 2.0, 3.2
        elif self.is_metal(pair):
            sl_mult, tp1_mult, tp2_mult = 1.5, 2.5, 3.8
        else:
            sl_mult, tp1_mult, tp2_mult = 2.0, 3.0, 5.0

        entry_low = entry - a * zone_mult
        entry_high = entry + a * zone_mult

        if direction == "BUY":
            sl = entry - a * sl_mult
            tp1 = entry + a * tp1_mult
            tp2 = entry + a * tp2_mult
            cls = "buy"
            emoji = "🟢"
        elif direction == "SELL":
            sl = entry + a * sl_mult
            tp1 = entry - a * tp1_mult
            tp2 = entry - a * tp2_mult
            cls = "sell"
            emoji = "🔴"
        else:
            sl = tp1 = tp2 = None
            cls = "hold"
            emoji = "🟡"

        # Strong label
        strength = "STRONG" if confluence >= (min_confluence + 4) else "NORMAL"

        return {
            "pair": pair,
            "status": "TRADE" if direction in ["BUY", "SELL"] else "HOLD",
            "signal": f"{'STRONG ' if strength=='STRONG' else ''}{direction}".strip(),
            "direction": direction,
            "strength": strength,
            "emoji": emoji,
            "css": cls,
            "price": cp,
            "tf": tf,
            "entry": float(entry),
            "entry_low": float(entry_low),
            "entry_high": float(entry_high),
            "entry_source": entry_source,
            "sl": float(sl) if sl is not None else None,
            "tp1": float(tp1) if tp1 is not None else None,
            "tp2": float(tp2) if tp2 is not None else None,
            "rr": round(tp1_mult / sl_mult, 2),
            "atr": a,
            "adx": trad["adx"],
            "rsi": trad["rsi"],
            "trad": trad,
            "smc_score": smc_score,
            "smc_reasons": smc_reasons,
            "smc_detail": smc_detail,
            "total_score": total_score,
            "confluence": confluence,
            "mtf": mtf_info,
        }


# =========================
# Sidebar Config
# =========================
with st.sidebar:
    st.header("⚙️ Settings")

    forex_pairs = st.multiselect(
        "💱 Forex",
        ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "NZD/USD", "USD/CHF"],
        default=["EUR/USD", "GBP/USD", "USD/JPY"],
    )
    metal_pairs = st.multiselect("🥇 Metals", ["XAU/USD", "XAG/USD"], default=["XAU/USD"])
    crypto_pairs = st.multiselect("₿ Crypto", ["BTC/USD", "ETH/USD", "SOL/USD", "BNB/USD"], default=["BTC/USD", "ETH/USD"])

    st.markdown("---")
    tf = st.selectbox("⏰ Timeframe (main)", ["5m", "15m", "1h", "4h", "1d"], index=2)

    st.markdown("---")
    st.subheader("✅ Filters")
    enable_mtf = st.checkbox("MTF confirmation (1 higher TF)", value=True)
    enable_adx = st.checkbox("ADX trend filter", value=True)
    adx_min = st.slider("ADX minimum", 10, 40, 20) if enable_adx else 0

    st.markdown("---")
    st.subheader("🧠 SMC Components")
    smc_ob = st.checkbox("Order Block (OB)", value=True)
    smc_fvg = st.checkbox("Fair Value Gap (FVG)", value=True)
    smc_bos = st.checkbox("Break of Structure (BOS)", value=True)
    smc_liq = st.checkbox("Liquidity sweep (EQH/EQL)", value=True)

    st.markdown("---")
    st.subheader("🎯 Signal Quality")
    min_confluence = st.slider("Min confluence score", 4, 16, 10, help="Higher = fewer but higher-quality signals")

    entry_mode = st.radio("Entry zone size", ["Conservative", "Moderate", "Aggressive"], index=1)

    st.caption("Tips: Kalau sinyal terlalu sedikit, turunkan confluence atau matikan MTF/ADX sementara.")

# =========================
# Run Scan
# =========================
pairs = forex_pairs + metal_pairs + crypto_pairs
screener = HybridSMCScreener()

scan = st.button("🚀 SCAN NOW (Hybrid SMC)")

if scan:
    if not pairs:
        st.warning("Pilih minimal 1 pair.")
        st.stop()

    st.write(f"**Scan time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.write(f"**Pairs:** {len(pairs)} | **TF:** {tf} | **MTF:** {enable_mtf} | **ADX filter:** {enable_adx} (min {adx_min}) | **Min confluence:** {min_confluence}")

    prog = st.progress(0)
    status = st.empty()
    results = []

    for i, pair in enumerate(pairs, start=1):
        status.text(f"Analyzing {pair} ({i}/{len(pairs)}) ...")
        res = screener.analyze_pair(
            pair=pair,
            tf=tf,
            enable_mtf=enable_mtf,
            enable_adx_filter=enable_adx,
            adx_min=float(adx_min),
            min_confluence=int(min_confluence),
            entry_mode=entry_mode,
            smc_enable_ob=smc_ob,
            smc_enable_fvg=smc_fvg,
            smc_enable_bos=smc_bos,
            smc_enable_liq=smc_liq,
        )
        results.append(res)
        prog.progress(i / len(pairs))
        time.sleep(0.15)

    status.empty()
    prog.empty()

    # Split buckets
    trades = [r for r in results if r.get("status") == "TRADE"]
    holds = [r for r in results if r.get("status") == "HOLD"]
    filtered = [r for r in results if r.get("status") == "FILTERED"]
    nodata = [r for r in results if r.get("status") == "NO_DATA"]

    buys = [r for r in trades if r.get("direction") == "BUY"]
    sells = [r for r in trades if r.get("direction") == "SELL"]

    # Dashboard
    st.markdown("---")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total", len(results))
    c2.metric("🟢 Buy", len(buys))
    c3.metric("🔴 Sell", len(sells))
    c4.metric("🟡 Hold", len(holds))
    c5.metric("⛔ Filtered/NoData", len(filtered) + len(nodata))

    # Utility: decimals formatting
    def decimals_for(pair: str) -> int:
        if "JPY" in pair:
            return 3
        if "XAU" in pair or "XAG" in pair:
            return 2
        if any(x in pair for x in ["BTC", "ETH", "SOL", "BNB"]):
            return 2
        return 5

    def render_card(r):
        dec = decimals_for(r["pair"])
        crypto_badge = "<span class='badge badge-crypto'>CRYPTO</span>" if any(x in r["pair"] for x in ["BTC", "ETH", "SOL", "BNB"]) else ""
        smc_badge = "<span class='badge badge-smc'>SMC</span>" if (r.get("smc_score", 0) != 0 or (r.get("smc_reasons") and len(r["smc_reasons"]) > 0)) else ""
        mtf_badge = ""
        if r.get("mtf") and r["mtf"].get("align") is True:
            mtf_badge = "<span class='badge badge-mtf'>MTF ✓</span>"

        header = f"{r.get('emoji','🟡')} {r['pair']} — {r.get('signal','HOLD')} {crypto_badge} {smc_badge} {mtf_badge}"
        subtitle = f"TF: {r.get('tf')} | Confluence: {r.get('confluence','-')} | TotalScore: {r.get('total_score','-'):+}"

        entry_block = ""
        if r.get("entry") is not None:
            entry_block = f"""
            <div class="box">
              <b>Entry Zone</b> ({entry_mode})<br/>
              Best entry: <b>{r['entry']:.{dec}f}</b> <span class="badge badge-s">{r.get('entry_source','Market')}</span><br/>
              Zone: {r['entry_low']:.{dec}f} → {r['entry_high']:.{dec}f}<br/>
              SL: <b>{r['sl']:.{dec}f}</b> | TP1: <b>{r['tp1']:.{dec}f}</b> | TP2: <b>{r['tp2']:.{dec}f}</b><br/>
              R:R (TP1): <b>1:{r.get('rr','-')}</b>
            </div>
            """

        trad_txt = ", ".join(r.get("trad", {}).get("reasons", [])[:4]) if r.get("trad") else ""
        smc_txt = ", ".join(r.get("smc_reasons", [])[:5])

        adx_txt = f"ADX: {r.get('adx', 0):.1f}" if r.get("adx") is not None else "ADX: -"
        rsi_txt = f"RSI: {r.get('rsi', 50):.1f}" if r.get("rsi") is not None else "RSI: -"

        mtf_txt = ""
        if r.get("mtf") and r["mtf"].get("htf"):
            mtf_txt = f"MTF: main {r['mtf'].get('main_dir')} vs {r['mtf'].get('htf')} {r['mtf'].get('htf_dir')} | aligned={r['mtf'].get('align')}"

        smc_zone_txt = ""
        pdz = r.get("smc_detail", {}).get("pdz")
        if pdz:
            smc_zone_txt = f"PDZ: {pdz.get('zone')} ({pdz.get('pos',0)*100:.0f}% in range)"

        st.markdown(
            f"""
            <div class="card {r.get('css','hold')}">
              <div style="font-size:20px; font-weight:900;">{header}</div>
              <div class="muted" style="margin-top:4px;">{subtitle} | {adx_txt} | {rsi_txt}</div>
              {entry_block}
              <div class="grid2">
                <div class="box">
                  <b>SMC</b><br/>
                  Score: <b>{r.get('smc_score',0):+}</b><br/>
                  {smc_zone_txt}<br/>
                  {smc_txt if smc_txt else "No strong SMC confluence detected"}
                </div>
                <div class="box">
                  <b>Traditional</b><br/>
                  Score: <b>{r.get('trad',{}).get('score',0):+}</b><br/>
                  {trad_txt if trad_txt else "No strong traditional confluence detected"}<br/>
                  <span class="muted">{mtf_txt}</span>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Sort trades by confluence
    trades_sorted = sorted(trades, key=lambda x: x.get("confluence", 0), reverse=True)

    st.markdown("---")
    st.subheader("🎯 Tradeable Signals (BUY/SELL)")
    if trades_sorted:
        for r in trades_sorted:
            render_card(r)
    else:
        st.warning(
            "Tidak ada BUY/SELL yang lolos threshold saat ini. "
            "Coba turunkan Min confluence, atau matikan MTF/ADX sementara, atau ganti timeframe."
        )

    # HOLD
    st.markdown("---")
    with st.expander(f"🟡 HOLD ({len(holds)}) — lihat setup lemah / belum matang"):
        for r in sorted(holds, key=lambda x: x.get("confluence", 0), reverse=True):
            render_card(r)

    # FILTERED
    with st.expander(f"⛔ FILTERED ({len(filtered)}) — diblokir filter ADX/MTF"):
        for r in filtered:
            st.write(f"**{r['pair']}** | {r.get('filter_reason','Filtered')} | TF: {r.get('tf')} | Price: {r.get('price')}")

    # NO DATA
    with st.expander(f"⚠️ NO DATA ({len(nodata)}) — Yahoo tidak menyediakan data untuk kombinasi ini"):
        for r in nodata:
            st.write(f"**{r['pair']}** | NO DATA. Coba timeframe lebih besar (1h/4h/1d).")

    st.markdown("---")
    st.info(
        """
**Catatan penting (SMC):**
- SMC pada tool ini bersifat *heuristic* (pendekatan otomatis), bukan pengganti analisa manual.
- OB/FVG/BOS/Liquidity di market nyata sering butuh konteks (session, range, news).
- Gunakan sebagai *screening* untuk mempersempit watchlist, lalu konfirmasi di chart.
"""
    )

# Footer
st.markdown("---")
st.caption("Hybrid SMC Screener | Data: Yahoo Finance | For educational purposes only.")
