# MQL & Pine Script to Python Converter

A comprehensive toolkit for converting MQL4/MQL5 and Pine Script trading indicators to self-hosted Python code. Includes complete implementation examples, testing frameworks, and optimization tools with adapter patterns.

## Featured Example: Adaptive Laguerre Filter

This repository demonstrates the conversion process with a sophisticated technical analysis indicator that provides 40-60% less lag than traditional moving averages while maintaining smooth output for reliable trend detection.

## 📁 Project Structure

```
mql-python-converter/
├── src/
│   ├── mql5/                                # Original MQL5 source files
│   │   ├── AdaptiveLaguerre_v2.mq5
│   │   └── AdaptiveLaguerre_v2_improved.mq5
│   │
│   ├── python/                              # Python conversions
│   │   ├── adaptive_laguerre_filter.py
│   │   ├── adaptive_laguerre_advanced.py
│   │   ├── test_laguerre_simple.py
│   │   └── data-ingestor/                  # Data ingestion module
│   │       ├── download_forex_data.py
│   │       └── data/                       # Market data storage
│   │           ├── gbpjpy_d1_5years.csv
│   │           └── optimization_results.json
│   │
│   ├── tools/                               # Conversion and optimization tools
│   │   ├── laguerre_optimizer.py
│   │   ├── laguerre_optimizer_simple.py
│   │   └── optimize_gbpjpy.py
│   │
│   ├── tests/                               # Test suites
│   │   ├── test_laguerre_filter.py
│   │   └── test_visual_comparison.py
│   │
│   └── examples/                            # Usage examples
│       └── example_usage.py
│
├── docs/                                    # Documentation
│   ├── AdaptiveLaguerre_Formulas.md
│   ├── adaptive_laguerre_python_docs.md
│   └── laguerre_parameter_guide.md
│
├── LICENSE
├── README.md
├── requirements.txt
└── .gitignore
```

## 🔄 Conversion Features

### MQL5 → Python
- **Complete Code Translation**: Convert MQL4/MQL5 indicators to Python
- **Mathematical Preservation**: Maintain exact calculations and formulas
- **Testing Framework**: Validate converted code against original
- **Optimization Tools**: Parameter tuning for different markets
- **Backtesting Support**: Full trading system implementation
- **Documentation Generation**: Automatic API documentation

### Pine Script → Python (NEW!)
- **Parse Pine Script v5**: Full syntax support
- **Convert to Self-Hosted Python**: Run anywhere, no TradingView lock-in
- **Technical Indicators**: All major indicators supported
- **Signal Generation**: Convert alerts to Python signals
- **Any Data Source**: Use with any broker or data feed

## 📦 Installation

### Using uv (Recommended)

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Install with optimization libraries
uv pip install -e ".[optimization]"
```

### Using pip (Legacy)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install optimization libraries
pip install -r requirements-optimization.txt
```

## 🐳 Docker Quick Start

See [DOCKER-VARIANTS.md](DOCKER-VARIANTS.md) for detailed Docker configuration options.

```bash
# Standard Python environment
docker-compose up --build

# MT4 with GUI access
docker-compose -f docker-compose-novnc.yml up --build
# Access at http://localhost:6080

# Lightweight production
docker-compose -f docker-compose.slim.yml up --build
```

## 🚀 Quick Start

### Converting Pine Script to Python
```python
from src.pinescript.pinescript_converter import convert_pinescript_to_python

# Your Pine Script code
pine_code = """
//@version=5
indicator("My Indicator", overlay=true)
fast_ma = ta.sma(close, 9)
slow_ma = ta.sma(close, 21)
plot(fast_ma, color=color.blue)
plot(slow_ma, color=color.red)
"""

# Convert to Python
python_code = convert_pinescript_to_python(pine_code)

# Now you can run it anywhere - no TradingView required!
```

### Using Converted MQL5 Indicators
```python
from src.python.adaptive_laguerre_filter import AdaptiveLaguerreFilter, SmoothMode

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

### Run Examples
```bash
# Run the example usage
python src/examples/example_usage.py

# Run tests
python src/tests/test_laguerre_filter.py

# Run optimization
python src/tools/laguerre_optimizer_simple.py

# Download forex data
python src/python/data-ingestor/download_forex_data.py

# Optimize on real data
python src/tools/optimize_gbpjpy.py
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

- **[Python API Documentation](docs/adaptive_laguerre_python_docs.md)**: Complete Python reference
- **[Parameter Guide](docs/laguerre_parameter_guide.md)**: Detailed parameter optimization
- **[Mathematical Formulas](docs/AdaptiveLaguerre_Formulas.md)**: Core equations explained

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