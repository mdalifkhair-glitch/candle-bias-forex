"""
Bias Calculator - Implements MT4 Trend Bias Logic
Compares current closed candle (C1) vs previous candle (C2)
"""

def calculate_bias(c1_open: float, c1_high: float, c1_low: float, c1_close: float,
                   c2_open: float, c2_high: float, c2_low: float, c2_close: float) -> str:
    """
    Calculate bias based on candle comparison.
    
    C1 = Last closed candle (yesterday/last week/last month)
    C2 = Candle before C1 (2 days ago/2 weeks ago/2 months ago)
    
    Priority Order (first match wins):
    1. STRONG BULL: C1.Close > C2.High (clean breakout above)
    2. STRONG BEAR: C1.Close < C2.Low (clean breakdown below)
    3. BEAR: C1.High > C2.High AND C1.Close < C2.High (rejection from high)
    4. BULL: C1.Low < C2.Low AND C1.Close > C2.Low (recovery from low)
    5. NEUTRAL: Inside bar (within previous range)
    """
    
    # STRONG BULL: Clean break above (close > previous high)
    if c1_close > c2_high:
        return "STRONG BULL"
    
    # STRONG BEAR: Clean break below (close < previous low)
    if c1_close < c2_low:
        return "STRONG BEAR"
    
    # BEAR: Rejection from high (tested above but failed)
    if c1_high > c2_high and c1_close < c2_high:
        return "BEAR"
    
    # BULL: Rejection recovery (tested below but recovered)
    if c1_low < c2_low and c1_close > c2_low:
        return "BULL"
    
    # NEUTRAL: Inside bar (within previous candle range)
    if c1_high <= c2_high and c1_low >= c2_low:
        return "NEUTRAL"
    
    return "NEUTRAL"


def get_bias_from_candles(candles: list) -> str:
    """
    Get bias from a list of candle data.
    Expects at least 3 candles, most recent first.
    Each candle should have: open, high, low, close
    
    C0 = Current candle (incomplete, skip this)
    C1 = Last closed candle (yesterday/last week/last month)
    C2 = Candle before C1
    
    We compare C1 vs C2 (ignore C0 as it's not complete yet)
    """
    if len(candles) < 3:
        return "NEUTRAL"
    
    c1 = candles[1]  # C1: Last CLOSED candle
    c2 = candles[2]  # C2: Candle before C1
    
    return calculate_bias(
        c1['open'], c1['high'], c1['low'], c1['close'],
        c2['open'], c2['high'], c2['low'], c2['close']
    )
