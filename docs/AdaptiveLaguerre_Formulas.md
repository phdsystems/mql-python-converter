# Adaptive Laguerre Filter - Mathematical Formulas Documentation

## 1. Main Laguerre Filter Formula

The core Laguerre filter is a recursive filter with order `n`:

### Laguerre Coefficients Calculation
For each order level `i` from 0 to `order-1`:

```
γ (gamma) = adaptive factor or fixed value
gam = 1 - γ

For i = 0:
    L[0] = (1 - gam) × price + gam × L[0]_prev
    
For i > 0:
    L[i] = -gam × L[i-1] + L[i-1]_prev + gam × L[i]_prev
```

Where:
- `L[i]` is the current Laguerre coefficient at level i
- `L[i]_prev` is the previous Laguerre coefficient at level i
- `price` is the current input price

### Final Filter Output
The final Laguerre filter value is calculated using a Triangular Moving Average (TriMA) of all coefficients:
```
Laguerre = TriMA_gen(L[], order, order-1)
```

## 2. Adaptive Gamma Calculation

When AdaptiveMode is enabled, gamma is calculated dynamically:

### Efficiency Ratio (Adaptive Factor)
```
eff = (current_diff - min_diff) / (max_diff - min_diff)
```

Where:
- `current_diff = |price - laguerre_prev|`
- `min_diff` = minimum difference over `Length` periods
- `max_diff` = maximum difference over `Length` periods
- If `max_diff = min_diff`, then `eff = 0`

### Smoothed Gamma
The efficiency ratio is then smoothed using one of several methods:
- **SMA**: Simple Moving Average
- **EMA**: Exponential Moving Average  
- **Wilder**: Wilder's smoothing (EMA with period × 2 - 1)
- **LWMA**: Linear Weighted Moving Average
- **Median**: Moving Median

### Fixed Gamma (Non-Adaptive Mode)
When AdaptiveMode is disabled:
```
γ = 10 / (Length + 9)
```

## 3. Moving Average Formulas

### Simple Moving Average (SMA)
```
SMA = Σ(price[i]) / period
```
Where i goes from 0 to period-1

### Exponential Moving Average (EMA)
```
α = 2 / (period + 1)
EMA = EMA_prev + α × (price - EMA_prev)
```

### Linear Weighted Moving Average (LWMA)
```
LWMA = Σ(price[i] × weight[i]) / Σ(weight[i])
```
Where:
- `weight[i] = period - i`
- i goes from 0 to period-1

### Triangular Moving Average Generalized (TriMA_gen)
```
len1 = floor((period + 1) / 2)
len2 = ceil((period + 1) / 2)

TriMA = Σ(SMA(array, len1, bar-i)) / len2
```
Where i goes from 0 to len2-1

### Moving Median
```
Median = middle value of sorted array (for odd period)
Median = average of two middle values (for even period)
```

## 4. Trend Direction Calculation

The trend direction for coloring is determined by:
```
if (laguerre[current] > laguerre[previous]):
    trend = 1 (uptrend - DeepSkyBlue)
    
elif (laguerre[current] < laguerre[previous]):
    trend = 2 (downtrend - OrangeRed)
    
else:
    trend = previous_trend (no change - maintains color)
```

## 5. Multi-Timeframe (MTF) Handling

When using a higher timeframe:
```
MTF_Value = iCustom(TimeFrame, "AdaptiveLaguerre_v2", parameters...)
```
The indicator recursively calls itself on the higher timeframe and maps values to the current chart.

## 6. Key Mathematical Properties

### Lag Reduction
The Laguerre filter achieves lag reduction through:
1. **Recursive filtering**: Each level uses information from the previous level
2. **Adaptive gamma**: Adjusts responsiveness based on market conditions
3. **Higher-order filtering**: Multiple levels provide better frequency response

### Filter Order Impact
- **Order = 1**: Simple exponential-like behavior
- **Order = 2-4**: Balanced smoothing and responsiveness (recommended)
- **Order > 4**: Increased smoothing but potential overshoot

### Gamma Parameter Range
- **γ ∈ (0, 1)**: Valid range for stable filtering
- **γ → 0**: More responsive (less smoothing)
- **γ → 1**: More smoothing (less responsive)
- **Typical adaptive range**: 0.05 to 0.95

## 7. Implementation Details

### Buffer Initialization
```
if (bar <= order):
    L[i] = price  (for all i)
```

### Calculation Flow
1. Calculate price difference: `diff = |price - laguerre_prev|`
2. Compute adaptive gamma (if enabled)
3. Smooth the gamma value
4. Apply Laguerre filter recursion
5. Calculate final output using TriMA
6. Determine trend direction for coloring

## 8. Practical Interpretation

### Signal Generation
- **Bullish Signal**: Laguerre line turns blue (uptrend)
- **Bearish Signal**: Laguerre line turns orange (downtrend)
- **Trend Strength**: Steeper slope indicates stronger trend

### Advantages Over Traditional MAs
1. **Reduced Lag**: ~40-60% less lag than equivalent SMA
2. **Smoother Output**: Less whipsaws in ranging markets
3. **Adaptive Response**: Automatically adjusts to market volatility
4. **Multi-level Filtering**: Better noise reduction

### Optimal Settings
- **Trending Markets**: Length=10-20, Order=3-4, Adaptive=ON
- **Ranging Markets**: Length=20-50, Order=4-6, Adaptive=ON
- **Scalping**: Length=5-10, Order=2-3, Adaptive=ON
- **Position Trading**: Length=50-100, Order=4-5, Adaptive=OFF