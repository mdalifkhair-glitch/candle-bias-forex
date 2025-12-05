"""
Data Fetcher - Twelve Data API Integration
Free tier: 800 API credits/day
Get free key at: https://twelvedata.com/
"""

import requests
from datetime import datetime
from typing import Dict, List
import json
import os
import time

# Twelve Data API
BASE_URL = "https://api.twelvedata.com"

def get_api_key():
    """Get API key from environment - called at runtime"""
    key = os.environ.get("TWELVEDATA_API_KEY", "demo")
    print(f"Using API key: {key[:8]}..." if len(key) > 8 else f"Using API key: {key}")
    return key

# Symbol mapping
SYMBOL_MAP = {
    "EUR/USD": "EUR/USD",
    "GBP/USD": "GBP/USD",
    "USD/JPY": "USD/JPY",
    "USD/CHF": "USD/CHF",
    "USD/CAD": "USD/CAD",
    "AUD/USD": "AUD/USD",
    "NZD/USD": "NZD/USD",
    "XAU/USD": "XAU/USD",
    "XAU/JPY": "XAU/JPY",
    "XAU/GBP": "XAU/GBP",
    "XAG/USD": "XAG/USD",
}

_cache: Dict[str, dict] = {}
_cache_file = "/tmp/data_cache.json"


def load_cache():
    global _cache
    try:
        if os.path.exists(_cache_file):
            with open(_cache_file, 'r') as f:
                _cache = json.load(f)
    except:
        _cache = {}


def save_cache():
    try:
        with open(_cache_file, 'w') as f:
            json.dump(_cache, f)
    except:
        pass


def get_candles(symbol: str, interval: str = "1day", outputsize: int = 5) -> List[dict]:
    """Fetch OHLC data from Twelve Data"""
    try:
        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": get_api_key(),
        }
        
        response = requests.get(f"{BASE_URL}/time_series", params=params, timeout=15)
        data = response.json()
        
        if data.get("status") == "error":
            print(f"Error for {symbol}: {data.get('message')}")
            return []
        
        values = data.get("values", [])
        candles = []
        for item in values:
            candles.append({
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
                "date": item["datetime"].split()[0]
            })
        return candles
        
    except Exception as e:
        print(f"Error: {e}")
        return []


def get_timeframe_candles(display_symbol: str, timeframe: str) -> List[dict]:
    td_symbol = SYMBOL_MAP.get(display_symbol)
    if not td_symbol:
        return []
    
    interval_map = {"daily": "1day", "weekly": "1week", "monthly": "1month"}
    interval = interval_map.get(timeframe, "1day")
    cache_key = f"{td_symbol}_{timeframe}"
    
    # Check cache (4 hour validity)
    now = datetime.now()
    if cache_key in _cache:
        cached = _cache[cache_key]
        try:
            cache_time = datetime.fromisoformat(cached.get("timestamp", "2000-01-01"))
            if (now - cache_time).total_seconds() < 14400:
                return cached.get("candles", [])
        except:
            pass
    
    candles = get_candles(td_symbol, interval, 5)
    
    if candles:
        _cache[cache_key] = {"timestamp": now.isoformat(), "candles": candles}
        save_cache()
    
    time.sleep(0.5)
    return candles


def get_all_symbols() -> List[str]:
    return list(SYMBOL_MAP.keys())


load_cache()
