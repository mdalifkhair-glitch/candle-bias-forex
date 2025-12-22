import pandas as pd
import numpy as np

def parse_currency(x):
    if isinstance(x, str):
        # Remove commas and handle negative signs if standard dash
        x = x.replace(',', '')
        return float(x)
    return x

# Load data
df = pd.read_csv(r"c:\Users\Administrator\Desktop\Candle Bias(Forex)\data_analysis.csv")

# Clean data
cols_to_fix = ['Open', 'High', 'Low', 'Close']
for col in cols_to_fix:
    df[col] = df[col].apply(parse_currency)

# Reverse data so it is chronological (oldest first)
df = df.iloc[::-1].reset_index(drop=True)

# Add Previous Day columns
df['PrevOpen'] = df['Open'].shift(1)
df['PrevHigh'] = df['High'].shift(1)
df['PrevLow'] = df['Low'].shift(1)
df['PrevClose'] = df['Close'].shift(1)
df['Prev2High'] = df['High'].shift(2)
df['Prev2Low'] = df['Low'].shift(2)

# Analyze Bullish Bias Logic
# Hypothesis: Bias for Day T is determined by action on Day T-1 (and maybe T-2)
# So we look at row T, and compare its Bias with features from T-1.
# Remember 'PrevHigh' in row T corresponds to High of T-1.

print("Analyzing Bullish Bias == 1")
bullish_days = df[df['Bullish Bias'] == 1]
for idx, row in bullish_days.iterrows():
    # We want to see what happened on the PREVIOUS day (or days) that caused this bias.
    # Since we are predicting Bias for Day T, the input must be available at start of Day T.
    # The input is Day T-1 data.
    
    # Check if PrevClose broke Prev2High
    # i.e., Close(T-1) > High(T-2)
    # In our dataframe, Close(T-1) is row['PrevClose'], High(T-2) is row['Prev2High']
    
    broken_high = row['PrevClose'] > row['Prev2High'] if not np.isnan(row['Prev2High']) else False
    prev_green = row['PrevClose'] > row['PrevOpen']
    
    print(f"Date: {row['Date']}, PrevClose > Prev2High: {broken_high}, PrevGreen: {prev_green}, PrevClose: {row['PrevClose']}, Prev2High: {row['Prev2High']}")

print("\nAnalyzing Bearish Bias == 1")
bearish_days = df[df['Bearish Bias'] == 1]
for idx, row in bearish_days.iterrows():
    broken_low = row['PrevClose'] < row['Prev2Low'] if not np.isnan(row['Prev2Low']) else False
    prev_red = row['PrevClose'] < row['PrevOpen']
    
    print(f"Date: {row['Date']}, PrevClose < Prev2Low: {broken_low}, PrevRed: {prev_red}, PrevClose: {row['PrevClose']}, Prev2Low: {row['Prev2Low']}")

# Let's count accuracy of rules
df['Rule_Bullish'] = (df['PrevClose'] > df['Prev2High'])
df['Rule_Bearish'] = (df['PrevClose'] < df['Prev2Low'])

# Check matches
# We only check rows where Prev2 exists (index >= 2)
valid_df = df.iloc[2:]

bullish_match = (valid_df['Rule_Bullish'] == (valid_df['Bullish Bias'] == 1))
bearish_match = (valid_df['Rule_Bearish'] == (valid_df['Bearish Bias'] == 1))

print(f"\nBullish Rule Fit: {bullish_match.mean()}")
print(f"Bearish Rule Fit: {bearish_match.mean()}")

# Inspect mismatches
print("\nBullish Mismatches:")
print(valid_df[valid_df['Rule_Bullish'] != (valid_df['Bullish Bias'] == 1)][['Date', 'PrevClose', 'Prev2High', 'Bullish Bias', 'Rule_Bullish']])

print("\nBearish Mismatches:")
print(valid_df[valid_df['Rule_Bearish'] != (valid_df['Bearish Bias'] == 1)][['Date', 'PrevClose', 'Prev2Low', 'Bearish Bias', 'Rule_Bearish']])
