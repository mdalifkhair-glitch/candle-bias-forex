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
    # Forex Pairs (7)
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "USD/CAD": "USDCAD=X",
    "AUD/USD": "AUDUSD=X",
    "NZD/USD": "NZDUSD=X",
    
    # Precious Metals (4)
    "XAU/USD": "GC=F",                    # Gold Futures
    "XAU/JPY": "CROSS:GC=F*USDJPY=X",     # Gold/Yen (calculated)
    "XAU/GBP": "CROSS:GC=F/GBPUSD=X",     # Gold/Pound (calculated)
    "XAG/USD": "SI=F",                    # Silver Futures
}

def get_all_symbols() -> List[str]:
    """Get list of all tracked symbols"""
    return list(SYMBOL_MAP.keys())

def fetch_direct_candles(yahoo_symbol: str, timeframe: str) -> List[dict]:
    """
    Fetch candles directly from Yahoo Finance for a single symbol
    """
    # Map timeframe to yfinance interval and period
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
            print(f"No data found for {yahoo_symbol}")
            return []

        # Sort descending (newest first)
        df = df.sort_index(ascending=False)
        
        # Convert to our dictionary format
        candles = []
        for index, row in df.iterrows():
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
        print(f"Error fetching {yahoo_symbol}: {e}")
        return []

def calculate_cross_rate(formula: str, timeframe: str) -> List[dict]:
    """
    Calculate synthetic cross-rate candles from two component pairs
    Formula format: "BASE*QUOTE" or "BASE/QUOTE"
    Example: "GC=F*USDJPY=X" or "GC=F/GBPUSD=X"
    """
    try:
        # Parse formula
        if "*" in formula:
            base_symbol, quote_symbol = formula.split("*")
            operation = "multiply"
        elif "/" in formula:
            base_symbol, quote_symbol = formula.split("/")
            operation = "divide"
        else:
            print(f"Invalid cross-rate formula: {formula}")
            return []
        
        # Fetch both component pairs
        base_candles = fetch_direct_candles(base_symbol, timeframe)
        quote_candles = fetch_direct_candles(quote_symbol, timeframe)
        
        if not base_candles or not quote_candles:
            print(f"Failed to fetch data for cross-rate: {formula}")
            return []
        
        # Calculate synthetic candles
        synthetic_candles = []
        min_length = min(len(base_candles), len(quote_candles))
        
        for i in range(min_length):
            base = base_candles[i]
            quote = quote_candles[i]
            
            if operation == "multiply":
                synthetic = {
                    "open": base["open"] * quote["open"],
                    "high": base["high"] * quote["high"],
                    "low": base["low"] * quote["low"],
                    "close": base["close"] * quote["close"],
                    "date": base["date"]
                }
            else:  # divide
                synthetic = {
                    "open": base["open"] / quote["open"],
                    "high": base["high"] / quote["high"],
                    "low": base["low"] / quote["low"],
                    "close": base["close"] / quote["close"],
                    "date": base["date"]
                }
            
            synthetic_candles.append(synthetic)
        
        return synthetic_candles
    
    except Exception as e:
        print(f"Error calculating cross-rate {formula}: {e}")
        return []

def get_timeframe_candles(display_symbol: str, timeframe: str) -> List[dict]:
    """
    Get candles for a specific timeframe using yfinance
    Supports both direct symbols and cross-rate calculations
    """
    
    # Get Yahoo ticker or cross-rate formula
    yahoo_symbol = SYMBOL_MAP.get(display_symbol)
    if not yahoo_symbol:
        print(f"Unknown symbol: {display_symbol}")
        return []
    
    # Check if this is a cross-rate calculation
    if yahoo_symbol.startswith("CROSS:"):
        formula = yahoo_symbol.replace("CROSS:", "")
        print(f"[{display_symbol} {timeframe}] Calculating cross-rate: {formula}")
        return calculate_cross_rate(formula, timeframe)
    
    # Direct fetch for regular symbols
    candles = fetch_direct_candles(yahoo_symbol, timeframe)
    
    if candles:
        latest = candles[0]
        print(f"[{display_symbol} {timeframe}] Date: {latest['date']}, Close: {latest['close']:.2f}")
    
    return candles
