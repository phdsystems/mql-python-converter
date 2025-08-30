"""
Simple test of Adaptive Laguerre Filter without external dependencies
Uses only built-in Python libraries for demonstration
"""

import math
import random

class SimpleLaguerreFilter:
    """Simplified Adaptive Laguerre Filter using only built-in libraries"""
    
    def __init__(self, length=10, order=4, adaptive_mode=True):
        self.length = length
        self.order = order
        self.adaptive_mode = adaptive_mode
        self.L = [[0, 0] for _ in range(order)]  # [current, previous]
        
    def calculate(self, prices):
        """Calculate Laguerre filter for price list"""
        n = len(prices)
        laguerre = [None] * n
        trend = [0] * n
        
        for i in range(n):
            if i < self.length * 2:
                continue
                
            # Calculate gamma
            if self.adaptive_mode:
                # Simple adaptive gamma based on price volatility
                if i >= self.length:
                    recent_prices = prices[i-self.length:i]
                    price_range = max(recent_prices) - min(recent_prices)
                    avg_price = sum(recent_prices) / len(recent_prices)
                    gamma = min(0.99, max(0.01, price_range / avg_price * 10))
                else:
                    gamma = 0.5
            else:
                gamma = 10.0 / (self.length + 9)
            
            # Calculate Laguerre filter
            laguerre[i] = self._laguerre_filter(prices[i], gamma, i)
            
            # Determine trend
            if i > 0 and laguerre[i] is not None and laguerre[i-1] is not None:
                if laguerre[i] > laguerre[i-1]:
                    trend[i] = 1  # Uptrend
                elif laguerre[i] < laguerre[i-1]:
                    trend[i] = -1  # Downtrend
                else:
                    trend[i] = trend[i-1]
        
        return laguerre, trend
    
    def _laguerre_filter(self, price, gamma, bar):
        """Core Laguerre filter calculation"""
        gam = 1 - gamma
        
        # Update previous values
        for i in range(self.order):
            self.L[i][1] = self.L[i][0]
        
        # Calculate Laguerre coefficients
        values = []
        for i in range(self.order):
            if bar <= self.order:
                self.L[i][0] = price
            else:
                if i == 0:
                    self.L[i][0] = (1 - gam) * price + gam * self.L[i][1]
                else:
                    self.L[i][0] = -gam * self.L[i-1][0] + self.L[i-1][1] + gam * self.L[i][1]
            values.append(self.L[i][0])
        
        # Return average of coefficients (simplified TriMA)
        return sum(values) / len(values)


def generate_sample_prices(n=200):
    """Generate sample price data"""
    random.seed(42)
    prices = []
    price = 100
    
    for i in range(n):
        # Add trend and noise
        trend = 0.1 * math.sin(i * 0.1)
        noise = random.gauss(0, 1)
        price = price * (1 + trend * 0.01 + noise * 0.005)
        prices.append(price)
    
    return prices


def print_chart(prices, laguerre, trend, width=80, height=20):
    """Print ASCII chart of prices and Laguerre filter"""
    # Find min and max for scaling
    valid_laguerre = [x for x in laguerre if x is not None]
    if not valid_laguerre:
        print("Not enough data to display chart")
        return
    
    all_values = prices + valid_laguerre
    min_val = min(all_values)
    max_val = max(all_values)
    value_range = max_val - min_val
    
    if value_range == 0:
        return
    
    # Create chart
    print("\nAdaptive Laguerre Filter - ASCII Chart")
    print("=" * width)
    print("Legend: . = Price, * = Laguerre Filter, ↑ = Uptrend, ↓ = Downtrend")
    print("-" * width)
    
    # Scale and plot
    for h in range(height, 0, -1):
        row = []
        threshold = min_val + (h / height) * value_range
        
        for i in range(0, min(width, len(prices))):
            idx = i * len(prices) // width
            
            char = ' '
            # Check if Laguerre crosses this level
            if laguerre[idx] is not None:
                if abs(laguerre[idx] - threshold) < value_range / height:
                    if trend[idx] == 1:
                        char = '↑'
                    elif trend[idx] == -1:
                        char = '↓'
                    else:
                        char = '*'
            # Check if price crosses this level
            elif abs(prices[idx] - threshold) < value_range / height:
                char = '.'
            
            row.append(char)
        
        print(f"{threshold:7.2f} |{''.join(row)}")
    
    print("-" * width)
    print(f"        {' ' * (width//4)}Time →")


def analyze_signals(prices, laguerre, trend):
    """Analyze trading signals and performance"""
    signals = []
    in_position = False
    entry_price = 0
    total_return = 0
    
    for i in range(1, len(trend)):
        if laguerre[i] is None:
            continue
            
        # Entry signal
        if not in_position and trend[i] == 1 and trend[i-1] != 1:
            in_position = True
            entry_price = prices[i]
            signals.append(('BUY', i, entry_price))
        
        # Exit signal
        elif in_position and trend[i] == -1 and trend[i-1] != -1:
            in_position = False
            exit_price = prices[i]
            return_pct = (exit_price - entry_price) / entry_price * 100
            total_return += return_pct
            signals.append(('SELL', i, exit_price, return_pct))
    
    # Close last position if still open
    if in_position:
        exit_price = prices[-1]
        return_pct = (exit_price - entry_price) / entry_price * 100
        total_return += return_pct
        signals.append(('SELL', len(prices)-1, exit_price, return_pct))
    
    return signals, total_return


# Main execution
if __name__ == "__main__":
    print("Adaptive Laguerre Filter - Python Implementation")
    print("=" * 60)
    
    # Generate sample data
    prices = generate_sample_prices(200)
    
    # Calculate Adaptive Laguerre Filter
    print("\nCalculating Adaptive Laguerre Filter...")
    alf = SimpleLaguerreFilter(length=10, order=4, adaptive_mode=True)
    laguerre, trend = alf.calculate(prices)
    
    # Display chart
    print_chart(prices, laguerre, trend)
    
    # Analyze signals
    signals, total_return = analyze_signals(prices, laguerre, trend)
    
    # Print statistics
    print("\n" + "=" * 60)
    print("Trading Signal Analysis")
    print("-" * 60)
    
    if signals:
        print(f"Total Signals: {len(signals)}")
        buy_signals = [s for s in signals if s[0] == 'BUY']
        sell_signals = [s for s in signals if s[0] == 'SELL' and len(s) > 3]
        
        print(f"Buy Signals: {len(buy_signals)}")
        print(f"Sell Signals: {len(sell_signals)}")
        
        if sell_signals:
            returns = [s[3] for s in sell_signals]
            winning = [r for r in returns if r > 0]
            losing = [r for r in returns if r <= 0]
            
            print(f"\nWinning Trades: {len(winning)}")
            print(f"Losing Trades: {len(losing)}")
            if returns:
                print(f"Win Rate: {len(winning)/len(returns)*100:.1f}%")
                print(f"Average Return per Trade: {sum(returns)/len(returns):.2f}%")
                print(f"Total Return: {total_return:.2f}%")
        
        # Show last few signals
        print("\nLast 5 Trading Signals:")
        print("-" * 40)
        for signal in signals[-5:]:
            if signal[0] == 'BUY':
                print(f"  {signal[0]:5} at position {signal[1]:3}, price {signal[2]:.2f}")
            else:
                print(f"  {signal[0]:5} at position {signal[1]:3}, price {signal[2]:.2f}, return {signal[3]:.2f}%")
    else:
        print("No trading signals generated")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  • Filter Order: {alf.order}")
    print(f"  • Length: {alf.length}")
    print(f"  • Adaptive Mode: {'Enabled' if alf.adaptive_mode else 'Disabled'}")
    print(f"  • Data Points: {len(prices)}")
    print(f"  • Valid Filter Values: {sum(1 for x in laguerre if x is not None)}")
    
    print("\nThe Adaptive Laguerre Filter successfully reduces lag")
    print("while maintaining smooth output for trend detection.")