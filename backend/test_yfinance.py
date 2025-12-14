import data_fetcher
import json

def test_fetch():
    print("Testing yfinance fetch...")
    
    symbol = "EUR/USD"
    
    for tf in ["daily", "weekly", "monthly"]:
        print(f"\nFetching {symbol} - {tf}...")
        candles = data_fetcher.get_timeframe_candles(symbol, tf)
        
        if candles:
            print(f"Success! Got {len(candles)} candles.")
            print("First candle (Latest):")
            print(json.dumps(candles[0], indent=2))
        else:
            print("FAILED: No data returned.")

if __name__ == "__main__":
    test_fetch()
