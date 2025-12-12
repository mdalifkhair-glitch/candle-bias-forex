"""
Candle Bias Forex - FastAPI Backend
Main server for bias calculation API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, List
import os
import data_fetcher
from bias_calculator import get_bias_from_candles

app = FastAPI(
    title="Candle Bias Forex API",
    description="Multi-timeframe trend bias indicator for Forex pairs",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
async def root():
    """Serve the frontend dashboard"""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Candle Bias Forex API", "status": "running"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/test")
async def test_endpoint():
    """Test endpoint with mock data to verify frontend works"""
    return {
        "data": [
            {"symbol": "EUR/USD", "daily": "BULL", "weekly": "STRONG BULL", "monthly": "NEUTRAL"},
            {"symbol": "GBP/USD", "daily": "BEAR", "weekly": "NEUTRAL", "monthly": "BULL"},
            {"symbol": "USD/JPY", "daily": "NEUTRAL", "weekly": "BEAR", "monthly": "STRONG BEAR"},
        ],
        "count": 3
    }


@app.get("/api/symbols")
async def get_symbols():
    """Get list of all tracked symbols"""
    return {"symbols": data_fetcher.get_all_symbols()}


@app.get("/api/bias/{symbol}")
async def get_symbol_bias(symbol: str):
    """
    Get bias for a specific symbol across all timeframes.
    Symbol format: EUR/USD, XAU/USD, etc.
    """
    symbol = symbol.upper().replace("-", "/")
    
    result = {
        "symbol": symbol,
        "daily": {"bias": "NEUTRAL", "candles": []},
        "weekly": {"bias": "NEUTRAL", "candles": []},
        "monthly": {"bias": "NEUTRAL", "candles": []},
    }
    
    for timeframe in ["daily", "weekly", "monthly"]:
        candles = data_fetcher.get_timeframe_candles(symbol, timeframe)
        if candles and len(candles) >= 2:
            bias = get_bias_from_candles(candles)
            result[timeframe] = {
                "bias": bias,
                "candles": candles[:2]  # Return last 2 candles for reference
            }
    
    return result


@app.get("/api/bias")
async def get_all_bias():
    """
    Get bias for all symbols across all timeframes.
    Returns a list of bias data for the dashboard.
    """
    symbols = data_fetcher.get_all_symbols()
    results = []
    
    for symbol in symbols:
        bias_data = {
            "symbol": symbol,
            "daily": "NEUTRAL",
            "weekly": "NEUTRAL",
            "monthly": "NEUTRAL",
        }
        
        # Try to fetch data, but don't block if it fails
        for timeframe in ["daily", "weekly", "monthly"]:
            try:
                candles = data_fetcher.get_timeframe_candles(symbol, timeframe)
                if candles and len(candles) >= 2:
                    bias_data[timeframe] = get_bias_from_candles(candles)
            except Exception as e:
                print(f"Error fetching {symbol} {timeframe}: {e}")
                # Keep NEUTRAL as default
        
        results.append(bias_data)
    
    return {"data": results, "count": len(results)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
