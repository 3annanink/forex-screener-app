import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time
from scipy.signal import argrelextrema

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
    
    # Forex pairs
    forex_pairs = st.multiselect(
        "💱 Forex Pairs",
        ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD', 'NZD/USD', 'USD/CHF', 'EUR/JPY', 'GBP/JPY'],
        default=['EUR/USD', 'GBP/USD']
    )
    
    # Metal pairs
    metal_pairs = st.multiselect(
        "🥇 Metal Pairs",
        ['XAU/USD', 'XAG/USD'],
        default=['XAU/USD']
    )
    
    # Crypto pairs
    crypto_pairs = st.multiselect(
        "₿ Crypto Pairs",
        ['BTC/USD', 'ETH/USD', 'SOL/USD', 'BNB/USD', 'XRP/USD', 'ADA/USD', 'DOGE/USD', 'MATIC/USD', 'DOT/USD', 'LINK/USD', 'AVAX/USD', 'LTC/USD'],
        default=['BTC/USD', 'ETH/USD']
    )
    
    st.markdown("---")
    st.subheader("⏰ Timeframe Settings")
    
    # Main timeframe
    main_interval = st.selectbox(
        "Main Timeframe",
        ['5m', '15m', '1h', '4h', '1d'],
        index=2,
        help="Primary timeframe for signals"
    )
    
    # MTF Analysis
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
    
    # ADX Filter
    enable_adx_filter = st.checkbox("ADX Trend Filter", value=True, help="Filter weak/choppy markets")
    if enable_adx_filter:
        adx_threshold = st.slider("Minimum ADX", 15, 40, 25, help="Higher = stronger trend required")
    
    # S/R Filter
    enable_sr_filter = st.checkbox("Support/Resistance Filter", value=True, help="Check distance to S/R levels")
    
    st.subheader("🎚️ Entry Strategy")
    entry_strategy = st.radio(
        "Entry Type",
        ["Aggressive", "Moderate", "Conservative"],
        index=1
    )
    
    st.markdown("---")
    st.info("💡 **Pro Tip:** Use 1h with MTF for best accuracy")
    
    # Stats
    total_pairs = len(forex_pairs) + len(metal_pairs) + len(crypto_pairs)
    st.metric("Total Pairs", total_pairs)

# Main screener class
class ProfessionalScreener:
    def __init__(self):
        self.ticker_map = {
            # Forex
            'EUR/USD': 'EURUSD=X', 'GBP/USD': 'GBPUSD=X', 'USD/JPY': 'USDJPY=X',
            'AUD/USD': 'AUDUSD=X', 'USD/CAD': 'USDCAD=X', 'NZD/USD': 'NZDUSD=X',
            'USD/CHF': 'USDCHF=X', 'EUR/JPY': 'EURJPY=X', 'GBP/JPY': 'GBPJPY=X',
            # Metals
            'XAU/USD': 'GC=F', 'XAG/USD': 'SI=F',
            # Crypto
            'BTC/USD': 'BTC-USD', 'ETH/USD': 'ETH-USD', 'SOL/USD': 'SOL-USD',
            'BNB/USD': 'BNB-USD', 'XRP/USD': 'XRP-USD', 'ADA/USD': 'ADA-USD',
            'DOGE/USD': 'DOGE-USD', 'MATIC/USD': 'MATIC-USD', 'DOT/USD': 'DOT-USD',
            'LINK/USD': 'LINK-USD', 'AVAX/USD': 'AVAX-USD', 'LTC/USD': 'LTC-USD'
        }
        
        # Timeframe hierarchy for MTF
        self.tf_hierarchy = {
            '1m': ['5m', '15m', '1h'],
            '5m': ['15m', '1h', '4h'],
            '15m': ['1h', '4h', '1d'],
            '1h': ['4h', '1d', '1w'],
            '4h': ['1d', '1w', '1mo'],
            '1d': ['1w', '1mo', '3mo']
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
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Moving Averages
            df['ma_20'] = df['close'].rolling(window=20).mean()
            df['ma_50'] = df['close'].rolling(window=50).mean()
            df['ma_200'] = df['close'].rolling(window=200).mean()
            df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['signal_line'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_histogram'] = df['macd'] - df['signal_line']
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            # ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['atr'] = true_range.rolling(14).mean()
            
            # Stochastic
            low_14 = df['low'].rolling(window=14).min()
            high_14 = df['high'].rolling(window=14).max()
            df['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
            df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
            
            # ADX (Average Directional Index)
            plus_dm = df['high'].diff()
            minus_dm = -df['low'].diff()
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm < 0] = 0
            
            tr = true_range
            atr14 = tr.rolling(14).mean()
            
            plus_di = 100 * (plus_dm.rolling(14).mean() / atr14)
            minus_di = 100 * (minus_dm.rolling(14).mean() / atr14)
            
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            df['adx'] = dx.rolling(14).mean()
            df['plus_di'] = plus_di
            df['minus_di'] = minus_di
            
            return df
            
        except:
            return None
    
    def detect_support_resistance(self, df, order=5):
        """Detect support and resistance levels using local extrema"""
        try:
            # Find local maxima (resistance)
            resistance_idx = argrelextrema(df['high'].values, np.greater, order=order)[0]
            resistance_levels = df.iloc[resistance_idx]['high'].values
            
            # Find local minima (support)
            support_idx = argrelextrema(df['low'].values, np.less, order=order)[0]
            support_levels = df.iloc[support_idx]['low'].values
            
            # Get recent levels (last 50 candles)
            recent_candles = 50
            recent_resistance = [r for i, r in zip(resistance_idx, resistance_levels) if i >= len(df) - recent_candles]
            recent_support = [s for i, s in zip(support_idx, support_levels) if i >= len(df) - recent_candles]
            
            # Cluster nearby levels
            def cluster_levels(levels, threshold=0.001):
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
            
            resistance = cluster_levels(recent_resistance)
            support = cluster_levels(recent_support)
            
            return {
                'resistance': sorted(resistance, reverse=True)[:3],  # Top 3
                'support': sorted(support, reverse=True)[:3]  # Top 3
            }
        except:
            return {'resistance': [], 'support': []}
    
    def analyze_sr_distance(self, current_price, sr_levels, is_buy):
        """Analyze distance to nearest S/R levels"""
        try:
            if is_buy:
                # For BUY: check support below and resistance above
                support_below = [s for s in sr_levels['support'] if s < current_price]
                resistance_above = [r for r in sr_levels['resistance'] if r > current_price]
                
                nearest_support = max(support_below) if support_below else None
                nearest_resistance = min(resistance_above) if resistance_above else None
                
                support_distance = ((current_price - nearest_support) / current_price * 100) if nearest_support else None
                resistance_distance = ((nearest_resistance - current_price) / current_price * 100) if nearest_resistance else None
                
                return {
                    'nearest_support': nearest_support,
                    'nearest_resistance': nearest_resistance,
                    'support_distance_pct': support_distance,
                    'resistance_distance_pct': resistance_distance,
                    'sr_quality': 'GOOD' if (support_distance and support_distance < 1 and resistance_distance and resistance_distance > 2) else 'MODERATE'
                }
            else:
                # For SELL: check resistance above and support below
                resistance_above = [r for r in sr_levels['resistance'] if r > current_price]
                support_below = [s for s in sr_levels['support'] if s < current_price]
                
                nearest_resistance = min(resistance_above) if resistance_above else None
                nearest_support = max(support_below) if support_below else None
                
                resistance_distance = ((nearest_resistance - current_price) / current_price * 100) if nearest_resistance else None
                support_distance = ((current_price - nearest_support) / current_price * 100) if nearest_support else None
                
                return {
                    'nearest_resistance': nearest_resistance,
                    'nearest_support': nearest_support,
                    'resistance_distance_pct': resistance_distance,
                    'support_distance_pct': support_distance,
                    'sr_quality': 'GOOD' if (resistance_distance and resistance_distance < 1 and support_distance and support_distance > 2) else 'MODERATE'
                }
        except:
            return None
    
    def get_timeframe_hierarchy(self, main_tf):
        """Get higher timeframes for MTF analysis"""
        hierarchy_map = {
            '5m': ['15m', '1h'],
            '15m': ['1h', '4h'],
            '1h': ['4h', '1d'],
            '4h': ['1d'],
            '1d': []
        }
        return hierarchy_map.get(main_tf, [])
    
    def multi_timeframe_analysis(self, pair, main_tf):
        """Analyze multiple timeframes"""
        try:
            higher_tfs = self.get_timeframe_hierarchy(main_tf)
            
            mtf_results = {
                'main_tf': main_tf,
                'main_signal': None,
                'higher_tf_signals': [],
                'alignment': 0,
                'mtf_confirmed': False
            }
            
            # Get main timeframe signal
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
            
            # Get higher timeframe signals
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
            
            # Calculate alignment
            if mtf_results['main_signal']:
                main_dir = mtf_results['main_signal']['direction']
                aligned_count = sum(1 for s in mtf_results['higher_tf_signals'] if s['direction'] == main_dir)
                total_tf = len(mtf_results['higher_tf_signals'])
                
                if total_tf > 0:
                    mtf_results['alignment'] = (aligned_count / total_tf) * 100
                    mtf_results['mtf_confirmed'] = mtf_results['alignment'] >= 66  # 2/3 agreement
            
            return mtf_results
        except:
            return None
    
    def calculate_signal_score(self, df):
        """Calculate simplified signal score for MTF"""
        if df is None or len(df) < 50:
            return 0
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        score = 0
        
        # RSI
        if latest['rsi'] < 30:
            score += 2
        elif latest['rsi'] > 70:
            score -= 2
        
        # MA
        if latest['close'] > latest['ma_20'] > latest['ma_50']:
            score += 2
        elif latest['close'] < latest['ma_20'] < latest['ma_50']:
            score -= 2
        
        # MACD
        if latest['macd'] > latest['signal_line']:
            score += 1
        else:
            score -= 1
        
        return score
    
    def generate_signal(self, df, pair, entry_strategy, enable_adx, adx_threshold, enable_sr, enable_mtf, mtf_strict, main_tf):
        if df is None or len(df) < 50:
            return None
        
        try:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            prev2 = df.iloc[-3]
            
            signal = {
                'pair': pair,
                'price': latest['close'],
                'timestamp': latest['timestamp'],
                'signal': 'HOLD',
                'strength': 0,
                'reasons': [],
                'score': 0,
                'is_crypto': self.is_crypto(pair),
                'filters_passed': []
            }
            
            score = 0
            reasons = []
            
            # === TECHNICAL ANALYSIS ===
            
            # RSI
            if latest['rsi'] < 25:
                score += 3
                reasons.append('🔥 RSI Extreme Oversold (<25)')
            elif latest['rsi'] < 30:
                score += 2
                reasons.append('RSI Oversold (<30)')
            elif latest['rsi'] < 40:
                score += 1
                reasons.append('RSI Bullish Zone')
            elif latest['rsi'] > 75:
                score -= 3
                reasons.append('🔥 RSI Extreme Overbought (>75)')
            elif latest['rsi'] > 70:
                score -= 2
                reasons.append('RSI Overbought (>70)')
            elif latest['rsi'] > 60:
                score -= 1
                reasons.append('RSI Bearish Zone')
            
            # Moving Averages
            if latest['ma_20'] > latest['ma_50'] and prev['ma_20'] <= prev['ma_50']:
                score += 4
                reasons.append('⭐ MA Golden Cross!')
            elif latest['ma_20'] < latest['ma_50'] and prev['ma_20'] >= prev['ma_50']:
                score -= 4
                reasons.append('⭐ MA Death Cross!')
            
            if latest['close'] > latest['ma_20'] > latest['ma_50']:
                score += 2
                reasons.append('Strong Uptrend')
            elif latest['close'] < latest['ma_20'] < latest['ma_50']:
                score -= 2
                reasons.append('Strong Downtrend')
            
            # MACD
            if latest['macd'] > latest['signal_line'] and prev['macd'] <= prev['signal_line']:
                score += 3
                reasons.append('⭐ MACD Bullish Cross')
            elif latest['macd'] < latest['signal_line'] and prev['macd'] >= prev['signal_line']:
                score -= 3
                reasons.append('⭐ MACD Bearish Cross')
            
            # Bollinger Bands
            bb_width = latest['bb_upper'] - latest['bb_lower']
            bb_position = (latest['close'] - latest['bb_lower']) / bb_width if bb_width > 0 else 0.5
            
            if bb_position < 0.2:
                score += 2
                reasons.append('Near BB Lower')
            elif bb_position > 0.8:
                score -= 2
                reasons.append('Near BB Upper')
            
            # Stochastic
            if latest['stoch_k'] < 20:
                score += 1
                reasons.append('Stoch Oversold')
            elif latest['stoch_k'] > 80:
                score -= 1
                reasons.append('Stoch Overbought')
            
            signal['score'] = score
            signal['reasons'] = reasons
            
            # === FILTER 1: ADX TREND FILTER ===
            adx_pass = True
            if enable_adx:
                adx_value = latest['adx']
                if adx_value < adx_threshold:
                    adx_pass = False
                    signal['adx_status'] = f"REJECTED (ADX: {adx_value:.1f} < {adx_threshold})"
                else:
                    signal['filters_passed'].append(f"✅ ADX Filter ({adx_value:.1f})")
                    
                    # Determine trend strength
                    if adx_value > 50:
                        signal['trend_strength'] = "VERY STRONG"
                        score += 2
                    elif adx_value > 40:
                        signal['trend_strength'] = "STRONG"
                        score += 1
                    elif adx_value > 25:
                        signal['trend_strength'] = "MODERATE"
                    else:
                        signal['trend_strength'] = "WEAK"
                
                signal['adx'] = adx_value
            
            # === FILTER 2: MULTI-TIMEFRAME CONFIRMATION ===
            mtf_pass = True
            if enable_mtf and adx_pass:
                mtf_results = self.multi_timeframe_analysis(pair, main_tf)
                signal['mtf_analysis'] = mtf_results
                
                if mtf_results:
                    if mtf_strict == "Strict (All TF agree)":
                        mtf_pass = mtf_results['alignment'] == 100
                    elif mtf_strict == "Moderate (2/3 TF agree)":
                        mtf_pass = mtf_results['alignment'] >= 66
                    else:  # Loose
                        mtf_pass = True
                    
                    if mtf_pass and mtf_results['mtf_confirmed']:
                        signal['filters_passed'].append(f"✅ MTF Confirmed ({mtf_results['alignment']:.0f}%)")
                        score += 3  # Bonus for MTF confirmation
                    elif not mtf_pass:
                        signal['mtf_status'] = f"REJECTED (Alignment: {mtf_results['alignment']:.0f}%)"
            
            # === FILTER 3: SUPPORT & RESISTANCE ===
            sr_pass = True
            if enable_sr and adx_pass and mtf_pass:
                sr_levels = self.detect_support_resistance(df)
                signal['sr_levels'] = sr_levels
                
                is_buy = score > 0
                sr_analysis = self.analyze_sr_distance(latest['close'], sr_levels, is_buy)
                signal['sr_analysis'] = sr_analysis
                
                if sr_analysis:
                    if sr_analysis['sr_quality'] == 'GOOD':
                        signal['filters_passed'].append("✅ S/R Quality Good")
                        score += 2
                    else:
                        signal['filters_passed'].append("⚠️ S/R Quality Moderate")
            
            # === FINAL SIGNAL DETERMINATION ===
            
            # Only generate signal if all enabled filters pass
            if (not enable_adx or adx_pass) and (not enable_mtf or mtf_pass):
                signal['strength'] = abs(score)
                
                if score >= 10:
                    signal['signal'] = 'STRONG BUY'
                    signal['color'] = '🟢🟢🟢'
                    signal['css_class'] = 'buy-signal'
                    signal['confidence'] = 'VERY HIGH'
                elif score >= 6:
                    signal['signal'] = 'BUY'
                    signal['color'] = '🟢🟢'
                    signal['css_class'] = 'buy-signal'
                    signal['confidence'] = 'HIGH'
                elif score >= 3:
                    signal['signal'] = 'WEAK BUY'
                    signal['color'] = '🟢'
                    signal['css_class'] = 'buy-signal'
                    signal['confidence'] = 'MEDIUM'
                elif score <= -10:
                    signal['signal'] = 'STRONG SELL'
                    signal['color'] = '🔴🔴🔴'
                    signal['css_class'] = 'sell-signal'
                    signal['confidence'] = 'VERY HIGH'
                elif score <= -6:
                    signal['signal'] = 'SELL'
                    signal['color'] = '🔴🔴'
                    signal['css_class'] = 'sell-signal'
                    signal['confidence'] = 'HIGH'
                elif score <= -3:
                    signal['signal'] = 'WEAK SELL'
                    signal['color'] = '🔴'
                    signal['css_class'] = 'sell-signal'
                    signal['confidence'] = 'MEDIUM'
                else:
                    signal['signal'] = 'HOLD'
                    signal['color'] = '🟡'
                    signal['css_class'] = 'hold-signal'
                    signal['confidence'] = 'LOW'
            else:
                # Filters failed
                signal['signal'] = 'HOLD'
                signal['color'] = '🟡'
                signal['css_class'] = 'hold-signal'
                signal['confidence'] = 'FILTERED OUT'
            
            # === CALCULATE SL & TP ===
            atr = latest['atr']
            current_price = latest['close']
            
            if self.is_crypto(pair):
                atr_mult_sl = 1.0
                atr_mult_tp1 = 2.0
                atr_mult_tp2 = 3.5
            elif 'XAU' in pair or 'XAG' in pair:
                atr_mult_sl = 1.5
                atr_mult_tp1 = 2.5
                atr_mult_tp2 = 4.0
            else:
                atr_mult_sl = 2.0
                atr_mult_tp1 = 3.0
                atr_mult_tp2 = 5.0
            
            # Entry zone
            if entry_strategy == 'Aggressive':
                zone_multiplier = 0.8
            elif entry_strategy == 'Conservative':
                zone_multiplier = 0.3
            else:
                zone_multiplier = 0.5
            
            entry_zone_range = atr * zone_multiplier
            
            if 'BUY' in signal['signal']:
                signal['best_entry'] = current_price
                signal['entry_zone_low'] = current_price - entry_zone_range
                signal['entry_zone_high'] = current_price + entry_zone_range
                signal['sl'] = current_price - (atr_mult_sl * atr)
                signal['tp1'] = current_price + (atr_mult_tp1 * atr)
                signal['tp2'] = current_price + (atr_mult_tp2 * atr)
                signal['risk_reward'] = round(atr_mult_tp1 / atr_mult_sl, 2)
            elif 'SELL' in signal['signal']:
                signal['best_entry'] = current_price
                signal['entry_zone_low'] = current_price - entry_zone_range
                signal['entry_zone_high'] = current_price + entry_zone_range
                signal['sl'] = current_price + (atr_mult_sl * atr)
                signal['tp1'] = current_price - (atr_mult_tp1 * atr)
                signal['tp2'] = current_price - (atr_mult_tp2 * atr)
                signal['risk_reward'] = round(atr_mult_tp1 / atr_mult_sl, 2)
            else:
                signal['best_entry'] = current_price
                signal['entry_zone_low'] = None
                signal['entry_zone_high'] = None
                signal['sl'] = None
                signal['tp1'] = None
                signal['tp2'] = None
                signal['risk_reward'] = None
            
            signal['rsi'] = latest['rsi']
            signal['stoch_k'] = latest['stoch_k']
            signal['atr'] = atr
            
            return signal
            
        except Exception as e:
            st.error(f"Error generating signal for {pair}: {str(e)}")
            return None
    
    def screen_all_pairs(self, all_pairs, main_tf, enable_adx, adx_threshold, enable_sr, enable_mtf, mtf_strict, entry_strategy):
        signals = []
        
        st.markdown("---")
        st.header("🔄 Professional Scanning in Progress...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total = len(all_pairs)
        
        for i, pair in enumerate(all_pairs):
            status_text.text(f"🔍 Analyzing {pair} with MTF & S/R detection... ({i+1}/{total})")
            
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
            
            progress_bar.progress((i + 1) / total)
            time.sleep(0.4)  # Slightly longer for MTF analysis
        
        status_text.empty()
        progress_bar.empty()
        
        st.success(f"✅ Professional scan complete! Analyzed {len(signals)} pairs")
        
        return signals
    
    def display_signals(self, signals):
        if not signals:
            st.warning("⚠️ No signals found. Try adjusting filters or selecting more pairs.")
            return
        
        # Categorize signals
        buy_signals = [s for s in signals if 'BUY' in s['signal']]
        sell_signals = [s for s in signals if 'SELL' in s['signal']]
        hold_signals = [s for s in signals if s['signal'] == 'HOLD']
        
        filtered_out = [s for s in hold_signals if 'FILTERED OUT' in s.get('confidence', '')]
        
        # Statistics
        st.markdown("---")
        st.header("📊 Professional Analysis Dashboard")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Scanned", len(signals))
        with col2:
            st.metric("🟢 Buy Signals", len(buy_signals))
        with col3:
            st.metric("🔴 Sell Signals", len(sell_signals))
        with col4:
            st.metric("🟡 Hold", len(hold_signals) - len(filtered_out))
        with col5:
            st.metric("⛔ Filtered", len(filtered_out))
        
        # Display BUY signals
        if buy_signals:
            st.markdown("---")
            st.header("🟢 BUY SIGNALS - INSTITUTIONAL GRADE")
            
            buy_signals.sort(key=lambda x: x['score'], reverse=True)
            
            for s in buy_signals:
                self.display_detailed_signal(s)
        
        # Display SELL signals
        if sell_signals:
            st.markdown("---")
            st.header("🔴 SELL SIGNALS - INSTITUTIONAL GRADE")
            
            sell_signals.sort(key=lambda x: abs(x['score']), reverse=True)
            
            for s in sell_signals:
                self.display_detailed_signal(s)
        
        # Display filtered signals
        if filtered_out:
            st.markdown("---")
            with st.expander(f"⛔ FILTERED OUT SIGNALS ({len(filtered_out)} pairs) - Click to see why"):
                for s in filtered_out:
                    st.markdown(f"""
                    **{s['pair']}** - Score: {s['score']:+d}
                    - Reason: {s.get('adx_status', s.get('mtf_status', 'Filter criteria not met'))}
                    """)
        
        # Trading Tips
        st.markdown("---")
        st.info("""
        ### 💡 Professional Trading Guide
        
        **Understanding Filters:**
        - **ADX Filter:** Ensures strong trending market (reduces choppy/sideways trades)
        - **MTF Confirmation:** Aligns multiple timeframes (higher probability setups)
        - **S/R Analysis:** Identifies quality entry near support/resistance
        
        **How to Use These Signals:**
        1. **High Confidence Signals:** MTF Confirmed + Good S/R + Strong ADX
        2. **Entry:** Use the entry zone (don't chase outside the zone)
        3. **Stop Loss:** Always set SL before entry (non-negotiable)
        4. **Take Profit:** Close 50% at TP1, trail the rest to TP2
        5. **Risk:** Never risk more than 1-2% per trade
        
        **When to Avoid:**
        - Signals without MTF confirmation (if enabled)
        - Weak ADX (choppy market)
        - Entry too close to resistance (for BUY) or support (for SELL)
        - Major news events upcoming
        """)
        
        st.caption(f"⏰ Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 📊 Data: Yahoo Finance | 🏆 Professional Grade Analysis")
    
    def display_detailed_signal(self, s):
        """Display a single signal with all details"""
        # Determine decimals
        if s['is_crypto']:
            decimals = 2
        elif 'JPY' in s['pair']:
            decimals = 3
        elif 'XAU' in s['pair'] or 'XAG' in s['pair']:
            decimals = 2
        else:
            decimals = 5
        
        crypto_badge = f"<span class='crypto-badge'>CRYPTO</span>" if s['is_crypto'] else ""
        mtf_badge = f"<span class='mtf-badge'>MTF ✓</span>" if s.get('mtf_analysis', {}).get('mtf_confirmed', False) else ""
        
        # Entry zone calculation
        if 'JPY' in s['pair']:
            zone_range = (s['entry_zone_high'] - s['entry_zone_low']) * 100
            zone_unit = "pips"
        elif s['is_crypto']:
            zone_range = s['entry_zone_high'] - s['entry_zone_low']
            zone_unit = "USD"
        else:
            zone_range = (s['entry_zone_high'] - s['entry_zone_low']) * 10000
            zone_unit = "pips"
        
        # MTF display
        mtf_html = ""
        if s.get('mtf_analysis'):
            mtf = s['mtf_analysis']
            mtf_html = f"""
            <div class='mtf-box'>
                <h4>🔄 Multi-Timeframe Analysis</h4>
                <p style='margin: 5px 0;'><strong>Main TF ({mtf['main_tf']}):</strong> {mtf['main_signal']['direction'] if mtf.get('main_signal') else 'N/A'} ({mtf['main_signal']['score']:+d if mtf.get('main_signal') else 0})</p>
            """
            for htf in mtf.get('higher_tf_signals', []):
                mtf_html += f"<p style='margin: 5px 0;'><strong>HTF ({htf['tf']}):</strong> {htf['direction']} ({htf['score']:+d})</p>"
            mtf_html += f"<p style='margin: 5px 0; font-size: 1.1em;'><strong>Alignment:</strong> {mtf['alignment']:.0f}% {'✅' if mtf['mtf_confirmed'] else '⚠️'}</p>"
            mtf_html += "</div>"
        
        # S/R display
        sr_html = ""
        if s.get('sr_analysis'):
            sr = s['sr_analysis']
            is_buy = 'BUY' in s['signal']
            
            sr_html = f"""
            <div class='sr-box'>
                <h4>📊 Support & Resistance Analysis</h4>
            """
            
            if is_buy:
                if sr.get('nearest_support'):
                    sr_html += f"<p style='margin: 5px 0;'><strong>Nearest Support:</strong> ${sr['nearest_support']:.{decimals}f} ({sr['support_distance_pct']:.2f}% below) ✅</p>"
                if sr.get('nearest_resistance'):
                    sr_html += f"<p style='margin: 5px 0;'><strong>Nearest Resistance:</strong> ${sr['nearest_resistance']:.{decimals}f} ({sr['resistance_distance_pct']:.2f}% above)</p>"
            else:
                if sr.get('nearest_resistance'):
                    sr_html += f"<p style='margin: 5px 0;'><strong>Nearest Resistance:</strong> ${sr['nearest_resistance']:.{decimals}f} ({sr['resistance_distance_pct']:.2f}% above) ✅</p>"
                if sr.get('nearest_support'):
                    sr_html += f"<p style='margin: 5px 0;'><strong>Nearest Support:</strong> ${sr['nearest_support']:.{decimals}f} ({sr['support_distance_pct']:.2f}% below)</p>"
            
            sr_html += f"<p style='margin: 5px 0; font-size: 1.1em;'><strong>S/R Quality:</strong> {sr['sr_quality']} {'✅' if sr['sr_quality'] == 'GOOD' else '⚠️'}</p>"
            sr_html += "</div>"
        
        # Trend display
        trend_html = ""
        if s.get('adx'):
            trend_html = f"""
            <div class='trend-box'>
                <h4>📈 Trend Analysis (ADX)</h4>
                <p style='margin: 5px 0;'><strong>ADX Value:</strong> {s['adx']:.1f}</p>
                <p style='margin: 5px 0;'><strong>Trend Strength:</strong> {s.get('trend_strength', 'N/A')} {'⚡' if s.get('trend_strength') in ['STRONG', 'VERY STRONG'] else ''}</p>
                <p style='margin: 5px 0; font-size: 0.9em; opacity: 0.9;'>Strong trend = Higher probability trade</p>
            </div>
            """
        
        # Filters passed
        filters_html = ""
        if s.get('filters_passed'):
            filters_html = "<p style='font-size: 1em; margin: 10px 0;'><strong>Filters Passed:</strong><br>" + "<br>".join(s['filters_passed']) + "</p>"
        
        st.markdown(f"""
        <div class='{s["css_class"]}'>
            <h2>{s['color']} {s['pair']} - {s['signal']} {crypto_badge} {mtf_badge}</h2>
            <p style='font-size: 1.1em; opacity: 0.9;'>Confidence: {s['confidence']} | Score: {s['score']:+d}</p>
            
            <div class='entry-zone'>
                <h3>🎯 ENTRY ZONE</h3>
                <p style='font-size: 1.2em; margin: 5px 0;'>
                    <strong>📍 Best Entry:</strong> ${s['best_entry']:,.{decimals}f}
                </p>
                <p style='font-size: 1.1em; margin: 5px 0;'>
                    <strong>📊 Entry Range:</strong> ${s['entry_zone_low']:,.{decimals}f} - ${s['entry_zone_high']:,.{decimals}f}
                </p>
                <p style='font-size: 0.9em; opacity: 0.9; margin: 5px 0;'>
                    Zone Width: {zone_range:.1f} {zone_unit}
                </p>
            </div>
            
            <p style='font-size: 1.1em; margin-top: 15px;'>
                <strong>🛑 Stop Loss:</strong> ${s['sl']:,.{decimals}f} | 
                <strong>🎯 TP1:</strong> ${s['tp1']:,.{decimals}f} | 
                <strong>🎯 TP2:</strong> ${s['tp2']:,.{decimals}f}
            </p>
            <p style='font-size: 1.1em;'>
                <strong>Risk:Reward:</strong> 1:{s['risk_reward']} | 
                <strong>RSI:</strong> {s['rsi']:.1f} | 
                <strong>Stoch:</strong> {s['stoch_k']:.1f}
            </p>
            
            {mtf_html}
            {sr_html}
            {trend_html}
            {filters_html}
            
            <p style='font-size: 1em; margin-top: 10px;'><strong>💡 Technical Reasons:</strong><br>{', '.join(s['reasons'][:5])}</p>
            <p style='font-size: 0.9em; opacity: 0.8; margin-top: 10px;'>⏰ {s['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """, unsafe_allow_html=True)

# Initialize screener
screener = ProfessionalScreener()

# Main scan button
if st.button("🚀 START PROFESSIONAL SCAN", key="scan_button"):
    all_pairs = forex_pairs + metal_pairs + crypto_pairs
    
    if not all_pairs:
        st.warning("⚠️ Please select at least one pair from the sidebar!")
    else:
        with st.spinner("🔍 Running institutional-grade analysis..."):
            signals = screener.screen_all_pairs(
                all_pairs, 
                main_interval, 
                enable_adx_filter, 
                adx_threshold if enable_adx_filter else 0,
                enable_sr_filter,
                enable_mtf,
                mtf_strict if enable_mtf else "Moderate (2/3 TF agree)",
                entry_strategy
            )
            screener.display_signals(signals)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px; color: #666;'>
    <p style='font-size: 0.9em;'>
        ⚠️ <strong>Disclaimer:</strong> This is a professional-grade tool for educational purposes. 
        Trading involves significant risk. Always do your own analysis and never risk more than you can afford to lose.
    </p>
    <p style='font-size: 0.9em;'>
        Made with ❤️ for professional traders | Powered by Yahoo Finance & Advanced Analytics
    </p>
    <p style='font-size: 0.8em; opacity: 0.7;'>
        v3.0 PRO - Multi-Timeframe | Support & Resistance | ADX Trend Filter
    </p>
</div>
""", unsafe_allow_html=True)
