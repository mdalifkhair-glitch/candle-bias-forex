import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import data_fetcher
from bias_calculator import calculate_trade_signal, get_bias_from_candles

def test_signals():
    symbols = ["AUD/USD", "EUR/USD", "GBP/USD", "NZD/USD"]
    
    print(f"{'SYMBOL':<10} {'MN':<12} {'W1':<12} {'D1':<12} {'SIGNAL'}")
    print("-" * 60)
    
    for symbol in symbols:
        try:
            # We need to fetch candles for each timeframe
            biases = {}
            for tf in ["daily", "weekly", "monthly"]:
                candles = data_fetcher.get_timeframe_candles(symbol, tf)
                if candles and len(candles) >= 2:
                    biases[tf] = get_bias_from_candles(candles)
                else:
                    biases[tf] = "NEUTRAL"
            
            mn = biases.get("monthly", "NEUTRAL")
            w1 = biases.get("weekly", "NEUTRAL")
            d1 = biases.get("daily", "NEUTRAL")
            
            signal = calculate_trade_signal(d1, w1, mn)
            
            print(f"{symbol:<10} {mn:<12} {w1:<12} {d1:<12} {signal}")
            
        except Exception as e:
            print(f"Error for {symbol}: {e}")

if __name__ == "__main__":
    test_signals()
