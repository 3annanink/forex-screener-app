import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

st.set_page_config(
    page_title="Hybrid SMC Screener",
    page_icon="🧠",
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
        transform: scale(1.02);
    }
    .buy-signal {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
    .sell-signal {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
    .hold-signal {
        background: linear-gradient(135deg, #a8a8a8 0%, #d0d0d0 100%);
        color: #333;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
    }
    .smc-box {
        background: rgba(255,255,255,0.15);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #ffd700;
    }
    .traditional-box {
        background: rgba(255,255,255,0.15);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #00f2fe;
    }
    .entry-zone {
        background: rgba(255,255,255,0.2);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #fff;
    }
    .smc-badge {
        background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
        padding: 5px 12px;
        border-radius: 5px;
        font-size: 0.85em;
        font-weight: bold;
        color: #333;
        margin-left: 10px;
    }
    .institutional-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 5px 12px;
        border-radius: 5px;
        font-size: 0.85em;
        font-weight: bold;
        color: white;
        margin-left: 10px;
    }
    .confluence-meter {
        background: rgba(255,255,255,0.1);
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .progress-bar {
        background: #ddd;
        border-radius: 10px;
        height: 20px;
        overflow: hidden;
    }
    .progress-fill {
        background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
        height: 100%;
        transition: width 0.3s;
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
    <h1 style='margin: 0; font-size: 2.5em;'>🧠 HYBRID SMC SCREENER</h1>
    <p style='margin: 10px 0 0 0; font-size: 1.3em;'>Smart Money Concepts + Traditional Indicators</p>
    <p style='margin: 5px 0 0 0; font-size: 0.95em; opacity: 0.95;'>Order Blocks • Fair Value Gaps • Break of Structure • Liquidity Zones</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configuration")
    
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
        ['BTC/USD', 'ETH/USD', 'SOL/USD', 'BNB/USD'],
        default=['BTC/USD', 'ETH/USD']
    )
    
    st.markdown("---")
    
    main_interval = st.selectbox(
        "⏰ Timeframe",
        ['5m', '15m', '1h', '4h', '1d'],
        index=2
    )
    
    st.markdown("---")
    st.subheader("🧠 SMC Settings")
    
    enable_ob = st.checkbox("Order Blocks", value=True, help="Detect institutional order blocks")
    enable_fvg = st.checkbox("Fair Value Gaps", value=True, help="Identify imbalances")
    enable_bos = st.checkbox("Break of Structure", value=True, help="Market structure shifts")
    enable_liquidity = st.checkbox("Liquidity Zones", value=True, help="Equal highs/lows")
    
    st.markdown("---")
    st.subheader("📊 Traditional Filters")
    
    enable_mtf = st.checkbox("Multi-Timeframe", value=True)
    enable_adx = st.checkbox("ADX Filter", value=True)
    if enable_adx:
        adx_threshold = st.slider("Min ADX", 15, 40, 20)
    
    st.markdown("---")
    st.subheader("🎯 Signal Settings")
    
    min_confluence = st.slider("Minimum Confluence", 5, 20, 12, help="Higher = fewer but stronger signals")
    
    entry_strategy = st.radio(
        "Entry Type",
        ["Conservative", "Moderate", "Aggressive"],
        index=1
    )
    
    st.markdown("---")
    total = len(forex_pairs) + len(metal_pairs) + len(crypto_pairs)
    st.metric("Total Pairs", total)
    
    st.info("🧠 **SMC Mode Active**\nFollowing institutional money flow")

class HybridSMCScreener:
    def __init__(self):
        self.ticker_map = {
            'EUR/USD': 'EURUSD=X', 'GBP/USD': 'GBPUSD=X', 'USD/JPY': 'USDJPY=X',
            'AUD/USD': 'AUDUSD=X', 'USD/CAD': 'USDCAD=X', 'NZD/USD': 'NZDUSD=X',
            'USD/CHF': 'USDCHF=X', 'XAU/USD': 'GC=F', 'XAG/USD': 'SI=F',
            'BTC/USD': 'BTC-USD', 'ETH/USD': 'ETH-USD', 'SOL/USD': 'SOL-USD', 'BNB/USD': 'BNB-USD'
        }
    
    def is_crypto(self, pair):
        return any(c in pair for c in ['BTC', 'ETH', 'SOL', 'BNB'])
    
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
    
    def calculate_traditional_indicators(self, df):
        """Traditional technical indicators"""
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
    
    def detect_order_blocks(self, df, lookback=20):
        """Detect Order Blocks (OB) - SMC Concept"""
        try:
            order_blocks = {
                'bullish_ob': [],
                'bearish_ob': []
            }
            
            recent_data = df.tail(lookback)
            
            for i in range(1, len(recent_data) - 1):
                current = recent_data.iloc[i]
                prev = recent_data.iloc[i-1]
                next_candle = recent_data.iloc[i+1]
                
                # Bullish Order Block: Last down candle before strong up move
                if (current['close'] < current['open'] and  # Bearish candle
                    next_candle['close'] > next_candle['open'] and  # Next is bullish
                    next_candle['close'] > current['high']):  # Strong move up
                    
                    order_blocks['bullish_ob'].append({
                        'price_top': current['high'],
                        'price_bottom': current['low'],
                        'price_mid': (current['high'] + current['low']) / 2,
                        'timestamp': current['timestamp'],
                        'strength': (next_candle['close'] - current['high']) / current['high']
                    })
                
                # Bearish Order Block: Last up candle before strong down move
                if (current['close'] > current['open'] and  # Bullish candle
                    next_candle['close'] < next_candle['open'] and  # Next is bearish
                    next_candle['close'] < current['low']):  # Strong move down
                    
                    order_blocks['bearish_ob'].append({
                        'price_top': current['high'],
                        'price_bottom': current['low'],
                        'price_mid': (current['high'] + current['low']) / 2,
                        'timestamp': current['timestamp'],
                        'strength': (current['low'] - next_candle['close']) / current['low']
                    })
            
            # Get most recent and strongest OBs
            if order_blocks['bullish_ob']:
                order_blocks['bullish_ob'] = sorted(order_blocks['bullish_ob'], 
                                                    key=lambda x: x['strength'], reverse=True)[:3]
            if order_blocks['bearish_ob']:
                order_blocks['bearish_ob'] = sorted(order_blocks['bearish_ob'], 
                                                     key=lambda x: x['strength'], reverse=True)[:3]
            
            return order_blocks
        except:
            return {'bullish_ob': [], 'bearish_ob': []}
    
    def detect_fair_value_gaps(self, df, lookback=20):
        """Detect Fair Value Gaps (FVG) - Imbalances"""
        try:
            fvgs = {
                'bullish_fvg': [],
                'bearish_fvg': []
            }
            
            recent_data = df.tail(lookback)
            
            for i in range(1, len(recent_data) - 1):
                candle1 = recent_data.iloc[i-1]
                candle2 = recent_data.iloc[i]
                candle3 = recent_data.iloc[i+1]
                
                # Bullish FVG: Gap between candle1 high and candle3 low
                if candle3['low'] > candle1['high']:
                    gap_size = candle3['low'] - candle1['high']
                    if gap_size > 0:
                        fvgs['bullish_fvg'].append({
                            'top': candle3['low'],
                            'bottom': candle1['high'],
                            'mid': (candle3['low'] + candle1['high']) / 2,
                            'size': gap_size,
                            'timestamp': candle2['timestamp']
                        })
                
                # Bearish FVG: Gap between candle1 low and candle3 high
                if candle3['high'] < candle1['low']:
                    gap_size = candle1['low'] - candle3['high']
                    if gap_size > 0:
                        fvgs['bearish_fvg'].append({
                            'top': candle1['low'],
                            'bottom': candle3['high'],
                            'mid': (candle1['low'] + candle3['high']) / 2,
                            'size': gap_size,
                            'timestamp': candle2['timestamp']
                        })
            
            # Filter unmitigated FVGs (price hasn't filled them yet)
            current_price = df.iloc[-1]['close']
            
            fvgs['bullish_fvg'] = [fvg for fvg in fvgs['bullish_fvg'] 
                                   if current_price < fvg['top']][:3]
            fvgs['bearish_fvg'] = [fvg for fvg in fvgs['bearish_fvg'] 
                                    if current_price > fvg['bottom']][:3]
            
            return fvgs
        except:
            return {'bullish_fvg': [], 'bearish_fvg': []}
    
    def detect_break_of_structure(self, df, lookback=30):
        """Detect Break of Structure (BOS) and Change of Character (CHoCH)"""
        try:
            recent_data = df.tail(lookback)
            
            # Find swing highs and lows
            highs = []
            lows = []
            
            for i in range(2, len(recent_data) - 2):
                # Swing High
                if (recent_data.iloc[i]['high'] > recent_data.iloc[i-1]['high'] and
                    recent_data.iloc[i]['high'] > recent_data.iloc[i-2]['high'] and
                    recent_data.iloc[i]['high'] > recent_data.iloc[i+1]['high'] and
                    recent_data.iloc[i]['high'] > recent_data.iloc[i+2]['high']):
                    highs.append({
                        'price': recent_data.iloc[i]['high'],
                        'index': i,
                        'timestamp': recent_data.iloc[i]['timestamp']
                    })
                
                # Swing Low
                if (recent_data.iloc[i]['low'] < recent_data.iloc[i-1]['low'] and
                    recent_data.iloc[i]['low'] < recent_data.iloc[i-2]['low'] and
                    recent_data.iloc[i]['low'] < recent_data.iloc[i+1]['low'] and
                    recent_data.iloc[i]['low'] < recent_data.iloc[i+2]['low']):
                    lows.append({
                        'price': recent_data.iloc[i]['low'],
                        'index': i,
                        'timestamp': recent_data.iloc[i]['timestamp']
                    })
            
            structure = {
                'bos_bullish': False,
                'bos_bearish': False,
                'trend': 'RANGING',
                'last_high': highs[-1]['price'] if highs else None,
                'last_low': lows[-1]['price'] if lows else None
            }
            
            current_price = recent_data.iloc[-1]['close']
            
            # Bullish BOS: Price breaks above recent high
            if highs and current_price > highs[-1]['price']:
                structure['bos_bullish'] = True
                structure['trend'] = 'BULLISH'
                structure['bos_level'] = highs[-1]['price']
            
            # Bearish BOS: Price breaks below recent low
            if lows and current_price < lows[-1]['price']:
                structure['bos_bearish'] = True
                structure['trend'] = 'BEARISH'
                structure['bos_level'] = lows[-1]['price']
            
            # Determine market structure
            if len(highs) >= 2 and len(lows) >= 2:
                higher_highs = highs[-1]['price'] > highs[-2]['price']
                higher_lows = lows[-1]['price'] > lows[-2]['price']
                lower_highs = highs[-1]['price'] < highs[-2]['price']
                lower_lows = lows[-1]['price'] < lows[-2]['price']
                
                if higher_highs and higher_lows:
                    structure['trend'] = 'BULLISH'
                elif lower_highs and lower_lows:
                    structure['trend'] = 'BEARISH'
            
            return structure
        except:
            return {'bos_bullish': False, 'bos_bearish': False, 'trend': 'RANGING'}
    
    def detect_liquidity_zones(self, df, lookback=50):
        """Detect liquidity zones (Equal Highs/Lows)"""
        try:
            recent_data = df.tail(lookback)
            
            liquidity = {
                'equal_highs': [],
                'equal_lows': [],
                'swept_highs': False,
                'swept_lows': False
            }
            
            # Find equal highs
            highs = recent_data['high'].values
            for i in range(len(highs) - 5):
                for j in range(i+1, min(i+10, len(highs))):
                    diff_pct = abs(highs[i] - highs[j]) / highs[i]
                    if diff_pct < 0.001:  # Within 0.1%
                        liquidity['equal_highs'].append({
                            'price': (highs[i] + highs[j]) / 2,
                            'count': 2
                        })
            
            # Find equal lows
            lows = recent_data['low'].values
            for i in range(len(lows) - 5):
                for j in range(i+1, min(i+10, len(lows))):
                    diff_pct = abs(lows[i] - lows[j]) / lows[i]
                    if diff_pct < 0.001:  # Within 0.1%
                        liquidity['equal_lows'].append({
                            'price': (lows[i] + lows[j]) / 2,
                            'count': 2
                        })
            
            # Check if liquidity was swept
            current_high = recent_data.iloc[-1]['high']
            current_low = recent_data.iloc[-1]['low']
            
            if liquidity['equal_highs']:
                highest_eq = max([eq['price'] for eq in liquidity['equal_highs']])
                if current_high > highest_eq:
                    liquidity['swept_highs'] = True
            
            if liquidity['equal_lows']:
                lowest_eq = min([eq['price'] for eq in liquidity['equal_lows']])
                if current_low < lowest_eq:
                    liquidity['swept_lows'] = True
            
            return liquidity
        except:
            return {'equal_highs': [], 'equal_lows': [], 'swept_highs': False, 'swept_lows': False}
    
    def calculate_premium_discount(self, df):
        """Calculate if price is in premium or discount zone (Fibonacci)"""
        try:
            recent_data = df.tail(50)
            
            high_50 = recent_data['high'].max()
            low_50 = recent_data['low'].min()
            current_price = df.iloc[-1]['close']
            
            # Calculate Fibonacci levels
            range_size = high_50 - low_50
            fib_50 = low_50 + (range_size * 0.5)
            fib_618 = low_50 + (range_size * 0.618)
            fib_382 = low_50 + (range_size * 0.382)
            
            position = (current_price - low_50) / range_size
            
            zone_info = {
                'high': high_50,
                'low': low_50,
                'fib_50': fib_50,
                'fib_618': fib_618,
                'fib_382': fib_382,
                'position_pct': position * 100
            }
            
            if position > 0.618:
                zone_info['zone'] = 'PREMIUM'
                zone_info['bias'] = 'SELL'
            elif position < 0.382:
                zone_info['zone'] = 'DISCOUNT'
                zone_info['bias'] = 'BUY'
            else:
                zone_info['zone'] = 'EQUILIBRIUM'
                zone_info['bias'] = 'NEUTRAL'
            
            return zone_info
        except:
            return None
    
    def generate_smc_analysis(self, df, enable_ob, enable_fvg, enable_bos, enable_liquidity):
        """Complete SMC analysis"""
        smc = {
            'order_blocks': None,
            'fvgs': None,
            'structure': None,
            'liquidity': None,
            'premium_discount': None,
            'smc_score': 0,
            'smc_reasons': []
        }
        
        try:
            current_price = df.iloc[-1]['close']
            
            # Order Blocks
            if enable_ob:
                smc['order_blocks'] = self.detect_order_blocks(df)
                
                # Check if price is at bullish OB
                for ob in smc['order_blocks']['bullish_ob']:
                    if ob['price_bottom'] <= current_price <= ob['price_top']:
                        smc['smc_score'] += 3
                        smc['smc_reasons'].append('🟢 At Bullish Order Block')
                        break
                
                # Check if price is at bearish OB
                for ob in smc['order_blocks']['bearish_ob']:
                    if ob['price_bottom'] <= current_price <= ob['price_top']:
                        smc['smc_score'] -= 3
                        smc['smc_reasons'].append('🔴 At Bearish Order Block')
                        break
            
            # Fair Value Gaps
            if enable_fvg:
                smc['fvgs'] = self.detect_fair_value_gaps(df)
                
                # Check if price is near bullish FVG
                for fvg in smc['fvgs']['bullish_fvg']:
                    if abs(current_price - fvg['mid']) / current_price < 0.002:
                        smc['smc_score'] += 2
                        smc['smc_reasons'].append('🟢 Near Bullish FVG')
                        break
                
                # Check if price is near bearish FVG
                for fvg in smc['fvgs']['bearish_fvg']:
                    if abs(current_price - fvg['mid']) / current_price < 0.002:
                        smc['smc_score'] -= 2
                        smc['smc_reasons'].append('🔴 Near Bearish FVG')
                        break
            
            # Break of Structure
            if enable_bos:
                smc['structure'] = self.detect_break_of_structure(df)
                
                if smc['structure']['bos_bullish']:
                    smc['smc_score'] += 3
                    smc['smc_reasons'].append('⭐ Bullish BOS')
                elif smc['structure']['bos_bearish']:
                    smc['smc_score'] -= 3
                    smc['smc_reasons'].append('⭐ Bearish BOS')
                
                if smc['structure']['trend'] == 'BULLISH':
                    smc['smc_score'] += 1
                    smc['smc_reasons'].append('📈 Bullish Structure')
                elif smc['structure']['trend'] == 'BEARISH':
                    smc['smc_score'] -= 1
                    smc['smc_reasons'].append('📉 Bearish Structure')
            
            # Liquidity
            if enable_liquidity:
                smc['liquidity'] = self.detect_liquidity_zones(df)
                
                if smc['liquidity']['swept_lows']:
                    smc['smc_score'] += 2
                    smc['smc_reasons'].append('💧 Lows Swept (Bullish)')
                elif smc['liquidity']['swept_highs']:
                    smc['smc_score'] -= 2
                    smc['smc_reasons'].append('💧 Highs Swept (Bearish)')
            
            # Premium/Discount
            smc['premium_discount'] = self.calculate_premium_discount(df)
            
            if smc['premium_discount']:
                if smc['premium_discount']['zone'] == 'DISCOUNT':
                    smc['smc_score'] += 2
                    smc['smc_reasons'].append('💎 Discount Zone (Buy)')
                elif smc['premium_discount']['zone'] == 'PREMIUM':
                    smc['smc_score'] -= 2
                    smc['smc_reasons'].append('💎 Premium Zone (Sell)')
            
            return smc
        except:
            return smc
    
    def generate_traditional_score(self, df):
        """Generate traditional indicators score"""
        try:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            trad_score = 0
            trad_reasons = []
            
            # RSI
            if latest['rsi'] < 30:
                trad_score += 2
                trad_reasons.append('RSI Oversold')
            elif latest['rsi'] > 70:
                trad_score -= 2
                trad_reasons.append('RSI Overbought')
            
            # MA Trend
            if latest['close'] > latest['ma_20'] > latest['ma_50']:
                trad_score += 2
                trad_reasons.append('MA Uptrend')
            elif latest['close'] < latest['ma_20'] < latest['ma_50']:
                trad_score -= 2
                trad_reasons.append('MA Downtrend')
            
            # MACD
            if latest['macd'] > latest['signal_line'] and prev['macd'] <= prev['signal_line']:
                trad_score += 3
                trad_reasons.append('MACD Bullish Cross')
            elif latest['macd'] < latest['signal_line'] and prev['macd'] >= prev['signal_line']:
                trad_score -= 3
                trad_reasons.append('MACD Bearish Cross')
            
            # ADX
            if latest['adx'] > 25:
                if latest['close'] > latest['ma_20']:
                    trad_score += 1
                else:
                    trad_score -= 1
                trad_reasons.append(f"ADX {latest['adx']:.1f} (Trending)")
            
            return {
                'score': trad_score,
                'reasons': trad_reasons,
                'rsi': latest['rsi'],
                'adx': latest['adx'],
                'macd': latest['macd']
            }
        except:
            return {'score': 0, 'reasons': [], 'rsi': 50, 'adx': 0, 'macd': 0}
    
    def generate_hybrid_signal(self, pair, main_tf, enable_ob, enable_fvg, enable_bos, enable_liquidity, enable_adx, adx_threshold, min_confluence, entry_strategy):
        """Generate hybrid signal combining SMC + Traditional"""
        try:
            df = self.fetch_data(pair, main_tf)
            
            if df is None or len(df) < 50:
                return None
            
            df = self.calculate_traditional_indicators(df)
            
            if df is None:
                return None
            
            # SMC Analysis
            smc = self.generate_smc_analysis(df, enable_ob, enable_fvg, enable_bos, enable_liquidity)
            
            # Traditional Analysis
            trad = self.generate_traditional_score(df)
            
            # ADX Filter
            if enable_adx and trad['adx'] < adx_threshold:
                return None
            
            # Combined Score
            total_score = smc['smc_score'] + trad['score']
            confluence = abs(total_score)
            
            # Filter by minimum confluence
            if confluence < min_confluence:
                return None
            
            latest = df.iloc[-1]
            atr = latest['atr']
            current_price = latest['close']
            
            signal = {
                'pair': pair,
                'price': current_price,
                'timestamp': latest['timestamp'],
                'is_crypto': self.is_crypto(pair),
                'smc_score': smc['smc_score'],
                'trad_score': trad['score'],
                'total_score': total_score,
                'confluence': confluence,
                'smc_reasons': smc['smc_reasons'],
                'trad_reasons': trad['trad_reasons'],
                'smc': smc,
                'trad': trad
            }
            
            # Determine signal
            if total_score >= 8:
                signal['signal'] = 'STRONG BUY'
                signal['color'] = '🟢🟢🟢'
                signal['css_class'] = 'buy-signal'
                signal['institutional'] = True
            elif total_score >= 5:
                signal['signal'] = 'BUY'
                signal['color'] = '🟢🟢'
                signal['css_class'] = 'buy-signal'
                signal['institutional'] = True
            elif total_score <= -8:
                signal['signal'] = 'STRONG SELL'
                signal['color'] = '🔴🔴🔴'
                signal['css_class'] = 'sell-signal'
                signal['institutional'] = True
            elif total_score <= -5:
                signal['signal'] = 'SELL'
                signal['color'] = '🔴🔴'
                signal['css_class'] = 'sell-signal'
                signal['institutional'] = True
            else:
                return None
            
            # Calculate SL/TP
            mult = (1.5, 3.0, 4.5) if self.is_crypto(pair) else (2.0, 3.0, 5.0)
            zone = {'Conservative': 0.3, 'Moderate': 0.5, 'Aggressive': 0.8}[entry_strategy]
            
            # Use Order Block for entry if available
            entry_price = current_price
            if 'BUY' in signal['signal'] and smc['order_blocks']:
                for ob in smc['order_blocks']['bullish_ob']:
                    if ob['price_bottom'] <= current_price <= ob['price_top']:
                        entry_price = ob['price_mid']
                        signal['entry_type'] = 'Order Block Entry'
                        break
            elif 'SELL' in signal['signal'] and smc['order_blocks']:
                for ob in smc['order_blocks']['bearish_ob']:
                    if ob['price_bottom'] <= current_price <= ob['price_top']:
                        entry_price = ob['price_mid']
                        signal['entry_type'] = 'Order Block Entry'
                        break
            
            if 'BUY' in signal['signal']:
                signal['entry'] = entry_price
                signal['entry_low'] = entry_price - (atr * zone)
                signal['entry_high'] = entry_price + (atr * zone)
                signal['sl'] = entry_price - (mult[0] * atr)
                signal['tp1'] = entry_price + (mult[1] * atr)
                signal['tp2'] = entry_price + (mult[2] * atr)
                signal['risk_reward'] = round(mult[1] / mult[0], 2)
            else:
                signal['entry'] = entry_price
                signal['entry_low'] = entry_price - (atr * zone)
                signal['entry_high'] = entry_price + (atr * zone)
                signal['sl'] = entry_price + (mult[0] * atr)
                signal['tp1'] = entry_
