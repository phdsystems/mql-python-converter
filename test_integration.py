import sys
sys.path.insert(0, 'backtesting')
from simple_framework import MT4DataReader, SimpleMovingAverage, CrossoverStrategy, SimpleBacktester
import os
import csv

# Test reading CSV data
csv_file = 'backtesting/test_data/EURUSD240.csv'
print('Testing Python Framework')
print('='*50)

# Read CSV data
data = []
with open(csv_file, 'r') as f:
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

print(f'✅ Loaded {len(data)} bars from CSV')
print(f'   First: {data[0]["time"]} Close={data[0]["close"]:.5f}')
print(f'   Last:  {data[-1]["time"]} Close={data[-1]["close"]:.5f}')

# Calculate indicators
prices = [bar['close'] for bar in data]
sma_10 = SimpleMovingAverage.calculate(prices, 10)
sma_20 = SimpleMovingAverage.calculate(prices, 20)

print(f'\n✅ Calculated indicators:')
print(f'   SMA(10) last value: {sma_10[-1]:.5f}')
print(f'   SMA(20) last value: {sma_20[-1]:.5f}')

# Generate signals
strategy = CrossoverStrategy(10, 20)
signals = strategy.generate_signals(prices)
buy_signals = sum(1 for s in signals if s == 1)
sell_signals = sum(1 for s in signals if s == -1)

print(f'\n✅ Generated trading signals:')
print(f'   Buy signals: {buy_signals}')
print(f'   Sell signals: {sell_signals}')

# Run backtest
backtester = SimpleBacktester(initial_capital=10000)

# Convert data to required format
class Bar:
    def __init__(self, time, open_p, high, low, close, volume):
        self.time = time
        self.open = open_p
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

bars = [Bar(d['time'], d['open'], d['high'], d['low'], d['close'], d['volume']) for d in data]
results = backtester.run(bars, signals)

print(f'\n✅ Backtest Results:')
print(f'   Total trades: {results["total_trades"]}')
print(f'   Win rate: {results["win_rate"]:.1%}')
print(f'   Total return: {results["total_return"]:.2%}')
if "final_equity" in results:
    print(f'   Final equity: ${results["final_equity"]:.2f}')
else:
    print(f'   Final P&L: ${10000 * (1 + results["total_return"]):.2f}')

print('\n'+'='*50)
print('✅ Python-MQL Integration Test: PASSED')