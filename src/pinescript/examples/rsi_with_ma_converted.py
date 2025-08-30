"""
RSI with MA
Self-hosted Python implementation (converted from Pine Script)
"""

import numpy as np

class RsiWithMa:
    """RSI with Moving Average - runs anywhere!"""
    
    def __init__(self, rsi_period=14, ma_period=9, overbought=70, oversold=30):
        self.rsi_period = rsi_period
        self.ma_period = ma_period
        self.overbought = overbought
        self.oversold = oversold
    
    def calculate(self, prices):
        """Calculate RSI and MA"""
        # Calculate RSI
        delta = np.diff(prices, prepend=prices[0])
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        # RMA (Wilder's smoothing)
        avg_gain = self._rma(gain, self.rsi_period)
        avg_loss = self._rma(loss, self.rsi_period)
        
        # RSI calculation
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        # MA of RSI
        rsi_ma = np.convolve(rsi, np.ones(self.ma_period)/self.ma_period, mode='same')
        
        # Signals
        buy_signal = self._crossover(rsi, self.oversold)
        sell_signal = self._crossunder(rsi, self.overbought)
        
        return {
            'rsi': rsi,
            'rsi_ma': rsi_ma,
            'buy_signal': buy_signal,
            'sell_signal': sell_signal
        }
    
    def _rma(self, series, period):
        """Running Moving Average"""
        alpha = 1 / period
        rma = np.zeros_like(series)
        rma[0] = series[0]
        for i in range(1, len(series)):
            rma[i] = alpha * series[i] + (1 - alpha) * rma[i-1]
        return rma
    
    def _crossover(self, series, level):
        """Detect crossover above level"""
        if isinstance(level, (int, float)):
            level = np.full_like(series, level)
        return (series > level) & (np.roll(series, 1) <= level)
    
    def _crossunder(self, series, level):
        """Detect crossunder below level"""
        if isinstance(level, (int, float)):
            level = np.full_like(series, level)
        return (series < level) & (np.roll(series, 1) >= level)

# Example usage
if __name__ == "__main__":
    # Generate sample data
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    # Create indicator
    indicator = RsiWithMa()
    
    # Calculate
    results = indicator.calculate(prices)
    
    # Display results
    print(f"RSI: {results['rsi'][-5:]}")
    print(f"Signals: {sum(results['buy_signal'])} buys, {sum(results['sell_signal'])} sells")
