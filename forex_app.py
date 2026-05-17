import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

st.set_page_config(
    page_title="Pro Forex & Crypto Screener",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .main {padding: 1rem;}
    .stButton>button {
        width: 100%;
        height: 60px;
        font-size: 20px;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    .buy-signal {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .sell-signal {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .hold-signal {
        background: linear-gradient(135deg, #a8a8a8 0%, #d0d0d0 100%);
        color: #333;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .crypto-badge {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 0.8em;
        margin-left: 10px;
        color: white;
    }
    .mtf-badge {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 0.8em;
        margin-left: 10px;
        color: white;
    }
    .entry-zone {
        background: rgba(255,255,255,0.2);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #fff;
    }
    .mtf-box {
        background: rgba(255,255,255,0.15);
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 3px solid #00f2fe;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 30px; 
            border-radius: 15px; 
            text-align: center; 
            color: white;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);'>
    <h1 style='margin: 0; font-size: 2.5em;'>🔍 PROFESSIONAL TRADING SCREENER</h1>
    <p style='margin: 10px 0 0 0; font-size: 1.2em;'>Multi-Timeframe | Support & Resistance | Trend Filter</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("📊 Select Pairs")
    
    forex_pairs = st.multiselect(
        "💱 Forex",
        ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD', 'NZD/USD', 'USD/CHF'],
        default=['EUR/USD', 'GBP/USD', 'USD/JPY']
    )
    
    metal_pairs = st.multiselect(
        "🥇 Metals",
        ['XAU/USD', 'XAG/USD'],
        default=['XAU/USD']
    )
    
    crypto_pairs = st.multiselect(
        "₿ Crypto",
        ['BTC/USD', 'ETH/USD', 'SOL/USD', 'BNB/USD', 'XRP/USD', 'ADA/USD'],
        default=['BTC/USD', 'ETH/USD']
    )
    
    st.markdown("---")
    
    main_interval = st.selectbox(
        "⏰ Main Timeframe",
        ['5m', '15m', '1h', '4h', '1d'],
        index=2
    )
    
    st.markdown("---")
    st.subheader("🎯 Filters")
    
    enable_mtf = st.checkbox("Multi-Timeframe", value=True)
    if enable_mtf:
        mtf_strict = st.radio(
            "MTF Level",
            ["Strict", "Moderate", "Loose"],
            index=1
        )
    
    enable_adx = st.checkbox("ADX Trend Filter", value=True)
    if enable_adx:
        adx_threshold = st.slider("Min ADX", 15, 40, 25)
    
    enable_sr = st.checkbox("S/R Detection", value=True)
    
    entry_strategy = st.radio(
        "Entry Type",
        ["Aggressive", "Moderate", "Conservative"],
        index=1
    )
    
    st.markdown("---")
    total = len(forex_pairs) + len(metal_pairs) + len(crypto_pairs)
    st.metric("Total Pairs", total)
    
    st.info("💡 **Tip:** If no signals, try:\n- Lower ADX to 20\n- Use 'Loose' MTF\n- Select more pairs")

class ProfessionalScreener:
    def __init__(self):
        self.ticker_map = {
            'EUR/USD': 'EURUSD=X', 'GBP/USD': 'GBPUSD=X', 'USD/JPY': 'USDJPY=X',
            'AUD/USD': 'AUDUSD=X', 'USD/CAD': 'USDCAD=X', 'NZD/USD': 'NZDUSD=X',
            'USD/CHF': 'USDCHF=X', 'XAU/USD': 'GC=F', 'XAG/USD': 'SI=F',
            'BTC/USD': 'BTC-USD', 'ETH/USD': 'ETH-USD', 'SOL/USD': 'SOL-USD',
            'BNB/USD': 'BNB-USD', 'XRP/USD': 'XRP-USD', 'ADA/USD': 'ADA-USD'
        }
    
    def is_crypto(self, pair):
        return any(c in pair for c in ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA'])
    
    def fetch_data(self, pair, interval='1h'):
        try:
            ticker = self.ticker_map.get(pair)
            period = '60d' if self.is_crypto(pair) else '30d'
            data = yf.download(ticker, period=period, interval=interval, progress=False)
            
            if data.empty:
                return None
            
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)
            
            df = pd.DataFrame({
                'timestamp': data.index,
                'open': data['Open'].values.flatten() if hasattr(data['Open'].values, 'flatten') else data['Open'].values,
                'high': data['High'].values.flatten() if hasattr(data['High'].values, 'flatten') else data['High'].values,
                'low': data['Low'].values.flatten() if hasattr(data['Low'].values, 'flatten') else data['Low'].values,
                'close': data['Close'].values.flatten() if hasattr(data['Close'].values, 'flatten') else data['Close'].values,
            })
            
            return df.dropna().reset_index(drop=True)
        except:
            return None
    
    def calculate_indicators(self, df):
        if df is None or len(df) < 50:
            return None
        
        try:
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MA
            df['ma_20'] = df['close'].rolling(window=20).mean()
            df['ma_50'] = df['close'].rolling(window=50).mean()
            df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['signal_line'] = df['macd'].ewm(span=9, adjust=False).mean()
            
            # ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['atr'] = true_range.rolling(14).mean()
            
            # ADX
            plus_dm = df['high'].diff()
            minus_dm = -df['low'].diff()
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm < 0] = 0
            
            atr14 = true_range.rolling(14).mean()
            plus_di = 100 * (plus_dm.rolling(14).mean() / atr14)
            minus_di = 100 * (minus_dm.rolling(14).mean() / atr14)
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            df['adx'] = dx.rolling(14).mean()
            
            return df
        except:
            return None
    
    def calculate_signal_score(self, df):
        if df is None or len(df) < 50:
            return 0
        
        latest = df.iloc[-1]
        score = 0
        
        if latest['rsi'] < 30:
            score += 2
        elif latest['rsi'] > 70:
            score -= 2
        
        if latest['close'] > latest['ma_20'] > latest['ma_50']:
            score += 2
        elif latest['close'] < latest['ma_20'] < latest['ma_50']:
            score -= 2
        
        if latest['macd'] > latest['signal_line']:
            score += 1
        else:
            score -= 1
        
        return score
    
    def get_timeframe_hierarchy(self, main_tf):
        hierarchy = {
            '5m': ['15m', '1h'],
            '15m': ['1h', '4h'],
            '1h': ['4h', '1d'],
            '4h': ['1d'],
            '1d': []
        }
        return hierarchy.get(main_tf, [])
    
    def multi_timeframe_analysis(self, pair, main_tf):
        try:
            higher_tfs = self.get_timeframe_hierarchy(main_tf)
            
            mtf_results = {
                'main_tf': main_tf,
                'main_score': 0,
                'main_dir': 'NEUTRAL',
                'higher_tf_signals': [],
                'alignment': 0,
                'confirmed': False
            }
            
            # Main TF
            df_main = self.fetch_data(pair, main_tf)
            if df_main is not None and len(df_main) >= 50:
                df_main = self.calculate_indicators(df_main)
                if df_main is not None:
                    score = self.calculate_signal_score(df_main)
                    mtf_results['main_score'] = score
                    mtf_results['main_dir'] = 'BUY' if score > 0 else 'SELL' if score < 0 else 'NEUTRAL'
            
            # Higher TFs
            for tf in higher_tfs:
                df_h = self.fetch_data(pair, tf)
                if df_h is not None and len(df_h) >= 50:
                    df_h = self.calculate_indicators(df_h)
                    if df_h is not None:
                        score = self.calculate_signal_score(df_h)
                        direction = 'BUY' if score > 0 else 'SELL' if score < 0 else 'NEUTRAL'
                        mtf_results['higher_tf_signals'].append({
                            'tf': tf,
                            'dir': direction,
                            'score': score
                        })
            
            # Calculate alignment
            if mtf_results['main_dir'] != 'NEUTRAL':
                aligned = sum(1 for s in mtf_results['higher_tf_signals'] if s['dir'] == mtf_results['main_dir'])
                total = len(mtf_results['higher_tf_signals'])
                if total > 0:
                    mtf_results['alignment'] = (aligned / total) * 100
                    mtf_results['confirmed'] = mtf_results['alignment'] >= 66
            
            return mtf_results
        except:
            return None
    
    def generate_signal(self, df, pair, entry_strategy, enable_adx, adx_threshold, enable_sr, enable_mtf, mtf_strict, main_tf):
        if df is None or len(df) < 50:
            return None
        
        try:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            signal = {
                'pair': pair,
                'price': latest['close'],
                'timestamp': latest['timestamp'],
                'signal': 'HOLD',
                'is_crypto': self.is_crypto(pair),
                'reasons': [],
                'filters': [],
                'score': 0,
                'filter_status': 'PASSED'
            }
            
            score = 0
            reasons = []
            
            # Technical analysis
            if latest['rsi'] < 30:
                score += 2
                reasons.append('RSI Oversold')
            elif latest['rsi'] > 70:
                score -= 2
                reasons.append('RSI Overbought')
            
            if latest['close'] > latest['ma_20'] > latest['ma_50']:
                score += 2
                reasons.append('Uptrend')
            elif latest['close'] < latest['ma_20'] < latest['ma_50']:
                score -= 2
                reasons.append('Downtrend')
            
            if latest['macd'] > latest['signal_line'] and prev['macd'] <= prev['signal_line']:
                score += 3
                reasons.append('MACD Bullish')
            elif latest['macd'] < latest['signal_line'] and prev['macd'] >= prev['signal_line']:
                score -= 3
                reasons.append('MACD Bearish')
            
            signal['score'] = score
            signal['reasons'] = reasons
            
            # Filters
            passed_all = True
            
            # ADX Filter
            if enable_adx:
                adx_val = latest['adx']
                signal['adx'] = adx_val
                if adx_val < adx_threshold:
                    passed_all = False
                    signal['filter_status'] = f'FILTERED (ADX {adx_val:.1f} < {adx_threshold})'
                else:
                    signal['filters'].append(f'ADX: {adx_val:.1f}')
                    if adx_val > 40:
                        score += 2
            
            # MTF Filter
            if enable_mtf and passed_all:
                mtf = self.multi_timeframe_analysis(pair, main_tf)
                signal['mtf'] = mtf
                
                if mtf:
                    if mtf_strict == "Strict":
                        passed_all = mtf['alignment'] == 100
                    elif mtf_strict == "Moderate":
                        passed_all = mtf['alignment'] >= 66
                    
                    if not passed_all:
                        signal['filter_status'] = f'FILTERED (MTF {mtf["alignment"]:.0f}%)'
                    else:
                        signal['filters'].append(f'MTF: {mtf["alignment"]:.0f}%')
                        if mtf['confirmed']:
                            score += 3
            
            signal['score'] = score
            
            # Final signal
            if passed_all:
                if score >= 7:
                    signal['signal'] = 'STRONG BUY'
                    signal['color'] = '🟢🟢🟢'
                    signal['css_class'] = 'buy-signal'
                elif score >= 4:
                    signal['signal'] = 'BUY'
                    signal['color'] = '🟢🟢'
                    signal['css_class'] = 'buy-signal'
                elif score <= -7:
                    signal['signal'] = 'STRONG SELL'
                    signal['color'] = '🔴🔴🔴'
                    signal['css_class'] = 'sell-signal'
                elif score <= -4:
                    signal['signal'] = 'SELL'
                    signal['color'] = '🔴🔴'
                    signal['css_class'] = 'sell-signal'
                else:
                    signal['signal'] = 'HOLD'
                    signal['color'] = '🟡'
                    signal['css_class'] = 'hold-signal'
            else:
                signal['signal'] = 'HOLD'
                signal['color'] = '⚪'
                signal['css_class'] = 'hold-signal'
            
            # SL/TP
            atr = latest['atr']
            price = latest['close']
            
            mult = (1.0, 2.0, 3.5) if self.is_crypto(pair) else (2.0, 3.0, 5.0)
            zone = {'Aggressive': 0.8, 'Moderate': 0.5, 'Conservative': 0.3}[entry_strategy]
            
            if 'BUY' in signal['signal']:
                signal['entry'] = price
                signal['entry_low'] = price - (atr * zone)
                signal['entry_high'] = price + (atr * zone)
                signal['sl'] = price - (mult[0] * atr)
                signal['tp1'] = price + (mult[1] * atr)
                signal['tp2'] = price + (mult[2] * atr)
            elif 'SELL' in signal['signal']:
                signal['entry'] = price
                signal['entry_low'] = price - (atr * zone)
                signal['entry_high'] = price + (atr * zone)
                signal['sl'] = price + (mult[0] * atr)
                signal['tp1'] = price - (mult[1] * atr)
                signal['tp2'] = price - (mult[2] * atr)
            
            signal['rsi'] = latest['rsi']
            
            return signal
        except:
            return None
    
    def screen_all_pairs(self, all_pairs, main_tf, enable_adx, adx_threshold, enable_sr, enable_mtf, mtf_strict, entry_strategy):
        signals = []
        
        st.markdown("---")
        st.header("🔄 Scanning...")
        
        progress = st.progress(0)
        status = st.empty()
        
        for i, pair in enumerate(all_pairs):
            status.text(f"📊 {pair}... ({i+1}/{len(all_pairs)})")
            
            df = self.fetch_data(pair, main_tf)
            if df is not None and len(df) >= 50:
                df = self.calculate_indicators(df)
                if df is not None:
                    sig = self.generate_signal(df, pair, entry_strategy, enable_adx, adx_threshold, enable_sr, enable_mtf, mtf_strict, main_tf)
                    if sig:
                        signals.append(sig)
            
            progress.progress((i + 1) / len(all_pairs))
            time.sleep(0.3)
        
        status.empty()
        progress.empty()
        
        st.success(f"✅ Analyzed {len(signals)} pairs")
        
        return signals
    
    def display_signals(self, signals):
        if not signals:
            st.warning("⚠️ No pairs analyzed. Check your settings.")
            return
        
        buy = [s for s in signals if 'BUY' in s['signal']]
        sell = [s for s in signals if 'SELL' in s['signal']]
        hold = [s for s in signals if s['signal'] == 'HOLD']
        filtered = [s for s in hold if 'FILTERED' in s['filter_status']]
        
        st.markdown("---")
        st.header("📊 Results")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total", len(signals))
        col2.metric("🟢 Buy", len(buy))
        col3.metric("🔴 Sell", len(sell))
        col4.metric("🟡 Hold", len(hold) - len(filtered))
        col5.metric("⚪ Filtered", len(filtered))
        
        # Display BUY
        if buy:
            st.markdown("### 🟢 BUY SIGNALS")
            for s in sorted(buy, key=lambda x: x['score'], reverse=True):
                self.display_signal_card(s)
        
        # Display SELL
        if sell:
            st.markdown("### 🔴 SELL SIGNALS")
            for s in sorted(sell, key=lambda x: abs(x['score']), reverse=True):
                self.display_signal_card(s)
        
        # Display HOLD (not filtered)
        active_hold = [h for h in hold if 'FILTERED' not in h['filter_status']]
        if active_hold:
            with st.expander(f"🟡 HOLD SIGNALS ({len(active_hold)}) - Click to expand"):
                for s in active_hold:
                    dec = 2 if (s['is_crypto'] or 'XAU' in s['pair']) else 5
                    st.markdown(f"""
                    **{s['color']} {s['pair']}** - Score: {s['score']:+d} | RSI: {s['rsi']:.1f} | Price: ${s['price']:,.{dec}f}
                    
                    Reasons: {', '.join(s['reasons']) if s['reasons'] else 'Weak setup'}
                    """)
        
        # Display FILTERED
        if filtered:
            with st.expander(f"⚪ FILTERED OUT ({len(filtered)}) - Why they didn't pass"):
                for s in filtered:
                    st.markdown(f"""
                    **{s['pair']}** - {s['filter_status']}
                    
                    Score: {s['score']:+d} | Reasons: {', '.join(s['reasons']) if s['reasons'] else 'N/A'}
                    """)
        
        # No tradeable signals warning
        if not buy and not sell:
            st.warning("""
            ### ⚠️ No Tradeable Signals Found
            
            **What to do:**
            1. **Relax Filters:**
               - Lower ADX threshold to 20
               - Change MTF to 'Loose'
               - Disable some filters temporarily
            
            2. **Try Different Timeframe:**
               - Current might be choppy
               - Try 1h or 4h
            
            3. **Add More Pairs:**
               - More pairs = more opportunities
            
            4. **Wait for Better Setup:**
               - Market might be ranging
               - Come back in 1-2 hours
            
            💡 **This is normal!** Not every scan produces signals. Quality > Quantity.
            """)
        
        st.markdown("---")
        st.info("""
        ### 💡 Understanding Results
        
        - **🟢 BUY/SELL**: Trade these (passed all filters)
        - **🟡 HOLD**: Weak setup, wait for better entry
        - **⚪ FILTERED**: Didn't pass ADX/MTF filters
        
        **Tip:** If too many filtered, lower filter strictness!
        """)
    
    def display_signal_card(self, s):
        dec = 2 if (s['is_crypto'] or 'XAU' in s['pair']) else 5
        badge = "<span class='crypto-badge'>CRYPTO</span>" if s['is_crypto'] else ""
        mtf_badge = "<span class='mtf-badge'>MTF ✓</span>" if s.get('mtf', {}).get('confirmed', False) else ""
        
        mtf_html = ""
        if s.get('mtf'):
            m = s['mtf']
            mtf_html = f"""
            <div class='mtf-box'>
                <strong>Multi-Timeframe:</strong> {m['main_dir']} ({m['main_score']:+d}) | 
                Alignment: {m['alignment']:.0f}%
            </div>
            """
        
        st.markdown(f"""
        <div class='{s["css_class"]}'>
            <h2>{s['color']} {s['pair']} - {s['signal']} {badge} {mtf_badge}</h2>
            
            <div class='entry-zone'>
                <strong>Entry:</strong> ${s['entry']:,.{dec}f} 
                (Zone: ${s['entry_low']:,.{dec}f} - ${s['entry_high']:,.{dec}f})
            </div>
            
            <p><strong>SL:</strong> ${s['sl']:,.{dec}f} | 
            <strong>TP1:</strong> ${s['tp1']:,.{dec}f} | 
            <strong>TP2:</strong> ${s['tp2']:,.{dec}f}</p>
            
            <p><strong>Score:</strong> {s['score']:+d} | 
            <strong>RSI:</strong> {s['rsi']:.1f} | 
            <strong>Filters:</strong> {', '.join(s['filters']) if s['filters'] else 'None'}</p>
            
            {mtf_html}
            
            <p><strong>Reasons:</strong> {', '.join(s['reasons'])}</p>
        </div>
        """, unsafe_allow_html=True)

screener = ProfessionalScreener()

if st.button("🚀 START SCAN"):
    all_pairs = forex_pairs + metal_pairs + crypto_pairs
    
    if all_pairs:
        signals = screener.screen_all_pairs(
            all_pairs, main_interval, enable_adx, 
            adx_threshold if enable_adx else 0,
            enable_sr, enable_mtf,
            mtf_strict if enable_mtf else "Moderate",
            entry_strategy
        )
        screener.display_signals(signals)
    else:
        st.warning("⚠️ Select pairs first!")

st.markdown("---")
st.caption("v3.1 PRO - Improved Display | Shows All Signals")
