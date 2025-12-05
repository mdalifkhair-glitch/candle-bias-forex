"""
Data Fetcher - Yahoo Finance Integration
Fetches OHLC data for Forex pairs and precious metals
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

# Yahoo Finance symbol mapping
# Forex pairs use format: EURUSD=X
# Precious metals: GC=F (Gold futures), SI=F (Silver futures)
SYMBOL_MAP = {
    # Major Forex Pairs
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "USD/CAD": "USDCAD=X",
    "AUD/USD": "AUDUSD=X",
    "NZD/USD": "NZDUSD=X",
    # Precious Metals
    "XAU/USD": "GC=F",      # Gold Futures (USD)
    "XAU/JPY": "XAUJPY=X",  # Gold/JPY - may need alternative
    "XAU/GBP": "XAUGBP=X",  # Gold/GBP - may need alternative
    "XAG/USD": "SI=F",      # Silver Futures (USD)
}

# Cache storage
_cache: Dict[str, dict] = {}
_cache_file = "data_cache.json"


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


def get_candles(symbol: str, period: str = "1mo", interval: str = "1d") -> List[dict]:
    """
    Fetch OHLC candle data from Yahoo Finance.
    
    Args:
        symbol: Yahoo Finance symbol (e.g., "EURUSD=X")
        period: Data period (1mo, 3mo, 6mo, 1y, etc.)
        interval: Candle interval (1d for daily, 1wk for weekly, 1mo for monthly)
    
    Returns:
        List of candle dictionaries with open, high, low, close
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            return []
        
        candles = []
        for idx in range(len(df) - 1, -1, -1):  # Most recent first
            row = df.iloc[idx]
            candles.append({
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "date": str(df.index[idx].date())
            })
        
        return candles
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []


def get_timeframe_candles(display_symbol: str, timeframe: str) -> List[dict]:
    """
    Get candles for a specific timeframe.
    
    Args:
        display_symbol: Display symbol (e.g., "EUR/USD")
        timeframe: "daily", "weekly", or "monthly"
    
    Returns:
        List of candles (most recent first)
    """
    yf_symbol = SYMBOL_MAP.get(display_symbol)
    if not yf_symbol:
        return []
    
    # Map timeframe to Yahoo Finance interval
    interval_map = {
        "daily": ("3mo", "1d"),    # 3 months of daily data
        "weekly": ("1y", "1wk"),   # 1 year of weekly data
        "monthly": ("2y", "1mo"),  # 2 years of monthly data
    }
    
    period, interval = interval_map.get(timeframe, ("3mo", "1d"))
    
    cache_key = f"{yf_symbol}_{timeframe}"
    
    # Check cache (simple time-based)
    if cache_key in _cache:
        cached = _cache[cache_key]
        cache_time = datetime.fromisoformat(cached.get("timestamp", "2000-01-01"))
        now = datetime.now()
        
        # Cache validity based on timeframe
        if timeframe == "daily" and (now - cache_time).total_seconds() < 3600:  # 1 hour
            return cached.get("candles", [])
        elif timeframe == "weekly" and (now - cache_time).total_seconds() < 86400:  # 1 day
            return cached.get("candles", [])
        elif timeframe == "monthly" and (now - cache_time).total_seconds() < 86400 * 7:  # 1 week
            return cached.get("candles", [])
    
    # Fetch fresh data
    candles = get_candles(yf_symbol, period, interval)
    
    if candles:
        _cache[cache_key] = {
            "timestamp": datetime.now().isoformat(),
            "candles": candles
        }
        save_cache()
    
    return candles


def get_all_symbols() -> List[str]:
    """Return list of all tracked symbols"""
    return list(SYMBOL_MAP.keys())


# Load cache on module import
load_cache()
