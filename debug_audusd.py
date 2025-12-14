import yfinance as yf
from datetime import datetime

# Logic from bias_calculator.py
def explain_bias(c1, c2):
    print("\n--- Bias Logic Trace ---")
    print(f"C1 (Latest Closed): Close={c1['close']}, High={c1['high']}, Low={c1['low']}")
    print(f"C2 (Previous):      Close={c2['close']}, High={c2['high']}, Low={c2['low']}")
    
    # 1. STRONG BULL
    if c1['close'] > c2['high']:
        return "STRONG BULL (C1.Close > C2.High)"
    print(f"Not STRONG BULL: {c1['close']} is not > {c2['high']}")
    
    # 2. STRONG BEAR
    if c1['close'] < c2['low']:
        return "STRONG BEAR (C1.Close < C2.Low)"
    print(f"Not STRONG BEAR: {c1['close']} is not < {c2['low']}")
    
    # 3. BEAR
    if c1['high'] > c2['high'] and c1['close'] < c2['high']:
        return "BEAR (Rejection from High)"
    
    # 4. BULL
    if c1['low'] < c2['low'] and c1['close'] > c2['low']:
        return "BULL (Rejection from Low)"
    
    # 5. NEUTRAL
    if c1['high'] <= c2['high'] and c1['low'] >= c2['low']:
        return "NEUTRAL (Inside Bar)"
    
    return "NEUTRAL (No clear break)"

def debug_audusd():
    print("Fetching AUDUSD=X daily data...")
    ticker = yf.Ticker("AUDUSD=X")
    df = ticker.history(period="1mo", interval="1d")
    
    if df.empty:
        print("Error: No data fetched.")
        return

    # Sort descending
    df = df.sort_index(ascending=False)
    
    # Convert to dicts
    candles = []
    for index, row in df.iterrows():
        candles.append({
            "close": round(float(row["Close"]), 5),
            "high": round(float(row["High"]), 5),
            "low": round(float(row["Low"]), 5),
            "date": index.strftime("%Y-%m-%d")
        })
    
    # C0 is today (open), C1 is yesterday (closed), C2 is day before
    if len(candles) < 3:
        print("Not enough candles.")
        return

    c1 = candles[1] # Yesterday (Last Closed)
    c2 = candles[2] # Day before
    
    print(f"\nComparing Date: {c1['date']} vs {c2['date']}")
    result = explain_bias(c1, c2)
    print(f"\nRESULT: {result}")

if __name__ == "__main__":
    debug_audusd()
