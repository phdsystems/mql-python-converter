# Triple Power Stop Parameter Optimization Guide

## 🎯 Overview

This guide helps you optimize the Triple Power Stop (CHE) parameters for different trading strategies and market conditions.

## 📊 Parameter Impact Analysis

### 1. **ATR Length (atr_length)**
**Default**: 14  
**Range**: 5-50  
**Impact**: Controls volatility measurement period

```python
# Conservative (smoother): 20-30
config.atr_length = 21

# Aggressive (more responsive): 7-12  
config.atr_length = 10

# Standard (balanced): 14
config.atr_length = 14
```

**Effects**:
- **Higher values**: Smoother stops, less noise, slower adaptation
- **Lower values**: More responsive stops, more signals, higher noise

### 2. **Base ATR Multiplier (base_atr_multiplier)**
**Default**: 2.0  
**Range**: 1.0-4.0  
**Impact**: Controls stop distance from price

```python
# Tight stops (higher risk/reward): 1.5-2.0
config.base_atr_multiplier = 1.8

# Wide stops (conservative): 2.5-3.5
config.base_atr_multiplier = 3.0

# Very tight (scalping): 1.0-1.5
config.base_atr_multiplier = 1.2
```

**Effects**:
- **Higher values**: Wider stops, fewer false exits, lower win rate
- **Lower values**: Tighter stops, more false exits, higher win rate

### 3. **Timeframe Multipliers (multiplier1, multiplier2, multiplier3)**
**Default**: 1, 2, 3  
**Range**: 1-10 each  
**Impact**: Controls multi-timeframe analysis scope

```python
# Short-term focus: 1, 2, 3
config.multiplier1, config.multiplier2, config.multiplier3 = 1, 2, 3

# Medium-term focus: 2, 4, 8  
config.multiplier1, config.multiplier2, config.multiplier3 = 2, 4, 8

# Long-term focus: 5, 10, 20
config.multiplier1, config.multiplier2, config.multiplier3 = 5, 10, 20
```

**Effects**:
- **Smaller gaps**: More signals, higher noise
- **Larger gaps**: Fewer signals, stronger trend confirmation

### 4. **Smooth Period (smooth_period)**
**Default**: 10  
**Range**: 3-21  
**Impact**: Controls price smoothing for trend detection

```python
# Minimal smoothing: 3-5
config.smooth_period = 5

# Standard smoothing: 8-12
config.smooth_period = 10

# Heavy smoothing: 15-21
config.smooth_period = 18
```

## 🎯 Trading Strategy Configurations

### **Scalping Strategy**
```python
scalping_config = TPSConfig(
    atr_length=7,           # Quick volatility response
    base_atr_multiplier=1.5, # Tight stops
    multiplier1=1,          # Very short timeframes
    multiplier2=2,
    multiplier3=3,
    smooth_period=5         # Minimal smoothing
)
```
**Characteristics**: High frequency, tight stops, quick entries/exits

### **Day Trading Strategy**
```python
daytrading_config = TPSConfig(
    atr_length=14,          # Standard volatility measurement
    base_atr_multiplier=2.0, # Balanced stop distance
    multiplier1=1,          # Mixed timeframes
    multiplier2=3,
    multiplier3=6,
    smooth_period=10        # Standard smoothing
)
```
**Characteristics**: Multiple signals per day, moderate stops

### **Swing Trading Strategy**
```python
swing_config = TPSConfig(
    atr_length=21,          # Smooth volatility
    base_atr_multiplier=2.5, # Wider stops
    multiplier1=2,          # Longer timeframes
    multiplier2=5,
    multiplier3=10,
    smooth_period=15        # More smoothing
)
```
**Characteristics**: Hold positions days/weeks, wider stops

### **Position Trading Strategy**
```python
position_config = TPSConfig(
    atr_length=30,          # Very smooth volatility
    base_atr_multiplier=3.0, # Wide stops
    multiplier1=5,          # Long timeframes
    multiplier2=15,
    multiplier3=30,
    smooth_period=21        # Heavy smoothing
)
```
**Characteristics**: Hold positions weeks/months, very wide stops

## 📈 Market Condition Adaptations

### **Trending Markets**
```python
trending_config = TPSConfig(
    atr_length=14,
    base_atr_multiplier=2.2,  # Slightly wider for trends
    multiplier1=1,
    multiplier2=4,            # Bigger gap for trend confirmation
    multiplier3=8,
    smooth_period=12          # More smoothing
)
```

### **Volatile/Choppy Markets**
```python
volatile_config = TPSConfig(
    atr_length=21,            # Longer period for stability
    base_atr_multiplier=2.8,  # Wider stops for volatility
    multiplier1=2,
    multiplier2=3,            # Smaller gaps to reduce noise
    multiplier3=4,
    smooth_period=15          # More smoothing
)
```

### **Low Volatility Markets**
```python
lowvol_config = TPSConfig(
    atr_length=10,            # Shorter for responsiveness
    base_atr_multiplier=1.8,  # Tighter stops
    multiplier1=1,
    multiplier2=2,
    multiplier3=3,
    smooth_period=8           # Less smoothing
)
```

## 🔧 Parameter Optimization Process

### **Step 1: Historical Analysis**
```python
# Test different ATR lengths
atr_lengths = [7, 10, 14, 21, 30]
for length in atr_lengths:
    config.atr_length = length
    result = backtest(config, historical_data)
    print(f"ATR {length}: Sharpe={result.sharpe:.3f}")
```

### **Step 2: Stop Distance Optimization**
```python
# Test multiplier range
multipliers = [1.5, 2.0, 2.5, 3.0, 3.5]
for mult in multipliers:
    config.base_atr_multiplier = mult
    result = backtest(config, historical_data)
    print(f"Mult {mult}: Win%={result.win_rate:.1f}%")
```

### **Step 3: Timeframe Tuning**
```python
# Test timeframe combinations
timeframe_sets = [
    (1, 2, 3),    # Short-term
    (1, 3, 6),    # Balanced
    (2, 5, 10),   # Medium-term
    (5, 10, 20)   # Long-term
]
for tf in timeframe_sets:
    config.multiplier1, config.multiplier2, config.multiplier3 = tf
    result = backtest(config, historical_data)
    print(f"TF {tf}: Return={result.total_return:.2f}%")
```

## 📊 Performance Metrics to Track

### **Signal Quality**
- **Signal Count**: Total long + short signals
- **Signal Accuracy**: % of profitable signals
- **False Signal Rate**: % of losing signals

### **Risk Management**
- **Average Stop Distance**: Mean % distance to stop
- **Stop Hit Rate**: % of positions stopped out
- **Maximum Drawdown**: Largest equity decline

### **Return Characteristics**
- **Total Return**: Overall profit/loss %
- **Sharpe Ratio**: Risk-adjusted returns
- **Win Rate**: % of profitable trades
- **Profit Factor**: Gross profit / Gross loss

## 🎯 Recommended Starting Points

### **Conservative Trader**
```python
conservative = TPSConfig(
    atr_length=21,
    base_atr_multiplier=2.8,
    multiplier1=2,
    multiplier2=5,
    multiplier3=10,
    smooth_period=15
)
```

### **Balanced Trader**
```python
balanced = TPSConfig(
    atr_length=14,
    base_atr_multiplier=2.0,
    multiplier1=1,
    multiplier2=3,
    multiplier3=6,
    smooth_period=10
)
```

### **Aggressive Trader**
```python
aggressive = TPSConfig(
    atr_length=10,
    base_atr_multiplier=1.8,
    multiplier1=1,
    multiplier2=2,
    multiplier3=4,
    smooth_period=8
)
```

## ⚠️ Important Considerations

1. **Market Regime Changes**: Re-optimize parameters quarterly
2. **Overfitting Risk**: Test on out-of-sample data
3. **Transaction Costs**: Account for spreads and commissions
4. **Slippage**: Consider execution delays in volatile markets
5. **Position Sizing**: Adjust based on stop distance

## 🔍 Parameter Sensitivity Analysis

High sensitivity parameters (optimize carefully):
- `base_atr_multiplier`: Directly affects risk/reward
- `atr_length`: Major impact on signal timing

Medium sensitivity parameters:
- `multiplier2`, `multiplier3`: Affect signal frequency
- `smooth_period`: Influences trend detection

Low sensitivity parameters:
- `multiplier1`: Usually keep at 1 for base timeframe

Start optimization with high sensitivity parameters first, then fine-tune the others.