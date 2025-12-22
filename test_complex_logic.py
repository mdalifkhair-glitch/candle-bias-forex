import pandas as pd
import numpy as np

# Load Data
df = pd.read_csv("data_analysis.csv")

def parse_currency(x):
    if isinstance(x, str):
        x = x.replace(',', '')
        return float(x)
    return x

cols = ['Open', 'High', 'Low', 'Close']
for c in cols:
    df[c] = df[c].apply(parse_currency)

# Chronological order
df = df.iloc[::-1].reset_index(drop=True)

# Proposed Logic: Breakout + Rejection
def calculate_complex_bias(c1, c2):
    # C1 is "Current Day" (The day we are analyzing to set the bias label)
    # Actually, in the CSV, the label "Bullish Bias" on Row T seems to be derived from the candle of Row T itself?
    # Or is it derived from T-1 to predict T?
    # Let's look at the "Simple Version" user sent: "if close > previous_high".
    # This implies we look at the COMPLETED candle and assign a bias.
    # So for Date T, we look at Close(T) vs High(T-1).
    # BUT, wait. In the CSV, on "Tue 09 Dec", the bias is 1.0.
    # My previous analysis showed Tue 09 Dec had a Rejection against Mon 08.
    # So we are looking at Row T (Current) vs Row T-1 (Previous) to generate the Label for Row T.
    
    # c1 = Current Row (T)
    # c2 = Previous Row (T-1)
    
    c1_close = c1['Close']
    c1_high = c1['High']
    c1_low = c1['Low']
    
    c2_high = c2['High']
    c2_low = c2['Low']
    
    # 1. Bullish Breakout
    if c1_close > c2_high:
        return 1, 0  # Bull, Bear
        
    # 2. Bearish Breakout
    if c1_close < c2_low:
        return 0, 1
        
    # 3. Bullish Rejection (Liquidity Grab)
    # Price went below prev low, but closed above it
    if c1_low < c2_low and c1_close > c2_low:
        return 1, 0
        
    # 4. Bearish Rejection (Liquidity Grab)
    # Price went above prev high, but closed below it
    if c1_high > c2_high and c1_close < c2_high:
        return 0, 1
        
    return 0, 0

results = []
for i in range(1, len(df)):
    c1 = df.iloc[i]     # Current
    c2 = df.iloc[i-1]   # Previous
    
    calc_bull, calc_bear = calculate_complex_bias(c1, c2)
    
    # Check match with CSV
    csv_bull = c1['Bullish Bias']
    csv_bear = c1['Bearish Bias']
    
    match = (calc_bull == csv_bull) and (calc_bear == csv_bear)
    results.append({
        'Date': c1['Date'],
        'Match': match,
        'Calc': (calc_bull, calc_bear),
        'CSV': (csv_bull, csv_bear)
    })

results_df = pd.DataFrame(results)
print(f"Total Rows: {len(results_df)}")
print(f"Matches: {results_df['Match'].sum()}")
print(f"Accuracy: {results_df['Match'].mean():.2%}")

print("\nRemaining Mismatches:")
print(results_df[~results_df['Match']])
