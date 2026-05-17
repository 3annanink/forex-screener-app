import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="Pro Forex, Metal & Crypto Screener",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
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
        transform: scale(1.02);
        transition: all 0.3s;
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
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
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
    }
    .mtf-badge {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 0.8em;
        margin-left: 10px;
    }
    .entry-zone {
        background: rgba(255,255,255,0.2);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #fff;
    }
    .sr-box {
        background: rgba(255,255,255,0.15);
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 3px solid #ffd700;
    }
    .mtf-box {
        background: rgba(255,255,255,0.15);
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 3px solid #00f2fe;
    }
    .trend-box {
        background: rgba(255,255,255,0.15);
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 3px solid #ff6b6b;
    }
    .pro-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.7em;
        font-weight: bold;
        margin-left: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 30px; 
            border-radius: 15px; 
            text-align: center; 
            color: white;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);'>
    <h1 style='margin: 0; font-size: 2.5em;'>🔍 PROFESSIONAL TRADING SCREENER <span class='pro-badge'>PRO</span></h1>
    <p style='margin: 10px 0 0 0; font-size: 1.2em;'>Multi-Timeframe Analysis | Support & Resistance | Trend Filtering</p>
    <p style='margin: 5px 0 0 0; font-size: 0.9em; opacity: 0.9;'>✨ Forex • Metals • Crypto | Institutional-Grade Signals</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("📊 Select Pairs")
    
    forex_pairs = st.multiselect(
        "💱 Forex Pairs",
        ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD', 'NZD/USD', 'USD/CHF', 'EUR/JPY', 'GBP/JPY'],
        default=['EUR/USD', 'GBP/USD']
    )
    
    metal_pairs = st.multiselect(
        "🥇 Metal Pairs",
        ['XAU/USD', 'XAG/USD'],
        default=['XAU/USD']
    )
    
    crypto_pairs = st.multiselect(
        "₿ Crypto Pairs",
        ['BTC/USD', 'ETH/USD', 'SOL/USD', 'BNB/USD', 'XRP/USD', 'ADA/USD', 'DOGE/USD', 'MATIC/USD', 'DOT/USD', 'LINK/USD', 'AVAX/USD', 'LTC/USD'],
        default=['BTC/USD', 'ETH/USD']
    )
    
    st.markdown("---")
    st.subheader("⏰ Timeframe Settings")
    
    main_interval = st.selectbox(
        "Main Timeframe",
        ['5m', '15m', '1h', '4h', '1d'],
        index=2,
        help="Primary timeframe for signals"
    )
    
    st.subheader("🔄 Multi-Timeframe Analysis")
    enable_mtf = st.checkbox("Enable MTF Confirmation", value=True, help="Scan multiple timeframes for confirmation")
    
    if enable_mtf:
        mtf_strict = st.radio(
            "MTF Filter Level",
            ["Strict (All TF agree)", "Moderate (2/3 TF agree)", "Loose (Any TF)"],
            index=1
        )
    
    st.markdown("---")
    st.subheader("🎯 Advanced Filters")
    
    enable_adx_filter = st.checkbox("ADX Trend Filter", value=True, help="Filter weak/choppy markets")
    if enable_adx_filter:
        adx_threshold = st.slider("Minimum ADX", 15, 40, 25, help="Higher = stronger trend required")
    
    enable_sr_filter = st.checkbox("Support/Resistance Filter", value=True, help="Check distance to S/R levels")
    
    st.subheader("🎚️ Entry Strategy")
    entry_strategy = st.radio(
        "Entry Type",
        ["Aggressive", "Moderate", "Conservative"],
        index=1
    )
    
    st.markdown("---")
    st.info("💡 **Pro Tip:** Use 1h with MTF for best accuracy")
    
    total_pairs = len(forex_pairs) + len(metal_pairs) + len(crypto_pairs)
    st.metric("Total Pairs", total_pairs)

class ProfessionalScreener:
    def __init__(self):
        self.ticker_map = {
            'EUR/USD': 'EURUSD=X', 'GBP/USD': 'GBPUSD=X', 'USD/JPY': 'USDJPY=X',
            'AUD/USD': 'AUDUSD=X', 'USD/CAD': 'USDCAD=X', 'NZD/USD': 'NZDUSD=X',
            'USD/CHF': 'USDCHF=X', 'EUR/JPY': 'EURJPY=X', 'GBP/JPY': 'GBPJPY=X',
            'XAU/USD': 'GC=F', 'XAG/USD': 'SI=F',
            'BTC/USD': 'BTC-USD', 'ETH/USD': 'ETH-USD', 'SOL/USD': 'SOL-USD',
            'BNB/USD': 'BNB-USD', 'XRP/USD': 'XRP-USD', 'ADA/USD': 'ADA-USD',
            'DOGE/USD': 'DOGE-USD', 'MATIC/USD': 'MATIC-USD', 'DOT/USD': 'DOT-USD',
            'LINK/USD': 'LINK-USD', 'AVAX/USD': 'AVAX-USD', 'LTC/USD': 'LTC-USD'
        }
    
    def is_crypto(self, pair):
        crypto_symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'MATIC', 'DOT', 'LINK', 'AVAX', 'LTC']
        return any(symbol in pair for symbol in crypto_symbols)
    
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
                'volume': data['Volume'].values.flatten() if 'Volume' in data.columns else [0]*len(data)
            })
            
            return df.dropna().reset_index(drop=True)
        except:
            return None
    
    def calculate_indicators(self, df):
        if df is None or len(df) < 50:
            return None
        
        try:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            df['ma_20'] = df['close'].rolling(window=20).mean()
            df['ma_50'] = df['close'].rolling(window=50).mean()
            df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
            
            df['macd'] = df['ema_12'] - df['ema_26']
            df['signal_line'] = df['macd'].ewm(span=9, adjust=False).mean()
            
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['atr'] = true_range.rolling(14).mean()
            
            low_14 = df['low'].rolling(window=14).min()
            high_14 = df['high'].rolling(window=14).max()
            df['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
            
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
    
    def detect_support_resistance_simple(self, df, lookback=50):
        try:
            recent_data = df.tail(lookback)
            resistance_levels = []
            support_levels = []
            
            for i in range(2, len(recent_data) - 2):
                if (recent_data.iloc[i]['high'] > recent_data.iloc[i-1]['high'] and 
                    recent_data.iloc[i]['high'] > recent_data.iloc[i-2]['high'] and
                    recent_data.iloc[i]['high'] > recent_data.iloc[i+1]['high'] and
                    recent_data.iloc[i]['high'] > recent_data.iloc[i+2]['high']):
                    resistance_levels.append(recent_data.iloc[i]['high'])
                
                if (recent_data.iloc[i]['low'] < recent_data.iloc[i-1]['low'] and 
                    recent_data.iloc[i]['low'] < recent_data.iloc[i-2]['low'] and
                    recent_data.iloc[i]['low'] < recent_data.iloc[i+1]['low'] and
                    recent_data.iloc[i]['low'] < recent_data.iloc[i+2]['low']):
                    support_levels.append(recent_data.iloc[i]['low'])
            
            def cluster_levels(levels, threshold=0.002):
                if len(levels) == 0:
                    return []
                levels = sorted(levels)
                clustered = []
                current_cluster = [levels[0]]
                
                for level in levels[1:]:
                    if abs(level - current_cluster[-1]) / current_cluster[-1] < threshold:
                        current_cluster.append(level)
                    else:
                        clustered.append(np.mean(current_cluster))
                        current_cluster = [level]
                clustered.append(np.mean(current_cluster))
                return clustered
            
            resistance = cluster_levels(resistance_levels)
            support = cluster_levels(support_levels)
            
            return {
                'resistance': sorted(resistance, reverse=True)[:3],
                'support': sorted(support, reverse=True)[:3]
            }
        except:
            return {'resistance': [], 'support': []}
    
    def get_timeframe_hierarchy(self, main_tf):
        hierarchy_map = {
            '5m': ['15m', '1h'],
            '15m': ['1h', '4h'],
            '1h': ['4h', '1d'],
            '4h': ['1d'],
            '1d': []
        }
        return hierarchy_map.get(main_tf, [])
    
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
    
    def multi_timeframe_analysis(self, pair, main_tf):
        try:
            higher_tfs = self.get_timeframe_hierarchy(main_tf)
            
            mtf_results = {
                'main_tf': main_tf,
                'main_signal': None,
                'higher_tf_signals': [],
                'alignment': 0,
                'mtf_confirmed': False
            }
            
            df_main = self.fetch_data(pair, main_tf)
            if df_main is not None and len(df_main) >= 50:
                df_main = self.calculate_indicators(df_main)
                if df_main is not None:
                    score = self.calculate_signal_score(df_main)
                    mtf_results['main_signal'] = {
                        'tf': main_tf,
                        'score': score,
                        'direction': 'BUY' if score > 0 else 'SELL' if score < 0 else 'NEUTRAL'
                    }
            
            for tf in higher_tfs:
                df_higher = self.fetch_data(pair, tf)
                if df_higher is not None and len(df_higher) >= 50:
                    df_higher = self.calculate_indicators(df_higher)
                    if df_higher is not None:
                        score = self.calculate_signal_score(df_higher)
                        mtf_results['higher_tf_signals'].append({
                            'tf': tf,
                            'score': score,
                            'direction': 'BUY' if score > 0 else 'SELL' if score < 0 else 'NEUTRAL'
                        })
            
            if mtf_results['main_signal']:
                main_dir = mtf_results['main_signal']['direction']
                aligned_count = sum(1 for s in mtf_results['higher_tf_signals'] if s['direction'] == main_dir)
                total_tf = len(mtf_results['higher_tf_signals'])
                
                if total_tf > 0:
                    mtf_results['alignment'] = (aligned_count / total_tf) * 100
                    mtf_results['mtf_confirmed'] = mtf_results['alignment'] >= 66
            
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
                'filters_passed': [],
                'reasons': [],
                'score': 0
            }
            
            score = 0
            reasons = []
            
            if latest['rsi'] < 25:
                score += 3
                reasons.append('RSI Extreme Oversold')
            elif latest['rsi'] < 30:
                score += 2
                reasons.append('RSI Oversold')
            elif latest['rsi'] > 75:
                score -= 3
                reasons.append('RSI Extreme Overbought')
            elif latest['rsi'] > 70:
                score -= 2
                reasons.append('RSI Overbought')
            
            if latest['close'] > latest['ma_20'] > latest['ma_50']:
                score += 2
                reasons.append('Strong Uptrend')
            elif latest['close'] < latest['ma_20'] < latest['ma_50']:
                score -= 2
                reasons.append('Strong Downtrend')
            
            if latest['macd'] > latest['signal_line'] and prev['macd'] <= prev['signal_line']:
                score += 3
                reasons.append('MACD Bullish Cross')
            elif latest['macd'] < latest['signal_line'] and prev['macd'] >= prev['signal_line']:
                score -= 3
                reasons.append('MACD Bearish Cross')
            
            signal['score'] = score
            signal['reasons'] = reasons
            
            # ADX Filter
            adx_pass = True
            if enable_adx:
                adx_value = latest['adx']
                if adx_value < adx_threshold:
                    adx_pass = False
                else:
                    signal['filters_passed'].append(f"ADX: {adx_value:.1f}")
                    if adx_value > 40:
                        signal['trend_strength'] = "STRONG"
                        score += 2
                    else:
                        signal['trend_strength'] = "MODERATE"
                signal['adx'] = adx_value
            
            # MTF
            mtf_pass = True
            if enable_mtf and adx_pass:
                mtf_results = self.multi_timeframe_analysis(pair, main_tf)
                signal['mtf_analysis'] = mtf_results
                
                if mtf_results:
                    if mtf_strict == "Strict (All TF agree)":
                        mtf_pass = mtf_results['alignment'] == 100
                    elif mtf_strict == "Moderate (2/3 TF agree)":
                        mtf_pass = mtf_results['alignment'] >= 66
                    else:
                        mtf_pass = True
                    
                    if mtf_pass and mtf_results['mtf_confirmed']:
                        signal['filters_passed'].append(f"MTF: {mtf_results['alignment']:.0f}%")
                        score += 3
            
            # S/R
            if enable_sr and adx_pass and mtf_pass:
                sr_levels = self.detect_support_resistance_simple(df)
                signal['sr_levels'] = sr_levels
                
                if len(sr_levels['support']) > 0 or len(sr_levels['resistance']) > 0:
                    signal['filters_passed'].append("S/R Detected")
                    score += 1
            
            # Final signal
            if (not enable_adx or adx_pass) and (not enable_mtf or mtf_pass):
                if score >= 8:
                    signal['signal'] = 'STRONG BUY'
                    signal['color'] = '🟢🟢🟢'
                    signal['css_class'] = 'buy-signal'
                elif score >= 5:
                    signal['signal'] = 'BUY'
                    signal['color'] = '🟢🟢'
                    signal['css_class'] = 'buy-signal'
                elif score <= -8:
                    signal['signal'] = 'STRONG SELL'
                    signal['color'] = '🔴🔴🔴'
                    signal['css_class'] = 'sell-signal'
                elif score <= -5:
                    signal['signal'] = 'SELL'
                    signal['color'] = '🔴🔴'
                    signal['css_class'] = 'sell-signal'
            
            # Entry & SL/TP
            atr = latest['atr']
            current_price = latest['close']
            
            if self.is_crypto(pair):
                atr_mult = (1.0, 2.0, 3.5)
            elif 'XAU' in pair or 'XAG' in pair:
                atr_mult = (1.5, 2.5, 4.0)
            else:
                atr_mult = (2.0, 3.0, 5.0)
            
            zone_mult = {'Aggressive': 0.8, 'Conservative': 0.3, 'Moderate': 0.5}[entry_strategy]
            
            if 'BUY' in signal['signal']:
                signal['best_entry'] = current_price
                signal['entry_zone_low'] = current_price - (atr * zone_mult)
                signal['entry_zone_high'] = current_price + (atr * zone_mult)
                signal['sl'] = current_price - (atr_mult[0] * atr)
                signal['tp1'] = current_price + (atr_mult[1] * atr)
                signal['tp2'] = current_price + (atr_mult[2] * atr)
                signal['risk_reward'] = round(atr_mult[1] / atr_mult[0], 2)
            elif 'SELL' in signal['signal']:
                signal['best_entry'] = current_price
                signal['entry_zone_low'] = current_price - (atr * zone_mult)
                signal['entry_zone_high'] = current_price + (atr * zone_mult)
                signal['sl'] = current_price + (atr_mult[0] * atr)
                signal['tp1'] = current_price - (atr_mult[1] * atr)
                signal['tp2'] = current_price - (atr_mult[2] * atr)
                signal['risk_reward'] = round(atr_mult[1] / atr_mult[0], 2)
            
            signal['rsi'] = latest['rsi']
            signal['stoch_k'] = latest['stoch_k']
            
            return signal
            
        except Exception as e:
            return None
    
    def screen_all_pairs(self, all_pairs, main_tf, enable_adx, adx_threshold, enable_sr, enable_mtf, mtf_strict, entry_strategy):
        signals = []
        
        st.markdown("---")
        st.header("🔄 Scanning in Progress...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, pair in enumerate(all_pairs):
            status_text.text(f"📊 Analyzing {pair}... ({i+1}/{len(all_pairs)})")
            
            df = self.fetch_data(pair, main_tf)
            
            if df is not None and len(df) >= 50:
                df = self.calculate_indicators(df)
                if df is not None:
                    signal = self.generate_signal(
                        df, pair, entry_strategy, enable_adx, adx_threshold, 
                        enable_sr, enable_mtf, mtf_strict, main_tf
                    )
                    if signal:
                        signals.append(signal)
            
            progress_bar.progress((i + 1) / len(all_pairs))
            time.sleep(0.4)
        
        status_text.empty()
        progress_bar.empty()
        
        st.success(f"✅ Scan complete! Analyzed {len(signals)} pairs")
        
        return signals
    
    def display_signals(self, signals):
        if not signals:
            st.warning("⚠️ No signals found. Try adjusting filters.")
            return
        
        buy_signals = [s for s in signals if 'BUY' in s['signal']]
        sell_signals = [s for s in signals if 'SELL' in s['signal']]
        hold_signals = [s for s in signals if s['signal'] == 'HOLD']
        
        st.markdown("---")
        st.header("📊 Results Dashboard")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Scanned", len(signals))
        with col2:
            st.metric("🟢 Buy Signals", len(buy_signals))
        with col3:
            st.metric("🔴 Sell Signals", len(sell_signals))
        
        # Display signals
        for s in buy_signals + sell_signals:
            decimals = 2 if (s['is_crypto'] or 'XAU' in s['pair'] or 'XAG' in s['pair']) else 5
            
            crypto_badge = "<span class='crypto-badge'>CRYPTO</span>" if s['is_crypto'] else ""
            mtf_badge = "<span class='mtf-badge'>MTF ✓</span>" if s.get('mtf_analysis', {}).get('mtf_confirmed', False) else ""
            
            # MTF info
            mtf_html = ""
            if s.get('mtf_analysis'):
                mtf = s['mtf_analysis']
                if mtf.get('main_signal'):
                    main_score = mtf['main_signal']['score']
                    main_dir = mtf['main_signal']['direction']
                    mtf_html = f"""
                    <div class='mtf-box'>
                        <h4>🔄 Multi-Timeframe</h4>
                        <p>Main ({mtf['main_tf']}): {main_dir} ({main_score:+d})</p>
                    """
                    for htf in mtf.get('higher_tf_signals', []):
                        mtf_html += f"<p>HTF ({htf['tf']}): {htf['direction']} ({htf['score']:+d})</p>"
                    mtf_html += f"<p><strong>Alignment: {mtf['alignment']:.0f}%</strong></p></div>"
            
            # Display
            st.markdown(f"""
            <div class='{s["css_class"]}'>
                <h2>{s['color']} {s['pair']} - {s['signal']} {crypto_badge} {mtf_badge}</h2>
                
                <div class='entry-zone'>
                    <h3>🎯 Entry Zone</h3>
                    <p><strong>Best Entry:</strong> ${s['best_entry']:,.{decimals}f}</p>
                    <p><strong>Zone:</strong> ${s['entry_zone_low']:,.{decimals}f} - ${s['entry_zone_high']:,.{decimals}f}</p>
                </div>
                
                <p><strong>SL:</strong> ${s['sl']:,.{decimals}f} | <strong>TP1:</strong> ${s['tp1']:,.{decimals}f} | <strong>TP2:</strong> ${s['tp2']:,.{decimals}f}</p>
                <p><strong>R:R:</strong> 1:{s['risk_reward']} | <strong>RSI:</strong> {s['rsi']:.1f} | <strong>Score:</strong> {s['score']:+d}</p>
                
                {mtf_html}
                
                <p><strong>Filters:</strong> {', '.join(s['filters_passed']) if s['filters_passed'] else 'None'}</p>
                <p><strong>Reasons:</strong> {', '.join(s['reasons'][:3])}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.info("""
        ### 💡 How to Use These Signals
        
        **Entry Strategy:**
        - Enter within the entry zone (not outside!)
        - Best entry = optimal price
        - Set SL immediately after entry
        
        **Risk Management:**
        - Risk max 1-2% per trade
        - Use position sizing calculator
        - Never skip stop loss
        
        **Exit Strategy:**
        - Close 50% at TP1
        - Trail stop to breakeven
        - Let rest run to TP2
        """)
        
        st.caption(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | v3.0 PRO")

screener = ProfessionalScreener()

if st.button("🚀 START PROFESSIONAL SCAN"):
    all_pairs = forex_pairs + metal_pairs + crypto_pairs
    
    if all_pairs:
        with st.spinner("🔍 Running institutional-grade analysis..."):
            signals = screener.screen_all_pairs(
                all_pairs, main_interval, enable_adx_filter, 
                adx_threshold if enable_adx_filter else 0,
                enable_sr_filter, enable_mtf,
                mtf_strict if enable_mtf else "Moderate (2/3 TF agree)",
                entry_strategy
            )
            screener.display_signals(signals)
    else:
        st.warning("⚠️ Please select at least one pair!")

st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px; color: #666;'>
    <p>⚠️ <strong>Disclaimer:</strong> For educational purposes only. Trading involves risk.</p>
    <p>Made with ❤️ for traders | v3.0 PRO - MTF | S/R | ADX</p>
</div>
""", unsafe_allow_html=True)
