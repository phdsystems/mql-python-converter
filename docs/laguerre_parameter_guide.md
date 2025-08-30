# Adaptive Laguerre Filter v2 - Complete Parameter Guide

## Quick Start Settings by Trading Style

| Trading Style | Length | Order | Adaptive | Smooth | Best For |
|--------------|--------|-------|----------|--------|----------|
| **Scalping** | 5-10 | 2-3 | ON | 3-5 | 1-5 min charts, quick trades |
| **Day Trading** | 10-20 | 3-4 | ON | 5-7 | 5-30 min charts, intraday |
| **Swing Trading** | 20-50 | 4-5 | ON | 7-10 | 1H-4H charts, multi-day |
| **Position Trading** | 50-100 | 4-6 | ON/OFF | 10-15 | Daily charts, long-term |

## Detailed Parameter Documentation

### 1. **TimeFrame** (ENUM_TIMEFRAMES)
- **Default:** 0 (Current chart timeframe)
- **Purpose:** Multi-timeframe analysis capability
- **Usage Tips:**
  - Set to higher timeframe to see larger trend on smaller timeframe chart
  - Example: Set to H4 on M15 chart to filter out noise
  - 0 = Use current chart timeframe (recommended for beginners)

### 2. **Price** (ENUM_APPLIED_PRICE)
- **Default:** PRICE_CLOSE
- **Options:**
  - `PRICE_CLOSE` - Most reliable for trend (recommended)
  - `PRICE_OPEN` - Less noise but may lag
  - `PRICE_HIGH/LOW` - For volatility breakout strategies
  - `PRICE_MEDIAN` - (High+Low)/2, good for ranging markets
  - `PRICE_TYPICAL` - (High+Low+Close)/3, balanced approach
  - `PRICE_WEIGHTED` - (High+Low+2*Close)/4, emphasizes close
- **Best Practice:** Use CLOSE for trend following, TYPICAL for mean reversion

### 3. **Length** (int)
- **Default:** 10
- **Range:** 3-200 (validated)
- **Impact:**
  - **Lower (3-10):** More responsive, more signals, more false signals
  - **Medium (10-30):** Balanced responsiveness and reliability
  - **Higher (30-200):** Smoother, fewer signals, more reliable trends
- **Formula Impact:** Controls lookback period for adaptive gamma calculation
- **Optimization:** Start with 10, increase if too many false signals

### 4. **Order** (int)
- **Default:** 4
- **Range:** 1-10 (validated, >6 warning)
- **Impact:**
  - **1-2:** Minimal filtering, similar to EMA
  - **3-4:** Optimal balance (recommended)
  - **5-6:** Very smooth, good for volatile markets
  - **7-10:** Risk of overshoot, use carefully
- **Technical:** Number of recursive Laguerre filter stages
- **Warning:** Orders > 6 may cause price overshoot in rapid moves

### 5. **AdaptiveMode** (bool)
- **Default:** true (ON)
- **Purpose:** Dynamically adjusts filter responsiveness
- **When ON:**
  - Filter adapts to market volatility
  - Better performance in changing conditions
  - Gamma varies between MinGamma and MaxGamma
- **When OFF:**
  - Fixed gamma = 10/(Length+9)
  - More predictable behavior
  - Better for automated systems
- **Recommendation:** Keep ON for discretionary trading

### 6. **AdaptiveSmooth** (int)
- **Default:** 5
- **Range:** 1-50 (validated)
- **Purpose:** Smooths the adaptive gamma factor
- **Impact:**
  - **1-3:** Rapid adaptation, may be jumpy
  - **4-7:** Balanced adaptation (recommended)
  - **8-15:** Slow adaptation, stable
  - **>15:** Very slow adaptation
- **Only Active When:** AdaptiveMode = true

### 7. **AdaptiveSmoothMode** (ENUM_SMOOTH_MODE)
- **Default:** 4 (Median)
- **Options:**
  - `0 - SMA`: Simple average, equal weights
  - `1 - EMA`: Exponential, recent emphasis
  - `2 - Wilder`: Smoother EMA variant
  - `3 - LWMA`: Linear weighted, gradual weights
  - `4 - Median`: Robust to outliers (recommended)
- **Best Choice:** Median for stability, EMA for responsiveness

### 8. **MinGamma** (double)
- **Default:** 0.01
- **Range:** 0.001-0.1 (validated)
- **Purpose:** Lower bound for adaptive factor
- **Impact:**
  - Lower values = More responsive minimum
  - Higher values = More filtering minimum
- **Typical Settings:**
  - Volatile markets: 0.001-0.01
  - Normal markets: 0.01-0.05
  - Stable markets: 0.05-0.1

### 9. **MaxGamma** (double)
- **Default:** 0.99
- **Range:** 0.9-0.999 (validated)
- **Purpose:** Upper bound for adaptive factor
- **Impact:**
  - Lower values = Less maximum smoothing
  - Higher values = More maximum smoothing
- **Typical Settings:**
  - Trending: 0.95-0.99
  - Ranging: 0.9-0.95
  - Mixed: 0.93-0.97

### 10. **ColorMode** (bool)
- **Default:** true (ON)
- **Visual Indicators:**
  - **Blue:** Uptrend (laguerre rising)
  - **Red:** Downtrend (laguerre falling)
  - **Silver:** Neutral/initialization
- **Usage:** Visual trend confirmation

### 11. **AlertOnTrendChange** (bool)
- **Default:** false
- **Function:** Popup/sound alert when trend changes
- **Best For:** Active monitoring, entry/exit signals
- **Note:** Only triggers once per bar

## Advanced Settings

### **UseEnhancedCalc** (bool)
- **Default:** true
- **Purpose:** Improved numerical stability
- **Benefit:** Prevents calculation errors in extreme conditions
- **Cost:** Slightly more CPU usage (negligible)

### **MinBarsRequired** (int)
- **Default:** 100
- **Range:** 50-500
- **Purpose:** Ensures enough data for reliable calculations
- **Impact:** Prevents false signals during initialization

### **DebugMode** (bool)
- **Default:** false
- **Purpose:** Prints diagnostic information
- **Use When:** Troubleshooting or optimizing parameters

## Parameter Optimization Strategy

### Step 1: Choose Base Settings
1. Select your trading style preset
2. Apply to your preferred timeframe
3. Use default Price (CLOSE)

### Step 2: Fine-Tune Length
1. Start with preset value
2. Increase if too many false signals
3. Decrease if missing opportunities
4. Test on 100+ historical trades

### Step 3: Adjust Order
1. Keep at 3-4 for most cases
2. Increase to 5-6 only for very volatile pairs
3. Never exceed 6 unless absolutely necessary

### Step 4: Optimize Adaptive Settings
1. Keep AdaptiveMode ON
2. Adjust AdaptiveSmooth based on timeframe:
   - M1-M5: 3-5
   - M15-H1: 5-8
   - H4-D1: 8-12
3. Use Median smoothing mode for stability

### Step 5: Set Gamma Bounds
1. Wider range (0.01-0.99) for varying markets
2. Narrower range for consistent markets
3. Test with historical data

## Common Parameter Combinations

### Conservative (Few signals, high reliability)
```
Length: 50
Order: 5
AdaptiveMode: true
AdaptiveSmooth: 10
MinGamma: 0.05
MaxGamma: 0.95
```

### Balanced (Moderate signals, good reliability)
```
Length: 20
Order: 4
AdaptiveMode: true
AdaptiveSmooth: 7
MinGamma: 0.02
MaxGamma: 0.98
```

### Aggressive (Many signals, lower reliability)
```
Length: 7
Order: 3
AdaptiveMode: true
AdaptiveSmooth: 3
MinGamma: 0.005
MaxGamma: 0.99
```

## Performance Impact

| Parameter | CPU Impact | Memory Impact | Signal Quality Impact |
|-----------|------------|---------------|---------------------|
| Length ↑ | Low | Low | Higher quality, fewer signals |
| Order ↑ | Medium | Low | Smoother, potential overshoot |
| AdaptiveMode ON | Medium | Low | Better adaptation |
| AdaptiveSmooth ↑ | Low | Low | More stable gamma |
| Enhanced Calc ON | Low | None | Better stability |

## Troubleshooting Guide

| Problem | Solution |
|---------|----------|
| Too many false signals | Increase Length, increase AdaptiveSmooth |
| Missing trend changes | Decrease Length, decrease Order |
| Indicator overshoots price | Reduce Order to 3-4 |
| Choppy indicator line | Increase Order or AdaptiveSmooth |
| Indicator lags too much | Decrease Length, enable AdaptiveMode |
| Alerts too frequent | Increase Length, check timeframe |

## Best Practices

1. **Always backtest** parameter changes on at least 100 trades
2. **Start conservative** and gradually become more aggressive
3. **Match parameters to market conditions** (trending vs ranging)
4. **Use higher timeframes** for confirmation
5. **Combine with other indicators** for confirmation
6. **Document your settings** for different market conditions
7. **Re-optimize quarterly** as market dynamics change

## Warning Notes

⚠️ **Order > 6**: May cause instability and overshoot
⚠️ **Length < 5**: Very sensitive, many false signals
⚠️ **MinGamma >= MaxGamma**: Will cause calculation errors
⚠️ **Extreme gamma values**: May cause erratic behavior
⚠️ **Insufficient bars**: Wait for MinBarsRequired before trading