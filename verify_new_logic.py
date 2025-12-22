import pandas as pd

# Load Data
df = pd.read_csv("new_data_verification.csv")

# Filter for EURUSD and GBPUSD
symbols = df['Symbol'].unique()

print(f"Verifying Logic V5 (Ignore Fakeouts) on {symbols}...")

BREAKOUT_FILTER = 0.00020 # 2 pips tolerance? Let's try 0.0001
# Note: User's previous filter was 2.0 on a 4-digit/5-digit mix. 
# For standard forex 1.1740, 1 pip is 0.0001. 2.0 points usually means 0.2 pips or 2 pips depending on broker.
# Let's assume 2 pips = 0.0002 for safety.

for symbol in symbols:
    print(f"\n--- Analyzing {symbol} ---")
    sub_df = df[df['Symbol'] == symbol].copy()
    
    # Sort chronological (Oldest First)
    sub_df = sub_df.iloc[::-1].reset_index(drop=True)
    
    # Initialize Logic State
    # Need to simulate the recursive "Mother Candle" state
    
    # We need a starting point. Let's assume the first candle establishes structure.
    mother_h = sub_df.iloc[0]['High']
    mother_l = sub_df.iloc[0]['Low']
    mother_idx = 0
    
    mismatches = 0
    
    # Iterate from 2nd candle onwards
    for i in range(1, len(sub_df)):
        c1 = sub_df.iloc[i]
        
        date = c1['Date']
        close = c1['Close']
        high = c1['High']
        low = c1['Low']
        
        csv_bull = c1['Bullish Bias'] == 1.0
        csv_bear = c1['Bearish Bias'] == 1.0
        
        # LOGIC V5
        is_bull = False
        is_bear = False
        update_structure = False
        
        logic_reason = "Inside"
        
        # 1. Close Breakout
        if close > mother_h + BREAKOUT_FILTER:
            is_bull = True
            update_structure = True
            logic_reason = "Bull Break"
        elif close < mother_l - BREAKOUT_FILTER:
            is_bear = True
            update_structure = True
            logic_reason = "Bear Break"
        else:
            # 2. Rejections (Fakeouts)
            if low < mother_l and close > mother_l:
                is_bull = True
                logic_reason = "Bull Reject"
                # Keep Old Mother
            elif high > mother_h and close < mother_h:
                is_bear = True
                logic_reason = "Bear Reject"
                # Keep Old Mother
        
        # Check Match
        match = False
        if is_bull and csv_bull: match = True
        elif is_bear and csv_bear: match = True
        elif (not is_bull and not is_bear) and (not csv_bull and not csv_bear): match = True
        
        if not match:
            mismatches += 1
            print(f"FAIL {date}: CSV Bull/Bear={csv_bull}/{csv_bear} | Logic={logic_reason} | Mother={sub_df.iloc[mother_idx]['Date']} H:{mother_h} L:{mother_l}")
        
        # Update State
        if update_structure:
            mother_h = high
            mother_l = low
            mother_idx = i

    print(f"{symbol} Accuracy: {len(sub_df)-1 - mismatches}/{len(sub_df)-1}")
