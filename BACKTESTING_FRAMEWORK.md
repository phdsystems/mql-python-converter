# MQL4 to Python Backtesting & Validation Framework

## Overview
This framework provides tools for validating MQL4 to Python indicator conversions and running backtests with historical data.

## Components Created

### 1. MQL4 Test Indicators
**File**: `server/mt4-terminal/MQL4/Indicators/SimpleMA_Test.mq4`
- Simple Moving Average indicator for testing
- Supports both Fast and Slow MA periods
- Multiple MA methods (SMA, EMA, SMMA, LWMA)
- Crossover signal detection

### 2. Python Backtesting Framework

#### Full Framework (with pandas)
**File**: `backtesting/framework.py`
- MT4 history file reader (.hst format)
- Indicator base classes
- SimpleMA Python implementation
- Backtest engine with position tracking
- Performance statistics calculation
- Indicator comparison tools

Features:
- Read MT4 .hst history files
- Calculate technical indicators
- Generate trading signals
- Run backtests with P&L tracking
- Compare MQL4 vs Python outputs

#### Simplified Framework (no dependencies)
**File**: `backtesting/simple_framework.py`
- Pure Python implementation (no external dependencies)
- MT4 data reader
- Simple Moving Average calculations
- Crossover strategy
- Basic backtester
- Value comparison tools

### 3. Validation Scripts
**File**: `backtesting/validate_conversion.py`
- Automated validation suite
- Tests multiple indicator parameters
- Edge case testing
- Accuracy verification
- JSON report generation

## Usage Examples

### 1. Load Historical Data
```python
from backtesting.simple_framework import MT4DataReader

reader = MT4DataReader("path/to/EURUSD240.hst")
data = reader.read()
print(f"Loaded {len(data)} bars")
```

### 2. Calculate Indicators
```python
from backtesting.simple_framework import SimpleMovingAverage

prices = [bar.close for bar in data]
sma_10 = SimpleMovingAverage.calculate(prices, period=10)
sma_20 = SimpleMovingAverage.calculate(prices, period=20)
```

### 3. Generate Trading Signals
```python
from backtesting.simple_framework import CrossoverStrategy

strategy = CrossoverStrategy(fast_period=10, slow_period=20)
signals = strategy.generate_signals(prices)
```

### 4. Run Backtest
```python
from backtesting.simple_framework import SimpleBacktester

backtester = SimpleBacktester(initial_capital=10000)
results = backtester.run(data, signals)
print(f"Total Return: {results['total_return']:.2%}")
print(f"Win Rate: {results['win_rate']:.2%}")
```

### 5. Compare MQL4 vs Python
```python
from backtesting.simple_framework import ConversionComparator

comparison = ConversionComparator.compare_values(
    mql4_values, 
    python_values,
    tolerance=1e-5
)
print(f"Values match: {comparison['match']}")
print(f"Max difference: {comparison['max_difference']}")
```

## Testing Workflow

### Step 1: Create MQL4 Indicator
1. Write MQL4 indicator in MT4
2. Compile using MT4 terminal
3. Export values for comparison

### Step 2: Implement Python Version
1. Create Python equivalent of MQL4 indicator
2. Use same parameters and calculation methods
3. Process same historical data

### Step 3: Validate Conversion
1. Load same historical data in both
2. Calculate indicator values
3. Compare outputs within tolerance
4. Generate validation report

### Step 4: Backtest Strategy
1. Generate trading signals
2. Run backtest simulation
3. Calculate performance metrics
4. Compare MQL4 vs Python results

## Known Issues

### Data Format
The MT4 history files (.hst) in the demo installation appear to contain sample/corrupted data. For production use:
1. Connect MT4 to a broker for real data
2. Export data from MT4 as CSV
3. Use third-party historical data sources

### MT4 Connection
Due to Wine network limitations (error 10042), MT4 cannot connect to live servers. Workarounds:
1. Use offline/historical data only
2. Import tick data manually
3. Use Strategy Tester in MT4
4. Run on Windows VM for full functionality

## Performance Metrics

The framework calculates:
- Total trades
- Win rate
- Total return
- Sharpe ratio
- Maximum drawdown
- Average win/loss
- Profit factor

## Validation Criteria

Conversions are validated by:
1. **Numerical Accuracy**: Values match within tolerance (default 1e-5)
2. **Signal Matching**: Same buy/sell signals generated
3. **Performance Parity**: Similar backtest results
4. **Edge Case Handling**: Proper handling of empty/invalid data

## Next Steps

1. **Fix Data Issues**
   - Obtain valid historical data
   - Implement CSV import/export
   - Add data validation checks

2. **Expand Indicators**
   - RSI, MACD, Bollinger Bands
   - Custom indicators
   - Multi-timeframe analysis

3. **Enhanced Backtesting**
   - Transaction costs
   - Slippage modeling
   - Position sizing
   - Risk management

4. **Automation**
   - Automated conversion pipeline
   - Continuous validation
   - Performance monitoring

## Files Structure
```
mql-python-converter/
├── backtesting/
│   ├── framework.py           # Full framework with pandas
│   ├── simple_framework.py    # Simplified framework (no deps)
│   └── validate_conversion.py # Validation suite
├── server/mt4-terminal/
│   └── MQL4/Indicators/
│       └── SimpleMA_Test.mq4  # Test indicator
└── BACKTESTING_FRAMEWORK.md   # This file
```

## Conclusion

The framework is ready for MQL4 to Python conversion validation. While MT4 cannot connect to live servers due to Wine limitations, the framework can:
- ✅ Read MT4 history files
- ✅ Calculate indicators in Python
- ✅ Compare MQL4 vs Python outputs
- ✅ Run backtests on historical data
- ✅ Generate validation reports

For production use with live data, consider using a Windows environment or alternative data sources.