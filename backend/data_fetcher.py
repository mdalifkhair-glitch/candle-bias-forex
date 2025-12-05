"""
Data Fetcher - Alpha Vantage API Integration
Free tier: 25 calls/day (free), 500/day with API key
Get free key at: https://www.alphavantage.co/support/#api-key
"""

import requests
from datetime import datetime
from typing import Dict, List
import json
import os
import time

# Alpha Vantage API
API_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "demo")
BASE_URL = "https://www.alphavantage.co/query"

# Symbol mapping for Alpha Vantage
# Forex format: from_currency, to_currency
SYMBOL_MAP = {
    # Major Forex Pairs
    "EUR/USD": ("EUR", "USD"),
    "GBP/USD": ("GBP", "USD"),
    "USD/JPY": ("USD", "JPY"),
    "USD/CHF": ("USD", "CHF"),
    "USD/CAD": ("USD", "CAD"),
    "AUD/USD": ("AUD", "USD"),
    "NZD/USD": ("NZD", "USD"),
    # Precious Metals
    "XAU/USD": ("XAU", "USD"),
    "XAU/JPY": ("XAU", "JPY"),
    "XAU/GBP": ("XAU", "GBP"),
    "XAG/USD": ("XAG", "USD"),
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


def get_forex_daily(from_currency: str, to_currency: str) -> List[dict]:
    """
    Fetch daily Forex data from Alpha Vantage
    """
    try:
        params = {
            "function": "FX_DAILY",
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "apikey": API_KEY,
            "outputsize": "compact",  # Last 100 data points
        }
        
        response = requests.get(BASE_URL, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            return []
        
        data = response.json()
        
        # Check for errors
        if "Error Message" in data:
            print(f"API Error: {data['Error Message']}")
            return []
        
        if "Note" in data:
            print(f"API Limit: {data['Note']}")
            return []
        
        time_series = data.get("Time Series FX (Daily)", {})
        if not time_series:
            print(f"No data for {from_currency}/{to_currency}")
            return []
        
        candles = []
        for date, values in sorted(time_series.items(), reverse=True)[:10]:
            candles.append({
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "date": date
            })
        
        return candles
        
    except Exception as e:
        print(f"Error: {e}")
        return []


def get_forex_weekly(from_currency: str, to_currency: str) -> List[dict]:
    """Fetch weekly Forex data"""
    try:
        params = {
            "function": "FX_WEEKLY",
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "apikey": API_KEY,
        }
        
        response = requests.get(BASE_URL, params=params, timeout=15)
        data = response.json()
        
        if "Error Message" in data or "Note" in data:
            return []
        
        time_series = data.get("Time Series FX (Weekly)", {})
        candles = []
        for date, values in sorted(time_series.items(), reverse=True)[:10]:
            candles.append({
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "date": date
            })
        return candles
    except:
        return []


def get_forex_monthly(from_currency: str, to_currency: str) -> List[dict]:
    """Fetch monthly Forex data"""
    try:
        params = {
            "function": "FX_MONTHLY",
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "apikey": API_KEY,
        }
        
        response = requests.get(BASE_URL, params=params, timeout=15)
        data = response.json()
        
        if "Error Message" in data or "Note" in data:
            return []
        
        time_series = data.get("Time Series FX (Monthly)", {})
        candles = []
        for date, values in sorted(time_series.items(), reverse=True)[:10]:
            candles.append({
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "date": date
            })
        return candles
    except:
        return []


def get_timeframe_candles(display_symbol: str, timeframe: str) -> List[dict]:
    """
    Get candles for a specific timeframe.
    """
    currencies = SYMBOL_MAP.get(display_symbol)
    if not currencies:
        return []
    
    from_curr, to_curr = currencies
    cache_key = f"{display_symbol}_{timeframe}"
    
    # Check cache
    now = datetime.now()
    if cache_key in _cache:
        cached = _cache[cache_key]
        try:
            cache_time = datetime.fromisoformat(cached.get("timestamp", "2000-01-01"))
            # Cache for 4 hours to save API calls
            if (now - cache_time).total_seconds() < 14400:
                return cached.get("candles", [])
        except:
            pass
    
    # Fetch based on timeframe
    if timeframe == "daily":
        candles = get_forex_daily(from_curr, to_curr)
    elif timeframe == "weekly":
        candles = get_forex_weekly(from_curr, to_curr)
    elif timeframe == "monthly":
        candles = get_forex_monthly(from_curr, to_curr)
    else:
        candles = []
    
    if candles:
        _cache[cache_key] = {
            "timestamp": now.isoformat(),
            "candles": candles
        }
        save_cache()
    
    # Rate limiting - Alpha Vantage allows 5 calls/minute on free tier
    time.sleep(12)  # 12 seconds between calls = 5 per minute
    
    return candles


def get_all_symbols() -> List[str]:
    """Return list of all tracked symbols"""
    return list(SYMBOL_MAP.keys())


# Load cache on module import
load_cache()
