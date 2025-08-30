"""
Adaptive Laguerre Filter - Python Implementation
Converted from MQL5 to Python
Author: Based on TrendLaboratory's AdaptiveLaguerre_v2.mq5
"""

import numpy as np
import pandas as pd
from enum import Enum
from typing import Optional, Union, Tuple
import warnings

class SmoothMode(Enum):
    """Smoothing modes for adaptive factor"""
    SMA = 0
    EMA = 1
    WILDER = 2
    LWMA = 3
    MEDIAN = 4

class AdaptiveLaguerreFilter:
    """
    Adaptive Laguerre Filter implementation for technical analysis.
    
    The Laguerre filter is a smoothing filter that provides less lag than 
    traditional moving averages while maintaining smooth output.
    """
    
    def __init__(self, 
                 length: int = 10,
                 order: int = 4,
                 adaptive_mode: bool = True,
                 adaptive_smooth: int = 5,
                 adaptive_smooth_mode: SmoothMode = SmoothMode.MEDIAN):
        """
        Initialize the Adaptive Laguerre Filter.
        
        Parameters:
        -----------
        length : int
            Period for calculations (default: 10)
        order : int
            Laguerre filter order - higher values provide more smoothing (default: 4)
        adaptive_mode : bool
            Enable/disable adaptive mode (default: True)
        adaptive_smooth : int
            Adaptive factor smoothing period (default: 5)
        adaptive_smooth_mode : SmoothMode
            Smoothing mode for adaptive factor (default: MEDIAN)
        """
        self.length = length
        self.order = order
        self.adaptive_mode = adaptive_mode
        self.adaptive_smooth = adaptive_smooth
        self.adaptive_smooth_mode = adaptive_smooth_mode
        
        # Initialize internal buffers
        self.L = np.zeros((order, 2))  # Laguerre coefficients [current, previous]
        self.ema_buffer = np.zeros(2)
        self.ema_initialized = False
        
    def calculate(self, prices: Union[list, np.ndarray, pd.Series]) -> dict:
        """
        Calculate the Adaptive Laguerre Filter for given prices.
        
        Parameters:
        -----------
        prices : array-like
            Input price series
            
        Returns:
        --------
        dict : Dictionary containing:
            - 'laguerre': Filtered values
            - 'trend': Trend direction (1=up, 2=down, 0=neutral)
            - 'gamma': Adaptive gamma values (if adaptive mode is on)
        """
        prices = np.asarray(prices)
        n = len(prices)
        
        # Initialize output arrays
        laguerre = np.full(n, np.nan)
        trend = np.zeros(n)
        gamma_values = np.full(n, np.nan)
        diff = np.full(n, np.nan)
        
        # Calculate for each point
        for i in range(n):
            # Skip if not enough data
            if i < self.length:
                continue
                
            # Calculate difference for adaptive mode
            if i > 0:
                diff[i] = abs(prices[i] - laguerre[i-1]) if not np.isnan(laguerre[i-1]) else 0
            
            # Skip if not enough data for calculations
            if i < 2 * self.length:
                continue
            
            # Calculate gamma (adaptive or fixed)
            if self.adaptive_mode:
                # Calculate adaptive gamma based on efficiency ratio
                gamma = self._calculate_adaptive_gamma(diff, i)
                
                # Smooth the gamma value
                if self.adaptive_smooth_mode == SmoothMode.SMA:
                    gamma = self._sma(gamma_values, self.adaptive_smooth, i)
                elif self.adaptive_smooth_mode == SmoothMode.EMA:
                    gamma = self._ema(gamma, self.adaptive_smooth, i)
                elif self.adaptive_smooth_mode == SmoothMode.WILDER:
                    gamma = self._ema(gamma, 2 * self.adaptive_smooth - 1, i)
                elif self.adaptive_smooth_mode == SmoothMode.LWMA:
                    gamma = self._lwma(gamma_values, self.adaptive_smooth, i)
                elif self.adaptive_smooth_mode == SmoothMode.MEDIAN:
                    gamma = self._median(gamma_values, self.adaptive_smooth, i)
                
                gamma_values[i] = gamma
            else:
                # Fixed gamma
                gamma = 10.0 / (self.length + 9)
                gamma_values[i] = gamma
            
            # Calculate Laguerre filter value
            laguerre[i] = self._laguerre_filter(prices[i], gamma, i)
            
            # Calculate trend direction
            if i > self.length + 2 and i > 0:
                if not np.isnan(laguerre[i-1]) and laguerre[i-1] > 0:
                    trend[i] = trend[i-1]  # Maintain previous trend
                    if laguerre[i] > laguerre[i-1]:
                        trend[i] = 1  # Uptrend
                    elif laguerre[i] < laguerre[i-1]:
                        trend[i] = 2  # Downtrend
        
        return {
            'laguerre': laguerre,
            'trend': trend,
            'gamma': gamma_values
        }
    
    def _laguerre_filter(self, price: float, gamma: float, bar: int) -> float:
        """
        Calculate the Laguerre filter value.
        
        Parameters:
        -----------
        price : float
            Current price
        gamma : float
            Gamma parameter (0 < gamma < 1)
        bar : int
            Current bar index
            
        Returns:
        --------
        float : Filtered value
        """
        gam = 1 - gamma
        
        # Update previous values
        self.L[:, 1] = self.L[:, 0]
        
        # Calculate Laguerre coefficients
        array = np.zeros(self.order)
        
        for i in range(self.order):
            if bar <= self.order:
                self.L[i, 0] = price
            else:
                if i == 0:
                    self.L[i, 0] = (1 - gam) * price + gam * self.L[i, 1]
                else:
                    self.L[i, 0] = -gam * self.L[i-1, 0] + self.L[i-1, 1] + gam * self.L[i, 1]
            
            array[i] = self.L[i, 0]
        
        # Apply triangular moving average to coefficients
        return self._trima_gen(array, self.order)
    
    def _calculate_adaptive_gamma(self, diff: np.ndarray, bar: int) -> float:
        """
        Calculate adaptive gamma based on efficiency ratio.
        
        Parameters:
        -----------
        diff : np.ndarray
            Array of price differences
        bar : int
            Current bar index
            
        Returns:
        --------
        float : Adaptive gamma value
        """
        if bar < self.length:
            return 0
        
        # Find min and max over the period
        start_idx = max(0, bar - self.length + 1)
        period_diff = diff[start_idx:bar + 1]
        
        # Remove NaN values
        valid_diff = period_diff[~np.isnan(period_diff)]
        
        if len(valid_diff) == 0:
            return 0
        
        max_diff = np.max(valid_diff)
        min_diff = np.min(valid_diff)
        
        # Calculate efficiency ratio
        if max_diff - min_diff != 0:
            eff = (diff[bar] - min_diff) / (max_diff - min_diff)
        else:
            eff = 0
        
        return eff
    
    def _sma(self, array: np.ndarray, period: int, bar: int) -> float:
        """Simple Moving Average"""
        if bar < period - 1:
            return 0
        
        start_idx = bar - period + 1
        values = array[start_idx:bar + 1]
        valid_values = values[~np.isnan(values)]
        
        if len(valid_values) == 0:
            return 0
        
        return np.mean(valid_values)
    
    def _ema(self, price: float, period: int, bar: int) -> float:
        """Exponential Moving Average"""
        if not self.ema_initialized:
            self.ema_buffer[0] = price
            self.ema_initialized = True
        else:
            alpha = 2.0 / (1 + period)
            self.ema_buffer[0] = self.ema_buffer[1] + alpha * (price - self.ema_buffer[1])
        
        self.ema_buffer[1] = self.ema_buffer[0]
        return self.ema_buffer[0]
    
    def _lwma(self, array: np.ndarray, period: int, bar: int) -> float:
        """Linear Weighted Moving Average"""
        if bar < period - 1:
            return 0
        
        weight_sum = 0
        value_sum = 0
        
        for i in range(period):
            idx = bar - i
            if idx >= 0 and not np.isnan(array[idx]):
                weight = period - i
                weight_sum += weight
                value_sum += array[idx] * weight
        
        if weight_sum > 0:
            return value_sum / weight_sum
        return 0
    
    def _median(self, array: np.ndarray, period: int, bar: int) -> float:
        """Moving Median"""
        if bar < period - 1:
            return 0
        
        start_idx = bar - period + 1
        values = array[start_idx:bar + 1]
        valid_values = values[~np.isnan(values)]
        
        if len(valid_values) == 0:
            return 0
        
        return np.median(valid_values)
    
    def _trima_gen(self, array: np.ndarray, period: int) -> float:
        """Triangular Moving Average Generalized"""
        len1 = int(np.floor((period + 1) * 0.5))
        len2 = int(np.ceil((period + 1) * 0.5))
        
        sum_val = 0
        for i in range(len2):
            # Simple average of the array subset
            if i < len(array):
                subset = array[max(0, len(array) - len1 - i):len(array) - i]
                if len(subset) > 0:
                    sum_val += np.mean(subset)
        
        if len2 > 0:
            return sum_val / len2
        return 0


def calculate_signals(laguerre_data: dict) -> pd.DataFrame:
    """
    Generate trading signals from Laguerre filter output.
    
    Parameters:
    -----------
    laguerre_data : dict
        Output from AdaptiveLaguerreFilter.calculate()
        
    Returns:
    --------
    pd.DataFrame : DataFrame with signals
    """
    df = pd.DataFrame(laguerre_data)
    
    # Generate signals based on trend changes
    df['signal'] = 0
    df.loc[df['trend'] == 1, 'signal'] = 1  # Buy signal
    df.loc[df['trend'] == 2, 'signal'] = -1  # Sell signal
    
    # Mark trend changes
    df['trend_change'] = df['trend'].diff() != 0
    
    return df


# Example usage
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    
    # Generate sample price data (sine wave with noise for demonstration)
    np.random.seed(42)
    n_points = 200
    t = np.linspace(0, 4 * np.pi, n_points)
    
    # Create price series with trend and noise
    trend = 100 + t * 2
    cycle = 10 * np.sin(t)
    noise = np.random.normal(0, 2, n_points)
    prices = trend + cycle + noise
    
    # Calculate Adaptive Laguerre Filter
    alf = AdaptiveLaguerreFilter(
        length=10,
        order=4,
        adaptive_mode=True,
        adaptive_smooth=5,
        adaptive_smooth_mode=SmoothMode.MEDIAN
    )
    
    result = alf.calculate(prices)
    
    # Create signals DataFrame
    signals_df = calculate_signals(result)
    
    # Plotting
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # Plot 1: Price and Laguerre Filter
    ax1 = axes[0]
    ax1.plot(prices, label='Price', alpha=0.7, color='gray')
    ax1.plot(result['laguerre'], label='Adaptive Laguerre', linewidth=2, color='blue')
    
    # Mark buy/sell points
    buy_signals = signals_df[signals_df['signal'] == 1].index
    sell_signals = signals_df[signals_df['signal'] == -1].index
    
    if len(buy_signals) > 0:
        ax1.scatter(buy_signals, prices[buy_signals], color='green', marker='^', 
                   s=100, label='Buy Signal', zorder=5)
    if len(sell_signals) > 0:
        ax1.scatter(sell_signals, prices[sell_signals], color='red', marker='v', 
                   s=100, label='Sell Signal', zorder=5)
    
    ax1.set_title('Adaptive Laguerre Filter')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Price')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Trend Direction
    ax2 = axes[1]
    ax2.plot(result['trend'], label='Trend (1=Up, 2=Down)', color='purple')
    ax2.fill_between(range(len(result['trend'])), 0, result['trend'], 
                     where=(result['trend'] == 1), color='green', alpha=0.3, label='Uptrend')
    ax2.fill_between(range(len(result['trend'])), 0, result['trend'], 
                     where=(result['trend'] == 2), color='red', alpha=0.3, label='Downtrend')
    ax2.set_title('Trend Direction')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Trend')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Adaptive Gamma
    ax3 = axes[2]
    ax3.plot(result['gamma'], label='Adaptive Gamma', color='orange')
    ax3.set_title('Adaptive Gamma Values')
    ax3.set_xlabel('Time')
    ax3.set_ylabel('Gamma')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/home/developer/adaptive_laguerre_plot.png', dpi=100)
    plt.show()
    
    # Print statistics
    print("\nAdaptive Laguerre Filter Statistics:")
    print("-" * 40)
    print(f"Total data points: {n_points}")
    print(f"Valid filter values: {(~np.isnan(result['laguerre'])).sum()}")
    print(f"Buy signals: {(signals_df['signal'] == 1).sum()}")
    print(f"Sell signals: {(signals_df['signal'] == -1).sum()}")
    print(f"Average gamma: {np.nanmean(result['gamma']):.4f}")
    print(f"Gamma std dev: {np.nanstd(result['gamma']):.4f}")