"""
Data Fetcher - Twelve Data API Integration
Free tier: 800 API credits/day (enough for this app)
"""

import requests
from datetime import datetime
from typing import Dict, List
import json
import os
import time

# Twelve Data API (Free tier - 800 credits/day)
# Get your free API key at: https://twelvedata.com/
API_KEY = os.getenv("TWELVEDATA_API_KEY", "demo")  # demo key has limited access
BASE_URL = "https://api.twelvedata.com"

# Symbol mapping for Twelve Data
SYMBOL_MAP = {
    # Major Forex Pairs
    "EUR/USD": "EUR/USD",
    "GBP/USD": "GBP/USD",
    "USD/JPY": "USD/JPY",
    "USD/CHF": "USD/CHF",
    "USD/CAD": "USD/CAD",
    "AUD/USD": "AUD/USD",
    "NZD/USD": "NZD/USD",
    # Precious Metals
    "XAU/USD": "XAU/USD",
    "XAU/JPY": "XAU/JPY",
    "XAU/GBP": "XAU/GBP",
    "XAG/USD": "XAG/USD",
}

# Cache storage
_cache: Dict[str, dict] = {}
_cache_file = "/tmp/data_cache.json"


def load_cache():
    """Load cache from file if exists"""
    global _cache
    try:
        if os.path.exists(_cache_file):
            with open(_cache_file, 'r') as f:
                _cache = json.load(f)
    except:
        _cache = {}


def save_cache():
    """Save cache to file"""
    try:
        with open(_cache_file, 'w') as f:
            json.dump(_cache, f)
    except:
        pass


def get_candles_twelvedata(symbol: str, interval: str = "1day", outputsize: int = 5) -> List[dict]:
    """
    Fetch OHLC data from Twelve Data API
    """
    try:
        url = f"{BASE_URL}/time_series"
        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": API_KEY,
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"Error fetching {symbol}: HTTP {response.status_code}")
            return []
        
        data = response.json()
        
        # Check for errors
        if data.get("status") == "error":
            print(f"API Error for {symbol}: {data.get('message', 'Unknown error')}")
            return []
        
        values = data.get("values", [])
        if not values:
            print(f"No data for {symbol}")
            return []
        
        candles = []
        for item in values:
            candles.append({
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
                "date": item["datetime"].split()[0] if " " in item["datetime"] else item["datetime"]
            })
        
        return candles  # Already sorted most recent first
        
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []


def get_timeframe_candles(display_symbol: str, timeframe: str) -> List[dict]:
    """
    Get candles for a specific timeframe.
    """
    td_symbol = SYMBOL_MAP.get(display_symbol)
    if not td_symbol:
        return []
    
    # Map timeframe to Twelve Data intervals
    interval_map = {
        "daily": "1day",
        "weekly": "1week",
        "monthly": "1month",
    }
    
    interval = interval_map.get(timeframe, "1day")
    cache_key = f"{td_symbol}_{timeframe}"
    
    # Check cache
    now = datetime.now()
    if cache_key in _cache:
        cached = _cache[cache_key]
        try:
            cache_time = datetime.fromisoformat(cached.get("timestamp", "2000-01-01"))
            max_age = 3600 if timeframe == "daily" else 86400 * 7
            if (now - cache_time).total_seconds() < max_age:
                return cached.get("candles", [])
        except:
            pass
    
    # Fetch fresh data
    candles = get_candles_twelvedata(td_symbol, interval, 5)
    
    if candles:
        _cache[cache_key] = {
            "timestamp": now.isoformat(),
            "candles": candles
        }
        save_cache()
    
    # Rate limiting - be nice to the API
    time.sleep(0.5)
    
    return candles


def get_all_symbols() -> List[str]:
    """Return list of all tracked symbols"""
    return list(SYMBOL_MAP.keys())


# Load cache on module import
load_cache()
