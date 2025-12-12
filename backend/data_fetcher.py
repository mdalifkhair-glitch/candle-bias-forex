"""
Data Fetcher - TradingView tvDatafeed Integration
Free, unlimited forex data from TradingView
"""

from tvDatafeed import TvDatafeed, Interval
from datetime import datetime
from typing import Dict, List
import sqlite3
import json
import os

# Initialize TradingView datafeed
tv = TvDatafeed()

# Symbol mapping: Your format → TradingView format
SYMBOL_MAP = {
    "EUR/USD": {"symbol": "EURUSD", "exchange": "FX_IDC"},
    "GBP/USD": {"symbol": "GBPUSD", "exchange": "FX_IDC"},
    "USD/JPY": {"symbol": "USDJPY", "exchange": "FX_IDC"},
    "USD/CHF": {"symbol": "USDCHF", "exchange": "FX_IDC"},
    "USD/CAD": {"symbol": "USDCAD", "exchange": "FX_IDC"},
    "AUD/USD": {"symbol": "AUDUSD", "exchange": "FX_IDC"},
    "NZD/USD": {"symbol": "NZDUSD", "exchange": "FX_IDC"},
    "XAU/USD": {"symbol": "XAUUSD", "exchange": "OANDA"},
    "XAU/JPY": {"symbol": "XAUJPY", "exchange": "OANDA"},
    "XAU/GBP": {"symbol": "XAUGBP", "exchange": "OANDA"},
    "XAG/USD": {"symbol": "XAGUSD", "exchange": "OANDA"},
}

# SQLite cache database
DB_PATH = "/tmp/candle_cache.db"

def init_db():
    """Initialize SQLite database for caching"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candle_cache (
            cache_key TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_from_cache(cache_key: str, max_age_hours: int = 24) -> List[dict]:
    """Get data from cache if fresh enough"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT data, timestamp FROM candle_cache WHERE cache_key = ?',
            (cache_key,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            data_json, timestamp_str = result
            cache_time = datetime.fromisoformat(timestamp_str)
            age_hours = (datetime.now() - cache_time).total_seconds() / 3600
            
            if age_hours < max_age_hours:
                return json.loads(data_json)
    except Exception as e:
        print(f"Cache read error: {e}")
    
    return None

def save_to_cache(cache_key: str, data: List[dict]):
    """Save data to cache"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO candle_cache (cache_key, data, timestamp) VALUES (?, ?, ?)',
            (cache_key, json.dumps(data), datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Cache write error: {e}")

def get_candles(symbol: str, exchange: str, interval: Interval, n_bars: int = 5) -> List[dict]:
    """Fetch OHLC data from TradingView"""
    try:
        df = tv.get_hist(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            n_bars=n_bars
        )
        
        if df is None or df.empty:
            print(f"No data returned for {symbol} on {exchange}")
            return []
        
        # Convert DataFrame to list of dicts
        candles = []
        for idx, row in df.iterrows():
            candles.append({
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "date": idx.strftime('%Y-%m-%d')
            })
        
        # Reverse to get most recent first
        candles.reverse()
        return candles
        
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []

def get_timeframe_candles(display_symbol: str, timeframe: str) -> List[dict]:
    """Get candles for a specific timeframe with caching"""
    
    # Get TradingView symbol mapping
    tv_mapping = SYMBOL_MAP.get(display_symbol)
    if not tv_mapping:
        print(f"Symbol not found: {display_symbol}")
        return []
    
    # Map timeframe to TradingView interval
    interval_map = {
        "daily": Interval.in_daily,
        "weekly": Interval.in_weekly,
        "monthly": Interval.in_1_month
    }
    interval = interval_map.get(timeframe, Interval.in_daily)
    
    # Cache key
    cache_key = f"{display_symbol}_{timeframe}"
    
    # Cache duration based on timeframe
    cache_hours = {
        "daily": 24,    # Refresh daily data every 24 hours
        "weekly": 168,  # Refresh weekly data every 7 days
        "monthly": 720  # Refresh monthly data every 30 days
    }
    max_age = cache_hours.get(timeframe, 24)
    
    # Try cache first
    cached_data = get_from_cache(cache_key, max_age)
    if cached_data:
        print(f"Using cached data for {display_symbol} {timeframe}")
        return cached_data
    
    # Fetch fresh data
    print(f"Fetching fresh data for {display_symbol} {timeframe}")
    candles = get_candles(
        symbol=tv_mapping["symbol"],
        exchange=tv_mapping["exchange"],
        interval=interval,
        n_bars=5
    )
    
    # Cache the result
    if candles:
        save_to_cache(cache_key, candles)
    
    return candles

def get_all_symbols() -> List[str]:
    """Get list of all tracked symbols"""
    return list(SYMBOL_MAP.keys())

# Initialize database on module load
init_db()
