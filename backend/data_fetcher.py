"""
Data Fetcher - Alpha Vantage API Integration
Official, reliable forex data API
Free tier: 25 API calls/day
Get free key at: https://www.alphavantage.co/support/#api-key
"""

import requests
from datetime import datetime
from typing import Dict, List
import sqlite3
import json
import os

# Alpha Vantage API
BASE_URL = "https://www.alphavantage.co/query"

def get_api_key():
    """Get API key from environment variable"""
    # Default demo key for testing (limited, get your own free key)
    return os.environ.get("ALPHAVANTAGE_API_KEY", "demo")

# Symbol mapping: Your format → Alpha Vantage format
SYMBOL_MAP = {
    "EUR/USD": "EURUSD",
    "GBP/USD": "GBPUSD",
    "USD/JPY": "USDJPY",
    "USD/CHF": "USDCHF",
    "USD/CAD": "USDCAD",
    "AUD/USD": "AUDUSD",
    "NZD/USD": "NZDUSD",
    "XAU/USD": "XAUUSD",  # Gold
    "XAU/JPY": "XAUJPY",  # May not be available
    "XAU/GBP": "XAUGBP",  # May not be available
    "XAG/USD": "XAGUSD",  # Silver
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

def get_candles_alphavantage(from_symbol: str, to_symbol: str, function: str) -> List[dict]:
    """
    Fetch OHLC data from Alpha Vantage
    function: FX_DAILY, FX_WEEKLY, FX_MONTHLY
    """
    try:
        params = {
            "function": function,
            "from_symbol": from_symbol,
            "to_symbol": to_symbol,
            "apikey": get_api_key(),
            "outputsize": "compact"  # Last 100 data points
        }
        
        response = requests.get(BASE_URL, params=params, timeout=15)
        data = response.json()
        
        # Check for errors
        if "Error Message" in data:
            print(f"API Error: {data['Error Message']}")
            return []
        
        if "Note" in data:
            print(f"API Note: {data['Note']}")  # Rate limit message
            return []
        
        # Get time series data
        time_series_key = None
        for key in data.keys():
            if "Time Series" in key:
                time_series_key = key
                break
        
        if not time_series_key:
            print(f"No time series data found for {from_symbol}/{to_symbol}")
            return []
        
        time_series = data[time_series_key]
        
        # Convert to our format
        candles = []
        for date_str, values in sorted(time_series.items(), reverse=True)[:5]:
            candles.append({
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "date": date_str
            })
        
        return candles
        
    except Exception as e:
        print(f"Error fetching {from_symbol}/{to_symbol}: {e}")
        return []

def get_timeframe_candles(display_symbol: str, timeframe: str) -> List[dict]:
    """Get candles for a specific timeframe with caching"""
    
    # Parse symbol (e.g., "EUR/USD" -> from="EUR", to="USD")
    if "/" not in display_symbol:
        print(f"Invalid symbol format: {display_symbol}")
        return []
    
    parts = display_symbol.split("/")
    from_symbol = parts[0]
    to_symbol = parts[1]
    
    # Map timeframe to Alpha Vantage function
    function_map = {
        "daily": "FX_DAILY",
        "weekly": "FX_WEEKLY",
        "monthly": "FX_MONTHLY"
    }
    function = function_map.get(timeframe, "FX_DAILY")
    
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
    candles = get_candles_alphavantage(from_symbol, to_symbol, function)
    
    # Cache the result
    if candles:
        save_to_cache(cache_key, candles)
    
    return candles

def get_all_symbols() -> List[str]:
    """Get list of all tracked symbols"""
    return list(SYMBOL_MAP.keys())

# Initialize database on module load
init_db()
