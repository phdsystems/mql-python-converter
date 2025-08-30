#!/usr/bin/env python3
"""
Comprehensive Backtest Runner for MQL-Python Converter
Tests multiple strategies and currency pairs
"""

import sys
sys.path.insert(0, 'backtesting')
from simple_framework import SimpleMovingAverage, CrossoverStrategy, SimpleBacktester
import csv
from datetime import datetime

class Bar:
    def __init__(self, time, open_p, high, low, close, volume):
        self.time = time
        self.open = open_p
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

def load_csv_data(filename):
    """Load data from CSV file"""
    data = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'time': row['Date'] + ' ' + row['Time'],
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            })
    return data

def test_strategy(data, strategy_name, fast_period, slow_period, initial_capital=10000):
    """Test a specific strategy configuration"""
    prices = [bar['close'] for bar in data]
    
    # Calculate indicators
    sma_fast = SimpleMovingAverage.calculate(prices, fast_period)
    sma_slow = SimpleMovingAverage.calculate(prices, slow_period)
    
    # Generate signals
    strategy = CrossoverStrategy(fast_period, slow_period)
    signals = strategy.generate_signals(prices)
    
    # Run backtest
    backtester = SimpleBacktester(initial_capital=initial_capital)
    bars = [Bar(d['time'], d['open'], d['high'], d['low'], d['close'], d['volume']) for d in data]
    results = backtester.run(bars, signals)
    
    return {
        'strategy': strategy_name,
        'fast_period': fast_period,
        'slow_period': slow_period,
        'total_trades': results['total_trades'],
        'win_rate': results['win_rate'],
        'total_return': results['total_return'],
        'final_equity': initial_capital * (1 + results['total_return'])
    }

def main():
    print("="*80)
    print("MQL-Python Converter: Comprehensive Backtest")
    print("="*80)
    
    # Test configurations
    pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'GBPJPY']
    strategies = [
        ('Fast MA(5/10)', 5, 10),
        ('Standard MA(10/20)', 10, 20),
        ('Slow MA(20/50)', 20, 50),
        ('Long-term MA(50/100)', 50, 100)
    ]
    
    all_results = []
    
    for pair in pairs:
        csv_file = f'backtesting/test_data/{pair}240.csv'
        print(f"\n📊 Testing {pair}")
        print("-"*40)
        
        try:
            data = load_csv_data(csv_file)
            print(f"Loaded {len(data)} bars")
            print(f"Period: {data[0]['time']} to {data[-1]['time']}")
            
            for strategy_name, fast, slow in strategies:
                result = test_strategy(data, strategy_name, fast, slow)
                result['pair'] = pair
                all_results.append(result)
                
                print(f"\n  {strategy_name}:")
                print(f"    Trades: {result['total_trades']}")
                print(f"    Win Rate: {result['win_rate']:.1%}")
                print(f"    Return: {result['total_return']:.2%}")
                print(f"    Final Equity: ${result['final_equity']:.2f}")
                
        except Exception as e:
            print(f"Error processing {pair}: {e}")
    
    # Summary statistics
    print("\n" + "="*80)
    print("BACKTEST SUMMARY")
    print("="*80)
    
    # Best performing strategy by return
    best_return = max(all_results, key=lambda x: x['total_return'])
    print(f"\n🏆 Best Return:")
    print(f"   {best_return['pair']} - {best_return['strategy']}")
    print(f"   Return: {best_return['total_return']:.2%}")
    print(f"   Final Equity: ${best_return['final_equity']:.2f}")
    
    # Most consistent strategy (highest win rate)
    best_winrate = max(all_results, key=lambda x: x['win_rate'])
    print(f"\n🎯 Highest Win Rate:")
    print(f"   {best_winrate['pair']} - {best_winrate['strategy']}")
    print(f"   Win Rate: {best_winrate['win_rate']:.1%}")
    print(f"   Return: {best_winrate['total_return']:.2%}")
    
    # Most active strategy
    most_active = max(all_results, key=lambda x: x['total_trades'])
    print(f"\n📈 Most Active:")
    print(f"   {most_active['pair']} - {most_active['strategy']}")
    print(f"   Total Trades: {most_active['total_trades']}")
    print(f"   Return: {most_active['total_return']:.2%}")
    
    # Overall statistics
    avg_return = sum(r['total_return'] for r in all_results) / len(all_results)
    avg_winrate = sum(r['win_rate'] for r in all_results) / len(all_results)
    total_trades = sum(r['total_trades'] for r in all_results)
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Strategies Tested: {len(all_results)}")
    print(f"   Average Return: {avg_return:.2%}")
    print(f"   Average Win Rate: {avg_winrate:.1%}")
    print(f"   Total Trades: {total_trades}")
    
    print("\n" + "="*80)
    print("✅ Backtest Complete!")
    print("="*80)

if __name__ == "__main__":
    main()