import pandas as pd

# Load Data
df = pd.read_csv("debug_snippet.csv")

def parse_currency(x):
    if isinstance(x, str):
        x = x.replace(',', '')
        return float(x)
    return x

cols = ['Open', 'High', 'Low', 'Close']
for c in cols:
    df[c] = df[c].apply(parse_currency)

df = df.iloc[::-1].reset_index(drop=True)

print(f"{'Date':<15} | {'Prev':<6} | {'Level':<10} | {'Close':<10} | {'Diff':<8} | {'CSV Bias':<10} | {'Logic':<15}")
print("-" * 100)

for i in range(1, len(df)):
    c1 = df.iloc[i]     # Current Row (Target)
    c0 = df.iloc[i-1]   # Previous Row (Source of Signal)
    
    date = c1['Date']
    bullish = c1['Bullish Bias'] == 1.0
    bearish = c1['Bearish Bias'] == 1.0
    
    # Levels
    prev_high = c0['High']
    prev_low = c0['Low']
    curr_close = c0['Close'] # Signal comes from Prev Close
    
    # 1. Breakout Check
    # Bullish Breakout
    if curr_close > prev_high:
        logic_res = "Bull Break"
        match = bullish
    elif curr_close < prev_low:
        logic_res = "Bear Break"
        match = bearish
    else:
        # Rejection Logic?
        # Check Inside Bar
        if c0['High'] <= prev_high and c0['Low'] >= prev_low:
             logic_res = "Inside Bar"
             match = (not bullish and not bearish)
        else:
            # Fakeout?
            # Swept Low, Closed High?
            if c0['Low'] < prev_low and curr_close > prev_low:
                logic_res = "Bull Recover" 
                match = bullish
                diff = curr_close - prev_low
            # Swept High, Closed Low?
            elif c0['High'] > prev_high and curr_close < prev_high:
                logic_res = "Bear Reject"
                match = bearish
                diff = prev_high - curr_close
            else:
                logic_res = "Neutral"
                match = (not bullish and not bearish)
    
    # Special Debug for discrepancies
    if not match or date.startswith("Tue 09") or date.startswith("Mon 17"):
        print(f"{date:<15} | {c0['Date'][:6]:<6} | H:{prev_high:.0f} L:{prev_low:.0f} | C:{curr_close:.0f} | {'Match' if match else 'FAIL'} | {bullish}/{bearish} | {logic_res}")
        if not match:
             # Check tolerance
             if logic_res == "Bear Break" and bullish:
                  print(f"    -> Bear Break but CSV Bull. Close {curr_close} vs Low {prev_low}. Diff: {curr_close - prev_low}")
