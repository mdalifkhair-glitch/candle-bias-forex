import pandas as pd
import numpy as np

# Logic from bias_calculator.py
def calculate_bias(c1, c2):
    c1_close = c1['Close']
    c1_high = c1['High']
    c1_low = c1['Low']
    
    c2_close = c2['Close']
    c2_high = c2['High']
    c2_low = c2['Low']
    
    # 1. STRONG BULL: C1.Close > C2.High
    if c1_close > c2_high:
        return "STRONG BULL"
    
    # 2. STRONG BEAR: C1.Close < C2.Low
    if c1_close < c2_low:
        return "STRONG BEAR"
    
    # 3. BEAR: C1.High > C2.High AND C1.Close < C2.High
    if c1_high > c2_high and c1_close < c2_high:
        return "BEAR"
    
    # 4. BULL: C1.Low < C2.Low AND C1.Close > C2.Low
    if c1_low < c2_low and c1_close > c2_low:
        return "BULL"
    
    # 5. NEUTRAL
    if c1_high <= c2_high and c1_low >= c2_low:
        return "NEUTRAL"
    
    return "NEUTRAL"

# Load data
df = pd.read_csv("data_analysis.csv")

def parse_currency(x):
    if isinstance(x, str):
        x = x.replace(',', '')
        return float(x)
    return x

cols = ['Open', 'High', 'Low', 'Close']
for c in cols:
    df[c] = df[c].apply(parse_currency)

# Sort chronological
df = df.iloc[::-1].reset_index(drop=True)

# Calculate Predicted Bias
# Row T Bias is calculated using T-1 (C1) and T-2 (C2)
# So we iterate and for index i, we use i-1 and i-2.
predicts = []
for i in range(len(df)):
    if i < 2:
        predicts.append("N/A")
        continue
    
    c1 = df.iloc[i-1]
    c2 = df.iloc[i-2]
    
    bias_text = calculate_bias(c1, c2)
    predicts.append(bias_text)

df['Calculated_Bias'] = predicts

# Compare with Actual Columns
# We assume the row "Bullish Bias" corresponds to the prediction valid FOR that date, 
# which is calculated from PREVIOUS dates.
# Let's print the comparison
comparison = df[['Date', 'Bullish Bias', 'Bearish Bias', 'Calculated_Bias']].tail(40) # tail because we reversed it

print(comparison)

# Check matches
matches = 0
total = 0
for idx, row in comparison.iterrows():
    if row['Calculated_Bias'] == "N/A": continue
    
    calc = row['Calculated_Bias']
    bull = row['Bullish Bias']
    bear = row['Bearish Bias']
    
    # Mapping Hypothesis
    pred_bull = 1 if calc in ["STRONG BULL"] else 0
    pred_bear = 1 if calc in ["STRONG BEAR"] else 0
    
    # Try including Rejections
    # pred_bull = 1 if calc in ["STRONG BULL", "BULL"] else 0
    # pred_bear = 1 if calc in ["STRONG BEAR", "BEAR"] else 0
    
    if pred_bull == bull and pred_bear == bear:
        matches += 1
    total += 1

print(f"\nStrict Strong Match Rate: {matches}/{total} ({matches/total:.2%})")

matches_inc_rej = 0
for idx, row in comparison.iterrows():
    if row['Calculated_Bias'] == "N/A": continue
    calc = row['Calculated_Bias']
    bull = row['Bullish Bias']
    bear = row['Bearish Bias']
    
    pred_bull = 1 if calc in ["STRONG BULL", "BULL"] else 0
    pred_bear = 1 if calc in ["STRONG BEAR", "BEAR"] else 0
    
    if pred_bull == bull and pred_bear == bear:
        matches_inc_rej += 1

print(f"Match Rate including Rejections: {matches_inc_rej}/{total} ({matches_inc_rej/total:.2%})")

# Print mismatches for Rejection-included logic
print("\nMismatches (Rejection-Included Logic):")
for idx, row in comparison.iterrows():
    if row['Calculated_Bias'] == "N/A": continue
    calc = row['Calculated_Bias']
    bull = row['Bullish Bias']
    bear = row['Bearish Bias']
    
    pred_bull = 1 if calc in ["STRONG BULL", "BULL"] else 0
    pred_bear = 1 if calc in ["STRONG BEAR", "BEAR"] else 0
    
    if not (pred_bull == bull and pred_bear == bear):
        print(f"Date: {row['Date']}, CSV Bull/Bear: {bull}/{bear}, Calc: {calc}")
