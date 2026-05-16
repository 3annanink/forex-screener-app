import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="Forex Screener",
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
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
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
    <h1 style='margin: 0; font-size: 2.5em;'>🔍 FOREX & METAL SCREENER</h1>
    <p style='margin: 10px 0 0 0; font-size: 1.2em;'>Real-time Market Analysis | Mobile-Friendly</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("📊 Select Pairs")
    forex_pairs = st.multiselect(
        "Forex Pairs",
        ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD', 'NZD/USD', 'USD/CHF'],
        default=['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD']
    )
    
    metal_pairs = st.multiselect(
        "Metal Pairs",
        ['XAU/USD', 'XAG/USD'],
        default=['XAU/USD']
    )
    
    st.subheader("⏰ Timeframe")
    interval = st.selectbox(
        "Select Interval",
        {
            '5 Minutes': '5m',
            '15 Minutes': '15m',
            '1 Hour': '1h',
            '4 Hours': '4h'
        },
        format_func=lambda x: x
    )
    interval_value = {'5 Minutes': '5m', '15 Minutes': '15m', '1 Hour': '1h', '4 Hours': '4h'}[interval]
    
    st.markdown("---")
    st.info("💡 **Tip:** Select fewer pairs for faster scanning on mobile")

# Main screener class
class ForexScreener:
    def __init__(self):
        self.ticker_map = {
            'EUR/USD': 'EURUSD=X', 'GBP/USD': 'GBPUSD=X', 'USD/JPY': 'USDJPY=X',
            'AUD/USD': 'AUDUSD=X', 'USD/CAD': 'USDCAD=X', 'NZD/USD': 'NZDUSD=X',
            'USD/CHF': 'USDCHF=X', 'XAU/USD': 'GC=F', 'XAG/USD': 'SI=F'
        }
    
    def fetch_data(self, pair, interval='5m'):
        try:
            ticker = self.ticker_map.get(pair)
            data = yf.download(ticker, period='5d', interval=interval, progress=False)
            
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
        except Exception as e:
            return None
    
    def calculate_indicators(self, df):
        if df is None or len(df) < 50:
            return None
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Moving Averages
        df['ma_20'] = df['close'].rolling(window=20).mean()
        df['ma_50'] = df['close'].rolling(window=50).mean()
        
        # MACD
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['signal_line'] = df['macd'].ewm(span=9, adjust=False).mean()
        
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
        
        return df
    
    def generate_signal(self, df, pair):
        if df is None or len(df) < 50:
            return None
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        score = 0
        reasons = []
        
        # RSI Analysis
        if latest['rsi'] < 30:
            score += 3
            reasons.append("🔥 RSI Oversold")
        elif latest['rsi'] < 40:
            score += 1
            reasons.append("RSI Bullish Zone")
        elif latest['rsi'] > 70:
            score -= 3
            reasons.append("🔥 RSI Overbought")
        elif latest['rsi'] > 60:
            score -= 1
            reasons.append("RSI Bearish Zone")
        
        # MA Analysis
        if latest['close'] > latest['ma_20'] > latest['ma_50']:
            score += 2
            reasons.append("⭐ Strong Uptrend")
        elif latest['close'] < latest['ma_20'] < latest['ma_50']:
            score -= 2
            reasons.append("⭐ Strong Downtrend")
        
        # MACD Analysis
        if latest['macd'] > latest['signal_line'] and prev['macd'] <= prev['signal_line']:
            score += 2
            reasons.append("MACD Bullish Cross")
        elif latest['macd'] < latest['signal_line'] and prev['macd'] >= prev['signal_line']:
            score -= 2
            reasons.append("MACD Bearish Cross")
        
        # Bollinger Bands
        bb_width = latest['bb_upper'] - latest['bb_lower']
        bb_position = (latest['close'] - latest['bb_lower']) / bb_width if bb_width > 0 else 0.5
        
        if bb_position < 0.2:
            score += 2
            reasons.append("Near Lower BB")
        elif bb_position > 0.8:
            score -= 2
            reasons.append("Near Upper BB")
        
        # Determine signal
        if score >= 4:
            signal = "STRONG BUY"
            color = "🟢🟢🟢"
            css_class = "buy-signal"
        elif score >= 2:
            signal = "BUY"
            color = "🟢"
            css_class = "buy-signal"
        elif score <= -4:
            signal = "STRONG SELL"
            color = "🔴🔴🔴"
            css_class = "sell-signal"
        elif score <= -2:
            signal = "SELL"
            color = "🔴"
            css_class = "sell-signal"
        else:
            signal = "HOLD"
            color = "🟡"
            css_class = "hold-signal"
        
        # Calculate SL & TP
        atr = latest['atr']
        current_price = latest['close']
        
        if 'BUY' in signal:
            sl = current_price - (2 * atr)
            tp1 = current_price + (3 * atr)
            tp2 = current_price + (5 * atr)
        elif 'SELL' in signal:
            sl = current_price + (2 * atr)
            tp1 = current_price - (3 * atr)
            tp2 = current_price - (5 * atr)
        else:
            sl = tp1 = tp2 = None
        
        return {
            'pair': pair,
            'signal': signal,
            'color': color,
            'css_class': css_class,
            'price': current_price,
            'sl': sl,
            'tp1': tp1,
            'tp2': tp2,
            'rsi': latest['rsi'],
            'score': score,
            'reasons': reasons,
            'timestamp': latest['timestamp']
        }

# Initialize screener
screener = ForexScreener()

# Main scan button
if st.button("🔄 SCAN NOW", key="scan_button"):
    all_pairs = forex_pairs + metal_pairs
    
    if not all_pairs:
        st.warning("⚠️ Please select at least one pair from the sidebar!")
    else:
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        signals = []
        total = len(all_pairs)
        
        for i, pair in enumerate(all_pairs):
            status_text.text(f"📊 Scanning {pair}... ({i+1}/{total})")
            
            df = screener.fetch_data(pair, interval_value)
            df = screener.calculate_indicators(df)
            signal = screener.generate_signal(df, pair)
            
            if signal:
                signals.append(signal)
            
            progress_bar.progress((i + 1) / total)
            time.sleep(0.3)
        
        status_text.empty()
        progress_bar.empty()
        
        st.success(f"✅ Scan complete! Found {len(signals)} pairs")
        
        # Filter signals
        buy_signals = [s for s in signals if 'BUY' in s['signal']]
        sell_signals = [s for s in signals if 'SELL' in s['signal']]
        hold_signals = [s for s in signals if s['signal'] == 'HOLD']
        
        # Display statistics
        st.markdown("---")
        st.header("📊 Market Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Pairs", len(signals))
        with col2:
            st.metric("🟢 Buy", len(buy_signals))
        with col3:
            st.metric("🔴 Sell", len(sell_signals))
        with col4:
            st.metric("🟡 Hold", len(hold_signals))
        
        # Display BUY signals
        if buy_signals:
            st.markdown("---")
            st.header("🟢 BUY SIGNALS")
            
            for s in sorted(buy_signals, key=lambda x: x['score'], reverse=True):
                decimals = 2 if 'JPY' in s['pair'] or 'XAU' in s['pair'] or 'XAG' in s['pair'] else 5
                
                st.markdown(f"""
                <div class='{s["css_class"]}'>
                    <h2>{s['color']} {s['pair']} - {s['signal']}</h2>
                    <h3>💰 Entry: {s['price']:.{decimals}f}</h3>
                    <p style='font-size: 1.1em;'>
                        <strong>🛑 Stop Loss:</strong> {s['sl']:.{decimals}f} | 
                        <strong>🎯 TP1:</strong> {s['tp1']:.{decimals}f} | 
                        <strong>🎯 TP2:</strong> {s['tp2']:.{decimals}f}
                    </p>
                    <p style='font-size: 1.1em;'><strong>📊 RSI:</strong> {s['rsi']:.1f} | <strong>Score:</strong> {s['score']:+d}</p>
                    <p style='font-size: 1.1em;'><strong>💡 Reasons:</strong> {', '.join(s['reasons'])}</p>
                    <p style='font-size: 0.9em; opacity: 0.8;'>⏰ {s['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Display SELL signals
        if sell_signals:
            st.markdown("---")
            st.header("🔴 SELL SIGNALS")
            
            for s in sorted(sell_signals, key=lambda x: abs(x['score']), reverse=True):
                decimals = 2 if 'JPY' in s['pair'] or 'XAU' in s['pair'] or 'XAG' in s['pair'] else 5
                
                st.markdown(f"""
                <div class='{s["css_class"]}'>
                    <h2>{s['color']} {s['pair']} - {s['signal']}</h2>
                    <h3>💰 Entry: {s['price']:.{decimals}f}</h3>
                    <p style='font-size: 1.1em;'>
                        <strong>🛑 Stop Loss:</strong> {s['sl']:.{decimals}f} | 
                        <strong>🎯 TP1:</strong> {s['tp1']:.{decimals}f} | 
                        <strong>🎯 TP2:</strong> {s['tp2']:.{decimals}f}
                    </p>
                    <p style='font-size: 1.1em;'><strong>📊 RSI:</strong> {s['rsi']:.1f} | <strong>Score:</strong> {s['score']:+d}</p>
                    <p style='font-size: 1.1em;'><strong>💡 Reasons:</strong> {', '.join(s['reasons'])}</p>
                    <p style='font-size: 0.9em; opacity: 0.8;'>⏰ {s['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Display HOLD signals (collapsed)
        if hold_signals:
            st.markdown("---")
            with st.expander(f"🟡 HOLD SIGNALS ({len(hold_signals)} pairs) - Click to expand"):
                for s in hold_signals:
                    decimals = 2 if 'JPY' in s['pair'] or 'XAU' in s['pair'] or 'XAG' in s['pair'] else 5
                    st.markdown(f"""
                    <div class='{s["css_class"]}'>
                        <h3>{s['color']} {s['pair']} - {s['signal']}</h3>
                        <p><strong>Price:</strong> {s['price']:.{decimals}f} | <strong>RSI:</strong> {s['rsi']:.1f} | <strong>Score:</strong> {s['score']:+d}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Trading tips
        st.markdown("---")
        st.info("""
        ### 💡 Trading Tips
        
        - **Risk Management:** Never risk more than 1-2% of your capital per trade
        - **Confirmation:** Always confirm signals with higher timeframes (H1, H4, D1)
        - **Stop Loss:** NEVER trade without a stop loss
        - **Take Profit:** Close 50% at TP1, let the rest run to TP2
        - **News:** Avoid trading during major news events (NFP, FOMC, etc.)
        - **Session:** Best to trade during London (14:00-23:00 WIB) or NY session (19:00-04:00 WIB)
        """)
        
        # Last update time
        st.markdown("---")
        st.caption(f"⏰ Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data source: Yahoo Finance")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px; color: #666;'>
    <p style='font-size: 0.9em;'>
        ⚠️ <strong>Disclaimer:</strong> This tool is for educational purposes only. 
        Trading forex and metals involves significant risk of loss. 
        Always do your own research and never invest more than you can afford to lose.
    </p>
    <p style='font-size: 0.9em;'>
        Made with ❤️ for traders | Powered by Yahoo Finance & Streamlit
    </p>
</div>
""", unsafe_allow_html=True)