import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="Forex, Metal & Crypto Screener",
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
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .sell-signal {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .hold-signal {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .crypto-badge {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
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
    <h1 style='margin: 0; font-size: 2.5em;'>🔍 FOREX, METAL & CRYPTO SCREENER</h1>
    <p style='margin: 10px 0 0 0; font-size: 1.2em;'>Real-time Market Analysis | Mobile-Friendly</p>
    <p style='margin: 5px 0 0 0; font-size: 0.9em; opacity: 0.9;'>✨ With Smart Entry Zones!</p>
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
        default=['EUR/USD', 'GBP/USD', 'USD/JPY']
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
    
    st.subheader("⏰ Timeframe")
    interval = st.selectbox(
        "Select Interval",
        {
            '5 Minutes': '5m',
            '15 Minutes': '15m',
            '1 Hour': '1h',
            '4 Hours': '4h',
            '1 Day': '1d'
        },
        format_func=lambda x: x
    )
    interval_value = {'5 Minutes': '5m', '15 Minutes': '15m', '1 Hour': '1h', '4 Hours': '4h', '1 Day': '1d'}[interval]
    
    st.subheader("🎯 Entry Strategy")
    entry_strategy = st.radio(
        "Choose Entry Type",
        ["Aggressive", "Moderate", "Conservative"],
        index=1,
        help="""
        • Aggressive: Wider entry zone, easier to enter
        • Moderate: Balanced entry zone (recommended)
        • Conservative: Tight entry zone, better price
        """
    )
    
    st.markdown("---")
    st.info("💡 **Tip:** For crypto, use 1h or 4h timeframe for better signals")
    
    # Stats
    total_pairs = len(forex_pairs) + len(metal_pairs) + len(crypto_pairs)
    st.metric("Total Pairs Selected", total_pairs)

# Main screener class
class ForexMetalCryptoScreener:
    def __init__(self):
        self.ticker_map = {
            # Forex
            'EUR/USD': 'EURUSD=X',
            'GBP/USD': 'GBPUSD=X',
            'USD/JPY': 'USDJPY=X',
            'AUD/USD': 'AUDUSD=X',
            'USD/CAD': 'USDCAD=X',
            'NZD/USD': 'NZDUSD=X',
            'USD/CHF': 'USDCHF=X',
            'EUR/JPY': 'EURJPY=X',
            'GBP/JPY': 'GBPJPY=X',
            
            # Metals
            'XAU/USD': 'GC=F',
            'XAG/USD': 'SI=F',
            
            # Crypto
            'BTC/USD': 'BTC-USD',
            'ETH/USD': 'ETH-USD',
            'SOL/USD': 'SOL-USD',
            'BNB/USD': 'BNB-USD',
            'XRP/USD': 'XRP-USD',
            'ADA/USD': 'ADA-USD',
            'DOGE/USD': 'DOGE-USD',
            'MATIC/USD': 'MATIC-USD',
            'DOT/USD': 'DOT-USD',
            'LINK/USD': 'LINK-USD',
            'AVAX/USD': 'AVAX-USD',
            'LTC/USD': 'LTC-USD'
        }
    
    def is_crypto(self, pair):
        """Check if pair is crypto"""
        crypto_symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'MATIC', 'DOT', 'LINK', 'AVAX', 'LTC']
        return any(symbol in pair for symbol in crypto_symbols)
    
    def fetch_data(self, pair, interval='5m'):
        try:
            ticker = self.ticker_map.get(pair)
            
            # Crypto needs longer period for data
            period = '30d' if self.is_crypto(pair) else '5d'
            
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
        except Exception as e:
            return None
    
    def calculate_indicators(self, df):
        if df is None or len(df) < 50:
            return None
        
        try:
            # RSI (14 period)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Moving Averages
            df['ma_20'] = df['close'].rolling(window=20).mean()
            df['ma_50'] = df['close'].rolling(window=50).mean()
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
            
            # ATR (Average True Range)
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['atr'] = true_range.rolling(14).mean()
            
            # Stochastic Oscillator
            low_14 = df['low'].rolling(window=14).min()
            high_14 = df['high'].rolling(window=14).max()
            df['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
            df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
            
            return df
            
        except Exception as e:
            return None
    
    def generate_signal(self, df, pair, entry_strategy='Moderate'):
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
                'is_crypto': self.is_crypto(pair)
            }
            
            score = 0
            reasons = []
            
            # 1. RSI Analysis
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
            
            # 2. Moving Average Analysis
            if latest['ma_20'] > latest['ma_50'] and prev['ma_20'] <= prev['ma_50']:
                score += 4
                reasons.append('⭐ MA Golden Cross!')
            elif latest['ma_20'] < latest['ma_50'] and prev['ma_20'] >= prev['ma_50']:
                score -= 4
                reasons.append('⭐ MA Death Cross!')
            
            if latest['close'] > latest['ma_20'] > latest['ma_50']:
                score += 2
                reasons.append('Strong Uptrend (Price > MA20 > MA50)')
            elif latest['close'] < latest['ma_20'] < latest['ma_50']:
                score -= 2
                reasons.append('Strong Downtrend (Price < MA20 < MA50)')
            elif latest['close'] > latest['ma_20']:
                score += 1
                reasons.append('Above MA20')
            elif latest['close'] < latest['ma_20']:
                score -= 1
                reasons.append('Below MA20')
            
            # 3. MACD Analysis
            if latest['macd'] > latest['signal_line'] and prev['macd'] <= prev['signal_line']:
                score += 3
                reasons.append('⭐ MACD Bullish Cross')
            elif latest['macd'] < latest['signal_line'] and prev['macd'] >= prev['signal_line']:
                score -= 3
                reasons.append('⭐ MACD Bearish Cross')
            
            if latest['macd_histogram'] > 0 and prev['macd_histogram'] <= 0:
                score += 2
                reasons.append('MACD Histogram Bullish')
            elif latest['macd_histogram'] < 0 and prev['macd_histogram'] >= 0:
                score -= 2
                reasons.append('MACD Histogram Bearish')
            elif latest['macd_histogram'] > prev['macd_histogram'] > prev2['macd_histogram']:
                score += 1
                reasons.append('MACD Momentum+')
            elif latest['macd_histogram'] < prev['macd_histogram'] < prev2['macd_histogram']:
                score -= 1
                reasons.append('MACD Momentum-')
            
            # 4. Bollinger Bands
            bb_width = latest['bb_upper'] - latest['bb_lower']
            bb_position = (latest['close'] - latest['bb_lower']) / bb_width if bb_width > 0 else 0.5
            
            if bb_position < 0.1:
                score += 3
                reasons.append('🔥 Near BB Lower Band (Bounce Expected)')
            elif bb_position < 0.2:
                score += 2
                reasons.append('Close to BB Lower')
            elif bb_position > 0.9:
                score -= 3
                reasons.append('🔥 Near BB Upper Band (Reversal Expected)')
            elif bb_position > 0.8:
                score -= 2
                reasons.append('Close to BB Upper')
            
            # 5. Stochastic
            if latest['stoch_k'] < 20 and latest['stoch_d'] < 20:
                score += 2
                reasons.append('Stochastic Oversold')
                if latest['stoch_k'] > prev['stoch_k']:
                    score += 1
                    reasons.append('Stoch Turning Up')
            elif latest['stoch_k'] > 80 and latest['stoch_d'] > 80:
                score -= 2
                reasons.append('Stochastic Overbought')
                if latest['stoch_k'] < prev['stoch_k']:
                    score -= 1
                    reasons.append('Stoch Turning Down')
            
            # 6. Price Action
            candle_body = latest['close'] - latest['open']
            candle_range = latest['high'] - latest['low']
            body_ratio = abs(candle_body) / candle_range if candle_range > 0 else 0
            
            if candle_body > 0 and body_ratio > 0.7:
                score += 2
                reasons.append('Strong Bullish Candle')
            elif candle_body < 0 and body_ratio > 0.7:
                score -= 2
                reasons.append('Strong Bearish Candle')
            
            # 7. Volume Analysis (for crypto)
            if self.is_crypto(pair) and latest['volume'] > 0:
                avg_volume = df['volume'].tail(20).mean()
                if latest['volume'] > 1.5 * avg_volume:
                    if candle_body > 0:
                        score += 1
                        reasons.append('High Volume Bullish')
                    else:
                        score -= 1
                        reasons.append('High Volume Bearish')
            
            # Determine signal
            signal['score'] = score
            signal['strength'] = abs(score)
            signal['reasons'] = reasons
            
            if score >= 8:
                signal['signal'] = 'STRONG BUY'
                signal['color'] = '🟢🟢🟢'
                signal['css_class'] = 'buy-signal'
                signal['confidence'] = 'VERY HIGH'
            elif score >= 5:
                signal['signal'] = 'BUY'
                signal['color'] = '🟢🟢'
                signal['css_class'] = 'buy-signal'
                signal['confidence'] = 'HIGH'
            elif score >= 3:
                signal['signal'] = 'WEAK BUY'
                signal['color'] = '🟢'
                signal['css_class'] = 'buy-signal'
                signal['confidence'] = 'MEDIUM'
            elif score <= -8:
                signal['signal'] = 'STRONG SELL'
                signal['color'] = '🔴🔴🔴'
                signal['css_class'] = 'sell-signal'
                signal['confidence'] = 'VERY HIGH'
            elif score <= -5:
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
            
            # Calculate SL & TP using ATR
            atr = latest['atr']
            current_price = latest['close']
            
            # Different ATR multipliers for different asset types
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
            
            # Entry zone calculation based on strategy
            if entry_strategy == 'Aggressive':
                zone_multiplier = 0.8  # 80% of ATR for wider zone
            elif entry_strategy == 'Conservative':
                zone_multiplier = 0.3  # 30% of ATR for tighter zone
            else:  # Moderate
                zone_multiplier = 0.5  # 50% of ATR
            
            entry_zone_range = atr * zone_multiplier
            
            if 'BUY' in signal['signal']:
                signal['best_entry'] = current_price
                signal['entry_zone_low'] = current_price - entry_zone_range
                signal['entry_zone_high'] = current_price + entry_zone_range
                signal['sl'] = current_price - (atr_mult_sl * atr)
                signal['tp1'] = current_price + (atr_mult_tp1 * atr)
                signal['tp2'] = current_price + (atr_mult_tp2 * atr)
                signal['risk_reward'] = round(atr_mult_tp1 / atr_mult_sl, 2)
                signal['entry_type'] = entry_strategy
            elif 'SELL' in signal['signal']:
                signal['best_entry'] = current_price
                signal['entry_zone_low'] = current_price - entry_zone_range
                signal['entry_zone_high'] = current_price + entry_zone_range
                signal['sl'] = current_price + (atr_mult_sl * atr)
                signal['tp1'] = current_price - (atr_mult_tp1 * atr)
                signal['tp2'] = current_price - (atr_mult_tp2 * atr)
                signal['risk_reward'] = round(atr_mult_tp1 / atr_mult_sl, 2)
                signal['entry_type'] = entry_strategy
            else:
                signal['best_entry'] = current_price
                signal['entry_zone_low'] = None
                signal['entry_zone_high'] = None
                signal['sl'] = None
                signal['tp1'] = None
                signal['tp2'] = None
                signal['risk_reward'] = None
                signal['entry_type'] = None
            
            # Add technical values
            signal['rsi'] = latest['rsi']
            signal['macd'] = latest['macd']
            signal['atr'] = atr
            signal['stoch_k'] = latest['stoch_k']
            signal['bb_position'] = bb_position * 100
            signal['volume'] = latest['volume']
            
            return signal
            
        except Exception as e:
            return None
    
    def screen_all_pairs(self, all_pairs, interval, entry_strategy):
        signals = []
        
        st.markdown("---")
        st.header("🔄 Scanning Progress")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total = len(all_pairs)
        
        for i, pair in enumerate(all_pairs):
            status_text.text(f"📊 Scanning {pair}... ({i+1}/{total})")
            
            df = self.fetch_data(pair, interval)
            
            if df is not None and len(df) >= 50:
                df = self.calculate_indicators(df)
                if df is not None:
                    signal = self.generate_signal(df, pair, entry_strategy)
                    if signal:
                        signals.append(signal)
            
            progress_bar.progress((i + 1) / total)
            time.sleep(0.3)
        
        status_text.empty()
        progress_bar.empty()
        
        st.success(f"✅ Scan complete! Found {len(signals)} pairs")
        
        return signals
    
    def display_signals(self, signals):
        if not signals:
            st.warning("⚠️ No signals found. Try selecting more pairs or different timeframe.")
            return
        
        # Separate by type
        forex_signals = [s for s in signals if not s['is_crypto'] and 'XAU' not in s['pair'] and 'XAG' not in s['pair']]
        metal_signals = [s for s in signals if 'XAU' in s['pair'] or 'XAG' in s['pair']]
        crypto_signals = [s for s in signals if s['is_crypto']]
        
        # Filter by signal type
        buy_signals = [s for s in signals if 'BUY' in s['signal']]
        sell_signals = [s for s in signals if 'SELL' in s['signal']]
        hold_signals = [s for s in signals if s['signal'] == 'HOLD']
        
        # Display statistics
        st.markdown("---")
        st.header("📊 Market Statistics")
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("Total Pairs", len(signals))
        with col2:
            st.metric("🟢 Buy", len(buy_signals))
        with col3:
            st.metric("🔴 Sell", len(sell_signals))
        with col4:
            st.metric("💱 Forex", len(forex_signals))
        with col5:
            st.metric("🥇 Metals", len(metal_signals))
        with col6:
            st.metric("₿ Crypto", len(crypto_signals))
        
        # Display BUY signals
        if buy_signals:
            st.markdown("---")
            st.header("🟢 BUY SIGNALS")
            
            buy_signals.sort(key=lambda x: x['score'], reverse=True)
            
            for s in buy_signals:
                # Determine decimal places
                if s['is_crypto']:
                    decimals = 2
                elif 'JPY' in s['pair']:
                    decimals = 3
                elif 'XAU' in s['pair'] or 'XAG' in s['pair']:
                    decimals = 2
                else:
                    decimals = 5
                
                crypto_badge = f"<span class='crypto-badge'>CRYPTO</span>" if s['is_crypto'] else ""
                
                # Calculate entry zone range in pips/points
                if 'JPY' in s['pair']:
                    zone_range = (s['entry_zone_high'] - s['entry_zone_low']) * 100
                    zone_unit = "pips"
                elif s['is_crypto']:
                    zone_range = s['entry_zone_high'] - s['entry_zone_low']
                    zone_unit = "USD"
                else:
                    zone_range = (s['entry_zone_high'] - s['entry_zone_low']) * 10000
                    zone_unit = "pips"
                
                st.markdown(f"""
                <div class='{s["css_class"]}'>
                    <h2>{s['color']} {s['pair']} - {s['signal']} {crypto_badge}</h2>
                    
                    <div class='entry-zone'>
                        <h3>🎯 ENTRY ZONE ({s['entry_type']})</h3>
                        <p style='font-size: 1.2em; margin: 5px 0;'>
                            <strong>📍 Best Entry:</strong> ${s['best_entry']:,.{decimals}f}
                        </p>
                        <p style='font-size: 1.1em; margin: 5px 0;'>
                            <strong>📊 Entry Range:</strong> ${s['entry_zone_low']:,.{decimals}f} - ${s['entry_zone_high']:,.{decimals}f}
                        </p>
                        <p style='font-size: 0.9em; opacity: 0.9; margin: 5px 0;'>
                            Zone Width: {zone_range:.1f} {zone_unit} | You can enter anywhere in this range
                        </p>
                    </div>
                    
                    <p style='font-size: 1.1em; margin-top: 15px;'>
                        <strong>🛑 Stop Loss:</strong> ${s['sl']:,.{decimals}f} | 
                        <strong>🎯 TP1:</strong> ${s['tp1']:,.{decimals}f} | 
                        <strong>🎯 TP2:</strong> ${s['tp2']:,.{decimals}f}
                    </p>
                    <p style='font-size: 1.1em;'>
                        <strong>📊 RSI:</strong> {s['rsi']:.1f} | 
                        <strong>Score:</strong> {s['score']:+d} | 
                        <strong>R:R:</strong> 1:{s['risk_reward']}
                    </p>
                    <p style='font-size: 1.1em;'><strong>💡 Reasons:</strong> {', '.join(s['reasons'][:4])}</p>
                    <p style='font-size: 0.9em; opacity: 0.8;'>⏰ {s['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Display SELL signals
        if sell_signals:
            st.markdown("---")
            st.header("🔴 SELL SIGNALS")
            
            sell_signals.sort(key=lambda x: abs(x['score']), reverse=True)
            
            for s in sell_signals:
                if s['is_crypto']:
                    decimals = 2
                elif 'JPY' in s['pair']:
                    decimals = 3
                elif 'XAU' in s['pair'] or 'XAG' in s['pair']:
                    decimals = 2
                else:
                    decimals = 5
                
                crypto_badge = f"<span class='crypto-badge'>CRYPTO</span>" if s['is_crypto'] else ""
                
                # Calculate entry zone range
                if 'JPY' in s['pair']:
                    zone_range = (s['entry_zone_high'] - s['entry_zone_low']) * 100
                    zone_unit = "pips"
                elif s['is_crypto']:
                    zone_range = s['entry_zone_high'] - s['entry_zone_low']
                    zone_unit = "USD"
                else:
                    zone_range = (s['entry_zone_high'] - s['entry_zone_low']) * 10000
                    zone_unit = "pips"
                
                st.markdown(f"""
                <div class='{s["css_class"]}'>
                    <h2>{s['color']} {s['pair']} - {s['signal']} {crypto_badge}</h2>
                    
                    <div class='entry-zone'>
                        <h3>🎯 ENTRY ZONE ({s['entry_type']})</h3>
                        <p style='font-size: 1.2em; margin: 5px 0;'>
                            <strong>📍 Best Entry:</strong> ${s['best_entry']:,.{decimals}f}
                        </p>
                        <p style='font-size: 1.1em; margin: 5px 0;'>
                            <strong>📊 Entry Range:</strong> ${s['entry_zone_low']:,.{decimals}f} - ${s['entry_zone_high']:,.{decimals}f}
                        </p>
                        <p style='font-size: 0.9em; opacity: 0.9; margin: 5px 0;'>
                            Zone Width: {zone_range:.1f} {zone_unit} | You can enter anywhere in this range
                        </p>
                    </div>
                    
                    <p style='font-size: 1.1em; margin-top: 15px;'>
                        <strong>🛑 Stop Loss:</strong> ${s['sl']:,.{decimals}f} | 
                        <strong>🎯 TP1:</strong> ${s['tp1']:,.{decimals}f} | 
                        <strong>🎯 TP2:</strong> ${s['tp2']:,.{decimals}f}
                    </p>
                    <p style='font-size: 1.1em;'>
                        <strong>📊 RSI:</strong> {s['rsi']:.1f} | 
                        <strong>Score:</strong> {s['score']:+d} | 
                        <strong>R:R:</strong> 1:{s['risk_reward']}
                    </p>
                    <p style='font-size: 1.1em;'><strong>💡 Reasons:</strong> {', '.join(s['reasons'][:4])}</p>
                    <p style='font-size: 0.9em; opacity: 0.8;'>⏰ {s['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Display HOLD signals (collapsed)
        if hold_signals:
            st.markdown("---")
            with st.expander(f"🟡 HOLD SIGNALS ({len(hold_signals)} pairs) - Click to expand"):
                for s in hold_signals:
                    if s['is_crypto']:
                        decimals = 2
                    elif 'JPY' in s['pair']:
                        decimals = 3
                    elif 'XAU' in s['pair'] or 'XAG' in s['pair']:
                        decimals = 2
                    else:
                        decimals = 5
                    
                    crypto_badge = f"<span class='crypto-badge'>CRYPTO</span>" if s['is_crypto'] else ""
                    
                    st.markdown(f"""
                    <div class='{s["css_class"]}'>
                        <h3>{s['color']} {s['pair']} - {s['signal']} {crypto_badge}</h3>
                        <p><strong>Price:</strong> ${s['price']:,.{decimals}f} | <strong>RSI:</strong> {s['rsi']:.1f} | <strong>Score:</strong> {s['score']:+d}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Trading tips
        st.markdown("---")
        st.info("""
        ### 💡 Trading Tips
        
        **Entry Zone Strategy:**
        - **Best Entry:** Ideal price for maximum profit potential
        - **Entry Range:** You can enter anywhere in this zone
        - **Aggressive:** Wider zone (easier to catch), higher risk
        - **Moderate:** Balanced zone (recommended for most traders)
        - **Conservative:** Tight zone (better price), might miss some trades
        
        **How to Use Entry Zones:**
        1. Set limit order at "Best Entry" price
        2. If price doesn't reach, you can still enter within the zone
        3. The closer to "Best Entry", the better your risk/reward
        4. Don't chase price outside the zone
        
        **General Trading Rules:**
        - Risk Management: Never risk more than 1-2% per trade
        - Use Stop Loss: ALWAYS set stop loss before entry
        - Take Profit Strategy: Close 50% at TP1, let rest run to TP2
        - Confirmation: Check higher timeframes before entry
        
        **Crypto-Specific:**
        - Higher volatility = Use tighter zones
        - 24/7 market = Can enter anytime
        - News sensitive = Monitor Twitter/Telegram
        
        **Forex-Specific:**
        - Best sessions: London (14:00 WIB) & NY (19:00 WIB)
        - Avoid major news events
        - Lower spreads during high liquidity
        """)
        
        # Last update time
        st.markdown("---")
        st.caption(f"⏰ Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data source: Yahoo Finance")

# Initialize screener
screener = ForexMetalCryptoScreener()

# Main scan button
if st.button("🔄 SCAN NOW", key="scan_button"):
    all_pairs = forex_pairs + metal_pairs + crypto_pairs
    
    if not all_pairs:
        st.warning("⚠️ Please select at least one pair from the sidebar!")
    else:
        signals = screener.screen_all_pairs(all_pairs, interval_value, entry_strategy)
        screener.display_signals(signals)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px; color: #666;'>
    <p style='font-size: 0.9em;'>
        ⚠️ <strong>Disclaimer:</strong> This tool is for educational purposes only. 
        Trading forex, metals, and cryptocurrencies involves significant risk of loss. 
        Always do your own research and never invest more than you can afford to lose.
    </p>
    <p style='font-size: 0.9em;'>
        Made with ❤️ for traders | Powered by Yahoo Finance & Streamlit
    </p>
    <p style='font-size: 0.8em; opacity: 0.7;'>
        v2.1 - With Smart Entry Zones!
    </p>
</div>
""", unsafe_allow_html=True)
