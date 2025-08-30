"""
Example usage of the MQL to Python converter
Demonstrates how to use the converted Adaptive Laguerre Filter
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.adaptive_laguerre_filter import AdaptiveLaguerreFilter, SmoothMode
from tools.download_forex_data import load_data, get_price_series

def main():
    """
    Example: Using the converted Adaptive Laguerre Filter on forex data
    """
    
    print("="*60)
    print("MQL TO PYTHON CONVERTER - EXAMPLE USAGE")
    print("="*60)
    
    # 1. Load sample data (or use your own)
    print("\n1. Loading sample data...")
    # Generate sample data if no real data available
    import random
    prices = [100 + i * 0.1 + random.gauss(0, 1) for i in range(100)]
    
    # 2. Create the filter (converted from MQL5)
    print("\n2. Creating Adaptive Laguerre Filter...")
    alf = AdaptiveLaguerreFilter(
        length=10,
        order=4,
        adaptive_mode=True,
        adaptive_smooth=5,
        adaptive_smooth_mode=SmoothMode.MEDIAN
    )
    
    # 3. Calculate filter values
    print("\n3. Calculating filter values...")
    result = alf.calculate(prices)
    
    # 4. Extract results
    filtered_values = result['laguerre']
    trend_direction = result['trend']  # 1=up, 2=down
    gamma_values = result['gamma']
    
    # 5. Display sample results
    print("\n4. Sample Results (last 10 values):")
    print("-"*40)
    print("Price | Filter | Trend | Gamma")
    print("-"*40)
    
    for i in range(-10, 0):
        price = prices[i]
        filt = filtered_values[i] if filtered_values[i] else 0
        trend = "UP" if trend_direction[i] == 1 else "DOWN" if trend_direction[i] == 2 else "NEUTRAL"
        gamma = gamma_values[i] if gamma_values[i] else 0
        
        print(f"{price:.2f} | {filt:.2f} | {trend:7} | {gamma:.3f}")
    
    # 6. Generate trading signals
    print("\n5. Trading Signals:")
    print("-"*40)
    
    signals = []
    for i in range(1, len(trend_direction)):
        if trend_direction[i] == 1 and trend_direction[i-1] != 1:
            signals.append(('BUY', i, prices[i]))
        elif trend_direction[i] == 2 and trend_direction[i-1] != 2:
            signals.append(('SELL', i, prices[i]))
    
    print(f"Total signals generated: {len(signals)}")
    if signals:
        print("\nLast 5 signals:")
        for signal in signals[-5:]:
            print(f"  {signal[0]:5} at position {signal[1]:3}, price {signal[2]:.2f}")
    
    print("\n" + "="*60)
    print("Example completed successfully!")
    print("This demonstrates how MQL5 indicators can be used in Python")
    print("="*60)

if __name__ == "__main__":
    main()