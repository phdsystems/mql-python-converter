# Adaptive Laguerre Filter - Python Documentation

## Table of Contents
1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [API Reference](#api-reference)
4. [Parameter Guide](#parameter-guide)
5. [Usage Examples](#usage-examples)
6. [Trading Strategies](#trading-strategies)
7. [Backtesting Guide](#backtesting-guide)
8. [Performance Optimization](#performance-optimization)

## Installation

### Requirements
```bash
pip install numpy pandas matplotlib
```

### Files
- `adaptive_laguerre_filter.py` - Core implementation
- `adaptive_laguerre_advanced.py` - Trading system with backtesting
- `test_laguerre_simple.py` - Standalone version (no dependencies)

## Quick Start

```python
from adaptive_laguerre_filter import AdaptiveLaguerreFilter, SmoothMode
import numpy as np

# Create filter instance
alf = AdaptiveLaguerreFilter(
    length=10,
    order=4,
    adaptive_mode=True,
    adaptive_smooth=5,
    adaptive_smooth_mode=SmoothMode.MEDIAN
)

# Calculate on price data
prices = [100, 101, 102, 101, 103, 104, 103, 105, 106, 105]
result = alf.calculate(prices)

# Access results
filtered_values = result['laguerre']
trend_direction = result['trend']  # 1=up, 2=down, 0=neutral
gamma_values = result['gamma']
```

## API Reference

### Class: `AdaptiveLaguerreFilter`

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `length` | int | 10 | Period for calculations (3-200) |
| `order` | int | 4 | Filter order - recursive levels (1-10) |
| `adaptive_mode` | bool | True | Enable/disable adaptive gamma |
| `adaptive_smooth` | int | 5 | Smoothing period for gamma (1-50) |
| `adaptive_smooth_mode` | SmoothMode | MEDIAN | Smoothing algorithm |

#### Methods

##### `calculate(prices) -> dict`
Calculates the Adaptive Laguerre Filter.

**Parameters:**
- `prices`: array-like - Input price series (list, numpy array, or pandas Series)

**Returns:**
Dictionary with keys:
- `'laguerre'`: Filtered values (numpy array)
- `'trend'`: Trend direction (1=up, 2=down, 0=neutral)
- `'gamma'`: Adaptive gamma values

**Example:**
```python
result = alf.calculate(price_series)
laguerre_line = result['laguerre']
```

### Class: `AdaptiveLaguerreTrader`

Advanced trading system with backtesting capabilities.

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filter_params` | dict | None | Parameters for the filter |
| `risk_params` | dict | None | Risk management settings |

#### Risk Parameters

```python
risk_params = {
    'position_size': 1.0,      # Position size (0-1)
    'stop_loss_pct': 0.02,     # Stop loss percentage
    'take_profit_pct': 0.04,   # Take profit percentage
    'use_trailing_stop': True, # Enable trailing stop
    'trailing_stop_pct': 0.015 # Trailing stop percentage
}
```

#### Methods

##### `generate_signals(prices) -> pd.DataFrame`
Generate trading signals from price data.

##### `backtest(df, initial_capital=10000) -> dict`
Perform backtesting on signals.

**Returns:**
```python
{
    'metrics': {
        'total_return_pct': float,
        'win_rate_pct': float,
        'sharpe_ratio': float,
        'max_drawdown_pct': float,
        ...
    },
    'trades': [...],
    'equity_curve': array
}
```

### Enum: `SmoothMode`

```python
class SmoothMode(Enum):
    SMA = 0      # Simple Moving Average
    EMA = 1      # Exponential Moving Average
    WILDER = 2   # Wilder's Smoothing
    LWMA = 3     # Linear Weighted MA
    MEDIAN = 4   # Moving Median (recommended)
```

## Parameter Guide

### Optimal Settings by Trading Style

| Style | Length | Order | Adaptive | Smooth | Best Timeframe |
|-------|--------|-------|----------|--------|----------------|
| **Scalping** | 5-10 | 2-3 | True | 3-5 | 1min, 5min |
| **Day Trading** | 10-20 | 3-4 | True | 5-7 | 15min, 30min |
| **Swing Trading** | 20-50 | 4-5 | True | 7-10 | 1H, 4H |
| **Position Trading** | 50-100 | 4-6 | True/False | 10-15 | Daily |

### Parameter Impact Analysis

#### Length
- **Lower (3-10):** More responsive, more signals, higher false positive rate
- **Medium (10-30):** Balanced performance
- **Higher (30-100):** Smoother, fewer but more reliable signals

#### Order
- **1-2:** Minimal filtering, EMA-like behavior
- **3-4:** Optimal balance (recommended)
- **5-6:** Very smooth, good for volatile markets
- **7+:** Risk of overshoot (use with caution)

#### Adaptive Mode
- **True:** Dynamic response to market conditions
- **False:** Fixed gamma = 10/(length+9)

## Usage Examples

### Example 1: Basic Trend Following

```python
import pandas as pd
from adaptive_laguerre_filter import AdaptiveLaguerreFilter, SmoothMode

# Load your price data
df = pd.read_csv('price_data.csv')
prices = df['close'].values

# Configure filter for trend following
alf = AdaptiveLaguerreFilter(
    length=20,
    order=4,
    adaptive_mode=True,
    adaptive_smooth=7,
    adaptive_smooth_mode=SmoothMode.MEDIAN
)

# Calculate filter
result = alf.calculate(prices)

# Generate signals
signals = []
for i in range(1, len(result['trend'])):
    if result['trend'][i] == 1 and result['trend'][i-1] != 1:
        signals.append(('BUY', i, prices[i]))
    elif result['trend'][i] == 2 and result['trend'][i-1] != 2:
        signals.append(('SELL', i, prices[i]))
```

### Example 2: Multi-Timeframe Analysis

```python
# Short-term filter
alf_short = AdaptiveLaguerreFilter(length=10, order=3)
short_result = alf_short.calculate(prices)

# Long-term filter
alf_long = AdaptiveLaguerreFilter(length=50, order=5)
long_result = alf_long.calculate(prices)

# Trade only when both align
for i in range(len(prices)):
    short_trend = short_result['trend'][i]
    long_trend = long_result['trend'][i]
    
    if short_trend == 1 and long_trend == 1:
        print(f"Strong BUY at {i}")
    elif short_trend == 2 and long_trend == 2:
        print(f"Strong SELL at {i}")
```

### Example 3: Volatility-Based Adaptation

```python
def calculate_volatility(prices, period=20):
    """Calculate rolling volatility"""
    returns = pd.Series(prices).pct_change()
    return returns.rolling(period).std()

# Adjust parameters based on volatility
volatility = calculate_volatility(prices)
current_vol = volatility.iloc[-1]

# High volatility settings
if current_vol > 0.02:
    alf = AdaptiveLaguerreFilter(
        length=30,  # Longer period
        order=5,    # More smoothing
        adaptive_smooth=10
    )
# Low volatility settings
else:
    alf = AdaptiveLaguerreFilter(
        length=10,  # Shorter period
        order=3,    # Less smoothing
        adaptive_smooth=5
    )
```

### Example 4: Advanced Backtesting

```python
from adaptive_laguerre_advanced import AdaptiveLaguerreTrader

# Initialize trader with custom parameters
trader = AdaptiveLaguerreTrader(
    filter_params={
        'length': 15,
        'order': 4,
        'adaptive_mode': True,
        'adaptive_smooth': 6,
        'adaptive_smooth_mode': SmoothMode.EMA
    },
    risk_params={
        'position_size': 0.95,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.05,
        'use_trailing_stop': True,
        'trailing_stop_pct': 0.015
    }
)

# Generate signals
signals_df = trader.generate_signals(price_series)

# Run backtest
results = trader.backtest(signals_df, initial_capital=10000)

# Print metrics
print(f"Total Return: {results['metrics']['total_return_pct']:.2f}%")
print(f"Win Rate: {results['metrics']['win_rate_pct']:.2f}%")
print(f"Sharpe Ratio: {results['metrics']['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['metrics']['max_drawdown_pct']:.2f}%")
```

## Trading Strategies

### Strategy 1: Trend Following
```python
def trend_following_strategy(prices, alf):
    result = alf.calculate(prices)
    positions = []
    
    for i in range(len(prices)):
        if result['trend'][i] == 1:  # Uptrend
            positions.append(1)  # Long
        elif result['trend'][i] == 2:  # Downtrend
            positions.append(-1)  # Short
        else:
            positions.append(0)  # Neutral
    
    return positions
```

### Strategy 2: Mean Reversion
```python
def mean_reversion_strategy(prices, alf):
    result = alf.calculate(prices)
    positions = []
    
    for i in range(len(prices)):
        if prices[i] < result['laguerre'][i] * 0.98:  # 2% below filter
            positions.append(1)  # Buy (expect reversion up)
        elif prices[i] > result['laguerre'][i] * 1.02:  # 2% above filter
            positions.append(-1)  # Sell (expect reversion down)
        else:
            positions.append(0)
    
    return positions
```

### Strategy 3: Breakout with Filter Confirmation
```python
def breakout_strategy(prices, alf, breakout_period=20):
    result = alf.calculate(prices)
    positions = []
    
    for i in range(breakout_period, len(prices)):
        # Calculate recent high/low
        recent_high = max(prices[i-breakout_period:i])
        recent_low = min(prices[i-breakout_period:i])
        
        # Breakout with trend confirmation
        if prices[i] > recent_high and result['trend'][i] == 1:
            positions.append(1)  # Buy breakout
        elif prices[i] < recent_low and result['trend'][i] == 2:
            positions.append(-1)  # Sell breakdown
        else:
            positions.append(0)
    
    return positions
```

## Backtesting Guide

### Performance Metrics Explained

| Metric | Description | Good Value |
|--------|-------------|------------|
| `total_return_pct` | Total percentage return | > 20% annually |
| `win_rate_pct` | Percentage of winning trades | > 50% |
| `profit_factor` | Gross profit / Gross loss | > 1.5 |
| `sharpe_ratio` | Risk-adjusted return | > 1.0 |
| `max_drawdown_pct` | Maximum peak-to-trough decline | < 20% |
| `avg_win` | Average winning trade | > avg_loss |
| `avg_loss` | Average losing trade | Minimize |

### Backtesting Best Practices

1. **Use sufficient data**: At least 2-3 years for daily, 6 months for intraday
2. **Include transaction costs**: Add realistic slippage and commissions
3. **Walk-forward analysis**: Test on out-of-sample data
4. **Monte Carlo simulation**: Test parameter robustness
5. **Consider market regimes**: Test in trending and ranging markets

## Performance Optimization

### Speed Optimization

```python
import numpy as np

# Vectorized calculation for batch processing
def batch_calculate(price_matrix, alf):
    """Process multiple price series efficiently"""
    results = []
    for prices in price_matrix:
        results.append(alf.calculate(prices))
    return results

# Pre-allocate arrays
def optimized_calculate(prices, length, order):
    n = len(prices)
    laguerre = np.zeros(n)
    gamma = np.zeros(n)
    # ... rest of calculation
```

### Memory Optimization

```python
# Use generators for large datasets
def streaming_calculate(price_generator, alf):
    """Process streaming data without loading all in memory"""
    for price_chunk in price_generator:
        yield alf.calculate(price_chunk)

# Reduce precision if appropriate
prices_float32 = prices.astype(np.float32)  # Half memory vs float64
```

### Parallel Processing

```python
from multiprocessing import Pool

def parallel_backtest(param_grid, prices):
    """Test multiple parameter combinations in parallel"""
    def test_params(params):
        alf = AdaptiveLaguerreFilter(**params)
        result = alf.calculate(prices)
        # Calculate performance metric
        return calculate_performance(result)
    
    with Pool() as pool:
        results = pool.map(test_params, param_grid)
    
    return results
```

## Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| NaN values in output | Insufficient data | Check length requirement: need 2*length bars |
| Jagged filter line | Too responsive | Increase length or order |
| Excessive lag | Over-smoothing | Decrease length, enable adaptive mode |
| Memory error | Large datasets | Use streaming or batch processing |
| Slow calculation | Inefficient code | Use vectorized numpy operations |

## Mathematical Reference

### Core Laguerre Filter Equation
```python
# For order i:
if i == 0:
    L[0] = (1 - gamma) * price + gamma * L_prev[0]
else:
    L[i] = -gamma * L[i-1] + L_prev[i-1] + gamma * L_prev[i]

# Final output
laguerre = TriMA(L, order)
```

### Adaptive Gamma Calculation
```python
efficiency_ratio = (current_diff - min_diff) / (max_diff - min_diff)
gamma = smooth(efficiency_ratio, smooth_period, smooth_mode)
```

## Further Resources

- [Original MQL5 Implementation](AdaptiveLaguerre_v2.mq5)
- [Mathematical Formulas](AdaptiveLaguerre_Formulas.md)
- [Parameter Optimization Guide](laguerre_parameter_guide.md)
- [Simple Test Script](test_laguerre_simple.py)