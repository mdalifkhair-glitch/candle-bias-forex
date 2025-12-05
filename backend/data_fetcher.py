"""
Data Fetcher - Yahoo Finance Integration (Fixed for Cloud)
Fetches OHLC data for Forex pairs and precious metals
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
import time

# Custom headers to avoid Yahoo Finance blocking
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Yahoo Finance symbol mapping
SYMBOL_MAP = {
    # Major Forex Pairs
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "USD/CAD": "USDCAD=X",
    "AUD/USD": "AUDUSD=X",
    "NZD/USD": "NZDUSD=X",
    # Precious Metals - using correct Yahoo symbols
    "XAU/USD": "XAUUSD=X",
    "XAU/JPY": "XAUJPY=X",
    "XAU/GBP": "XAUGBP=X",
    "XAG/USD": "XAGUSD=X",
}

# Cache storage
_cache: Dict[str, dict] = {}
_cache_file = "/tmp/data_cache.json"  # Use /tmp for Render


def load_cache():
    """Load cache from file if exists"""
    global _cache
    if os.path.exists(_cache_file):
        try:
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


def get_candles_direct(symbol: str, interval: str = "1d", range_period: str = "3mo") -> List[dict]:
    """
    Fetch OHLC data directly from Yahoo Finance API (bypassing yfinance library)
    """
    try:
        # Yahoo Finance v8 API endpoint
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        
        params = {
            "interval": interval,
            "range": range_period,
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"Error fetching {symbol}: HTTP {response.status_code}")
            return []
        
        data = response.json()
        
        # Parse response
        result = data.get("chart", {}).get("result", [])
        if not result:
            print(f"No data for {symbol}")
            return []
        
        chart_data = result[0]
        timestamps = chart_data.get("timestamp", [])
        quote = chart_data.get("indicators", {}).get("quote", [{}])[0]
        
        opens = quote.get("open", [])
        highs = quote.get("high", [])
        lows = quote.get("low", [])
        closes = quote.get("close", [])
        
        if not timestamps or not closes:
            return []
        
        candles = []
        # Build candles from most recent to oldest
        for i in range(len(timestamps) - 1, -1, -1):
            if opens[i] is None or highs[i] is None or lows[i] is None or closes[i] is None:
                continue
                
            candles.append({
                "open": float(opens[i]),
                "high": float(highs[i]),
                "low": float(lows[i]),
                "close": float(closes[i]),
                "date": datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d")
            })
        
        return candles
        
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []


def get_timeframe_candles(display_symbol: str, timeframe: str) -> List[dict]:
    """
    Get candles for a specific timeframe.
    """
    yf_symbol = SYMBOL_MAP.get(display_symbol)
    if not yf_symbol:
        return []
    
    # Map timeframe to Yahoo Finance parameters
    interval_map = {
        "daily": ("1d", "3mo"),
        "weekly": ("1wk", "1y"),
        "monthly": ("1mo", "2y"),
    }
    
    interval, range_period = interval_map.get(timeframe, ("1d", "3mo"))
    cache_key = f"{yf_symbol}_{timeframe}"
    
    # Check cache
    if cache_key in _cache:
        cached = _cache[cache_key]
        cache_time = datetime.fromisoformat(cached.get("timestamp", "2000-01-01"))
        now = datetime.now()
        
        # Cache validity
        max_age = 3600 if timeframe == "daily" else 86400  # 1 hour for daily, 1 day for others
        if (now - cache_time).total_seconds() < max_age:
            return cached.get("candles", [])
    
    # Fetch fresh data
    candles = get_candles_direct(yf_symbol, interval, range_period)
    
    if candles:
        _cache[cache_key] = {
            "timestamp": datetime.now().isoformat(),
            "candles": candles
        }
        save_cache()
    
    # Small delay to avoid rate limiting
    time.sleep(0.3)
    
    return candles


def get_all_symbols() -> List[str]:
    """Return list of all tracked symbols"""
    return list(SYMBOL_MAP.keys())


# Load cache on module import
load_cache()
