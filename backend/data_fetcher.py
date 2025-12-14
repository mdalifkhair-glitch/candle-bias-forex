"""
Data Fetcher - yfinance Integration
Uses Yahoo Finance data (free, no key required)
"""

import yfinance as yf
from datetime import datetime
from typing import List, Dict
import pandas as pd

# Symbol mapping: Your format -> Yahoo Finance format
SYMBOL_MAP = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "USD/CAD": "USDCAD=X",
    "AUD/USD": "AUDUSD=X",
    "NZD/USD": "NZDUSD=X",
    "XAU/USD": "GC=F",      # Gold Futures (closest proxy on Yahoo for free)
    "BTC/USD": "BTC-USD",   # Bitcoin
    "ETH/USD": "ETH-USD",   # Ethereum
}

def get_all_symbols() -> List[str]:
    """Get list of all tracked symbols"""
    return list(SYMBOL_MAP.keys())

def get_timeframe_candles(display_symbol: str, timeframe: str) -> List[dict]:
    """
    Get candles for a specific timeframe using yfinance
    """
    
    # Get Yahoo ticker
    yahoo_symbol = SYMBOL_MAP.get(display_symbol)
    if not yahoo_symbol:
        print(f"Unknown symbol: {display_symbol}")
        # Try a direct mapping guess if not in map (e.g. trying to pass a yahoo ticker directly)
        if "=" in display_symbol or "-" in display_symbol:
             yahoo_symbol = display_symbol
        else:
             return []

    # Map timeframe to yfinance interval and period
    # period needs to be long enough to get at least a few closed candles
    tf_map = {
        "daily":   {"interval": "1d", "period": "1mo"},
        "weekly":  {"interval": "1wk", "period": "3mo"},
        "monthly": {"interval": "1mo", "period": "1y"}, 
    }
    
    config = tf_map.get(timeframe)
    if not config:
        print(f"Invalid timeframe: {timeframe}")
        return []

    try:
        # Fetch data
        ticker = yf.Ticker(yahoo_symbol)
        df = ticker.history(period=config["period"], interval=config["interval"])
        
        if df.empty:
            print(f"No data found for {display_symbol} ({yahoo_symbol})")
            return []

        # LOGGING: Print the latest candle for debugging
        latest = df.iloc[0]
        print(f"[{display_symbol} {timeframe}] Date: {latest.name}, Close: {latest['Close']}")

        # Sort descending (newest first)
        df = df.sort_index(ascending=False)
        
        # Convert to our dictionary format
        candles = []
        for index, row in df.iterrows():
            # index is Timestamp
            date_str = index.strftime("%Y-%m-%d")
            
            candles.append({
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "date": date_str
            })
            
            # We only need the last few candles for bias calculation
            if len(candles) >= 5:
                break
                
        return candles

    except Exception as e:
        print(f"Error fetching {display_symbol} with yfinance: {e}")
        return []
