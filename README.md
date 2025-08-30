# MQL to Python Converter

A comprehensive toolkit for converting MQL4/MQL5 trading indicators and strategies to Python. Includes complete implementation examples, testing frameworks, and optimization tools.

## Featured Example: Adaptive Laguerre Filter

This repository demonstrates the conversion process with a sophisticated technical analysis indicator that provides 40-60% less lag than traditional moving averages while maintaining smooth output for reliable trend detection.

## 📁 Project Structure

```
mql-python-converter/
├── MQL5 Source Files
│   ├── AdaptiveLaguerre_v2.mq5              # Original MQL5 indicator
│   └── AdaptiveLaguerre_v2_improved.mq5     # Enhanced version with validation
│
├── Python Conversions
│   ├── adaptive_laguerre_filter.py          # Converted Python implementation
│   ├── adaptive_laguerre_advanced.py        # Extended with backtesting
│   └── test_laguerre_simple.py              # Standalone version (no dependencies)
│
├── Conversion Tools
│   ├── laguerre_optimizer.py                # Parameter optimization framework
│   ├── laguerre_optimizer_simple.py         # Simplified optimizer
│   └── optimize_gbpjpy.py                   # Real data optimization example
│
├── Testing Framework
│   ├── test_laguerre_filter.py              # Comprehensive test suite
│   ├── test_visual_comparison.py            # Visual comparison tools
│   └── download_forex_data.py               # Market data downloader
│
├── Documentation
│   ├── AdaptiveLaguerre_Formulas.md         # Mathematical formulas
│   ├── adaptive_laguerre_python_docs.md     # Python API documentation
│   └── laguerre_parameter_guide.md          # Parameter optimization guide
│
└── README.md                                 # This file
```

## 🔄 MQL to Python Conversion Features

- **Complete Code Translation**: Convert MQL4/MQL5 indicators to Python
- **Mathematical Preservation**: Maintain exact calculations and formulas
- **Testing Framework**: Validate converted code against original
- **Optimization Tools**: Parameter tuning for different markets
- **Backtesting Support**: Full trading system implementation
- **Documentation Generation**: Automatic API documentation

## 🚀 Quick Start

### Python Version
```python
from adaptive_laguerre_filter import AdaptiveLaguerreFilter, SmoothMode

# Create filter
alf = AdaptiveLaguerreFilter(
    length=10,
    order=4,
    adaptive_mode=True
)

# Calculate on prices
result = alf.calculate(price_data)
filtered = result['laguerre']
trend = result['trend']  # 1=up, 2=down
```

### MQL5 Version
1. Copy `AdaptiveLaguerre_v2_improved.mq5` to MetaTrader 5 Indicators folder
2. Compile in MetaEditor
3. Add to chart with desired parameters

## 📊 Key Features

- **Adaptive Mode**: Dynamically adjusts to market volatility
- **Multi-Timeframe**: Display higher timeframe calculations on lower charts
- **Low Lag**: 40-60% less lag than traditional moving averages
- **Smooth Output**: Reduces false signals while maintaining responsiveness
- **Trading Presets**: Optimized settings for different trading styles
- **Backtesting**: Complete Python backtesting framework included

## 📈 Performance Characteristics

| Metric | Value |
|--------|-------|
| Lag Reduction | 40-60% vs SMA |
| Smoothness | High (adjustable) |
| Responsiveness | Adaptive |
| False Signals | Low with proper settings |
| CPU Usage | Moderate |

## 🎯 Trading Applications

1. **Trend Following**: Identify and follow market trends
2. **Entry/Exit Signals**: Color changes indicate trend shifts
3. **Multi-Timeframe Analysis**: Confirm signals across timeframes
4. **Volatility Adaptation**: Automatically adjusts to market conditions
5. **Risk Management**: Clear trend identification for position sizing

## 📚 Documentation

- **[Python API Documentation](adaptive_laguerre_python_docs.md)**: Complete Python reference
- **[Parameter Guide](laguerre_parameter_guide.md)**: Detailed parameter optimization
- **[Mathematical Formulas](AdaptiveLaguerre_Formulas.md)**: Core equations explained

## 🔧 Recommended Settings

| Trading Style | Length | Order | Adaptive | Timeframe |
|--------------|--------|-------|----------|-----------|
| Scalping | 5-10 | 2-3 | ON | 1-5 min |
| Day Trading | 10-20 | 3-4 | ON | 15-30 min |
| Swing Trading | 20-50 | 4-5 | ON | 1-4 hour |
| Position Trading | 50-100 | 4-6 | ON/OFF | Daily |

## 💡 Tips for Success

1. **Start Conservative**: Begin with higher length values and decrease gradually
2. **Confirm Signals**: Use with other indicators for confirmation
3. **Respect the Trend**: Don't fight strong trends indicated by the filter
4. **Adjust to Volatility**: Increase smoothing in volatile markets
5. **Backtest Thoroughly**: Test parameters on historical data before live trading

## ⚠️ Important Notes

- Requires minimum 2×Length bars for calculation
- Order values > 6 may cause overshoot
- Always validate parameters before use
- Not suitable as sole trading signal

## 🔄 Version History

- **v2.1** (Improved): Added parameter validation, presets, and enhanced documentation
- **v2.0** (Original): Core Adaptive Laguerre implementation
- **Python Port**: Full feature parity with MQL5 plus backtesting

## 📝 License

Based on original work by TrendLaboratory (2012)
Enhanced documentation and Python implementation added

## 🤝 Contributing

Improvements and optimizations welcome. Key areas:
- Additional smoothing algorithms
- Performance optimization
- Real-time data integration
- Machine learning parameter optimization

## 📞 Support

For questions or issues:
- Review documentation files
- Check parameter guide for troubleshooting
- Test with simplified parameters first

---

*The Adaptive Laguerre Filter provides professional-grade trend analysis with minimal lag and maximum reliability when properly configured.*