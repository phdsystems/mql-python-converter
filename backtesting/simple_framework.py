#!/usr/bin/env python3
"""
Simplified MQL4 to Python Backtesting Framework
No external dependencies required - uses only Python standard library
"""

import struct
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json
import math


@dataclass
class OHLCV:
    """Simple OHLC data structure"""
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class MT4DataReader:
    """Reads MT4 .hst files without pandas"""
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data = []
        self.header = {}
        
    def read(self) -> List[OHLCV]:
        """Read MT4 history file"""
        with open(self.filepath, 'rb') as f:
            # Read header (148 bytes)
            self.header['version'] = struct.unpack('<I', f.read(4))[0]
            self.header['copyright'] = f.read(64).decode('ascii', 'ignore').strip('\x00')
            self.header['symbol'] = f.read(12).decode('ascii', 'ignore').strip('\x00')
            self.header['period'] = struct.unpack('<I', f.read(4))[0]
            self.header['digits'] = struct.unpack('<I', f.read(4))[0]
            f.read(60)  # Skip rest of header
            
            # Read bars
            while True:
                bar_data = f.read(60)
                if len(bar_data) < 60:
                    break
                    
                time_val = struct.unpack('<I', bar_data[0:4])[0]
                open_val = struct.unpack('<d', bar_data[4:12])[0]
                high_val = struct.unpack('<d', bar_data[12:20])[0]
                low_val = struct.unpack('<d', bar_data[20:28])[0]
                close_val = struct.unpack('<d', bar_data[28:36])[0]
                volume_val = struct.unpack('<Q', bar_data[36:44])[0]
                
                self.data.append(OHLCV(
                    time=datetime.fromtimestamp(time_val),
                    open=open_val,
                    high=high_val,
                    low=low_val,
                    close=close_val,
                    volume=volume_val
                ))
                
        return self.data


class SimpleMovingAverage:
    """Simple Moving Average indicator"""
    
    @staticmethod
    def calculate(data: List[float], period: int) -> List[Optional[float]]:
        """Calculate SMA"""
        result = []
        for i in range(len(data)):
            if i < period - 1:
                result.append(None)
            else:
                window = data[i - period + 1:i + 1]
                result.append(sum(window) / period)
        return result
    
    @staticmethod
    def calculate_ema(data: List[float], period: int) -> List[Optional[float]]:
        """Calculate EMA"""
        result = []
        multiplier = 2 / (period + 1)
        
        # Start with SMA for first value
        sma_first = None
        for i in range(len(data)):
            if i < period - 1:
                result.append(None)
            elif i == period - 1:
                sma_first = sum(data[:period]) / period
                result.append(sma_first)
            else:
                prev_ema = result[-1]
                ema = (data[i] - prev_ema) * multiplier + prev_ema
                result.append(ema)
                
        return result


class CrossoverStrategy:
    """Moving Average Crossover Strategy"""
    
    def __init__(self, fast_period: int = 10, slow_period: int = 20):
        self.fast_period = fast_period
        self.slow_period = slow_period
        
    def generate_signals(self, prices: List[float]) -> List[int]:
        """
        Generate trading signals
        Returns: List of signals (1=buy, -1=sell, 0=hold)
        """
        fast_ma = SimpleMovingAverage.calculate(prices, self.fast_period)
        slow_ma = SimpleMovingAverage.calculate(prices, self.slow_period)
        
        signals = []
        for i in range(len(prices)):
            if i == 0 or fast_ma[i] is None or slow_ma[i] is None or \
               fast_ma[i-1] is None or slow_ma[i-1] is None:
                signals.append(0)
                continue
                
            # Check for crossover
            if fast_ma[i-1] <= slow_ma[i-1] and fast_ma[i] > slow_ma[i]:
                signals.append(1)  # Bullish crossover
            elif fast_ma[i-1] >= slow_ma[i-1] and fast_ma[i] < slow_ma[i]:
                signals.append(-1)  # Bearish crossover
            else:
                signals.append(0)  # No signal
                
        return signals


class SimpleBacktester:
    """Simple backtesting engine"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0
        self.trades = []
        
    def run(self, data: List[OHLCV], signals: List[int]) -> Dict:
        """Run backtest"""
        for i in range(len(data)):
            if signals[i] == 0:
                continue
                
            price = data[i].close
            
            if signals[i] == 1 and self.position == 0:
                # Buy
                shares = self.capital / price
                self.position = shares
                self.trades.append({
                    'time': data[i].time,
                    'type': 'BUY',
                    'price': price,
                    'shares': shares
                })
                
            elif signals[i] == -1 and self.position > 0:
                # Sell
                pnl = (price - self.trades[-1]['price']) * self.position
                self.capital += pnl
                self.trades.append({
                    'time': data[i].time,
                    'type': 'SELL',
                    'price': price,
                    'shares': self.position,
                    'pnl': pnl
                })
                self.position = 0
                
        # Calculate statistics
        winning_trades = [t for t in self.trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in self.trades if t.get('pnl', 0) < 0]
        
        total_return = (self.capital - self.initial_capital) / self.initial_capital
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'total_return': total_return,
            'total_trades': len([t for t in self.trades if t['type'] == 'SELL']),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / max(1, len(winning_trades) + len(losing_trades))
        }


class ConversionComparator:
    """Compare MQL4 and Python indicator outputs"""
    
    @staticmethod
    def compare_values(mql4_values: List[float], python_values: List[float], 
                      tolerance: float = 1e-5) -> Dict:
        """Compare two lists of values"""
        if len(mql4_values) != len(python_values):
            return {
                'match': False,
                'error': f'Length mismatch: MQL4={len(mql4_values)}, Python={len(python_values)}'
            }
        
        differences = []
        max_diff = 0
        
        for i in range(len(mql4_values)):
            if mql4_values[i] is None or python_values[i] is None:
                continue
            diff = abs(mql4_values[i] - python_values[i])
            differences.append(diff)
            max_diff = max(max_diff, diff)
            
        avg_diff = sum(differences) / len(differences) if differences else 0
        
        return {
            'match': max_diff <= tolerance,
            'max_difference': max_diff,
            'avg_difference': avg_diff,
            'tolerance': tolerance,
            'values_compared': len(differences)
        }


def test_framework():
    """Test the framework with sample data"""
    print("Testing Simplified Backtesting Framework")
    print("=" * 50)
    
    # Load data
    data_file = "/home/developer/mql-python-converter/server/mt4-terminal/history/default/EURUSD240.hst"
    
    if not Path(data_file).exists():
        print(f"Data file not found: {data_file}")
        return
    
    reader = MT4DataReader(data_file)
    data = reader.read()
    
    print(f"Loaded {reader.header['symbol']} {reader.header['period']}M")
    print(f"Total bars: {len(data)}")
    print(f"Date range: {data[0].time} to {data[-1].time}")
    
    # Extract close prices
    prices = [bar.close for bar in data]
    
    # Test SMA calculation
    print("\n" + "-" * 50)
    print("Testing SMA Calculation")
    sma_10 = SimpleMovingAverage.calculate(prices[:100], 10)
    sma_20 = SimpleMovingAverage.calculate(prices[:100], 20)
    
    # Show some values
    print(f"SMA(10) at bar 50: {sma_10[50]:.5f}")
    print(f"SMA(20) at bar 50: {sma_20[50]:.5f}")
    
    # Manual verification
    manual_sma_10 = sum(prices[40:50]) / 10
    print(f"Manual SMA(10) at bar 50: {manual_sma_10:.5f}")
    print(f"Difference: {abs(sma_10[50] - manual_sma_10):.8f}")
    
    # Test strategy
    print("\n" + "-" * 50)
    print("Testing Crossover Strategy")
    strategy = CrossoverStrategy(fast_period=10, slow_period=20)
    signals = strategy.generate_signals(prices)
    
    buy_signals = signals.count(1)
    sell_signals = signals.count(-1)
    print(f"Buy signals: {buy_signals}")
    print(f"Sell signals: {sell_signals}")
    
    # Run backtest
    print("\n" + "-" * 50)
    print("Running Backtest")
    backtester = SimpleBacktester(initial_capital=10000)
    results = backtester.run(data, signals)
    
    for key, value in results.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
    
    # Test comparison
    print("\n" + "-" * 50)
    print("Testing Value Comparison")
    
    # Create slightly different values for testing
    python_values = sma_10[:50]
    mql4_values = [v + 0.00001 if v else v for v in python_values]  # Small difference
    
    comparison = ConversionComparator.compare_values(mql4_values, python_values)
    print(f"Values match: {comparison['match']}")
    print(f"Max difference: {comparison['max_difference']:.8f}")
    print(f"Avg difference: {comparison['avg_difference']:.8f}")
    
    print("\n✅ Framework test completed successfully!")


if __name__ == "__main__":
    test_framework()