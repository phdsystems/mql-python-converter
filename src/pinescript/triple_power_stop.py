#!/usr/bin/env python3
"""
Triple Power Stop (CHE) - Python Conversion
Multi-timeframe stop-loss system with dynamic ATR-based stops

Converted from Pine Script v6 to self-hosted Python
Original: Triple Power Stop (CHE) indicator
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass 
class TPSConfig:
    """Triple Power Stop configuration parameters"""
    atr_length: int = 14
    base_atr_multiplier: float = 2.0
    multiplier1: int = 1
    multiplier2: int = 2
    multiplier3: int = 3
    label_count: int = 4
    smooth_period: int = 10  # SMA period for close price smoothing


class TriplePowerStop:
    """
    Triple Power Stop (CHE) Indicator
    
    Multi-timeframe stop-loss system that:
    - Calculates ATR-based stops on 3 different timeframes
    - Uses dynamic ATR multipliers based on volatility
    - Generates long/short signals when all timeframes align
    - Provides position state tracking
    """
    
    def __init__(self, config: TPSConfig = None):
        """
        Initialize Triple Power Stop
        
        Args:
            config: Configuration parameters
        """
        self.config = config or TPSConfig()
        self.reset()
        
    def reset(self):
        """Reset internal state"""
        self.htf_stop_level1 = None
        self.htf_stop_level2 = None
        self.htf_stop_level3 = None
        self.position_state = 0
        self.prev_position_state = 0
        
    def calculate_resolution(self, multiplier: int, base_timeframe: str = "1D") -> str:
        """
        Calculate resolution based on multiplier
        
        Args:
            multiplier: Timeframe multiplier
            base_timeframe: Base timeframe (e.g., "1D", "1H", "15m")
            
        Returns:
            New resolution string
        """
        # For simplification, assume daily timeframe base
        if base_timeframe.endswith("D"):
            return f"{multiplier}D"
        elif base_timeframe.endswith("H"):
            return f"{multiplier}H"
        elif base_timeframe.endswith("m"):
            base_minutes = int(base_timeframe[:-1])
            return f"{base_minutes * multiplier}m"
        else:
            return f"{multiplier}D"  # Default to daily
            
    def calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, 
                     period: int) -> np.ndarray:
        """Calculate Average True Range"""
        high_low = high - low
        high_close = np.abs(high - np.roll(close, 1))
        low_close = np.abs(low - np.roll(close, 1))
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        
        # Handle first value
        true_range[0] = high_low[0]
        
        # Calculate ATR using RMA (Recursive Moving Average)
        atr = np.zeros_like(true_range)
        atr[period-1] = np.mean(true_range[:period])
        
        for i in range(period, len(true_range)):
            atr[i] = (atr[i-1] * (period - 1) + true_range[i]) / period
            
        return atr
    
    def calculate_stdev(self, values: np.ndarray, period: int) -> np.ndarray:
        """Calculate rolling standard deviation"""
        stdev = np.zeros_like(values)
        
        for i in range(period-1, len(values)):
            window = values[i-period+1:i+1]
            stdev[i] = np.std(window, ddof=0)
            
        return stdev
    
    def calculate_sma(self, values: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average"""
        sma = np.zeros_like(values)
        
        for i in range(period-1, len(values)):
            sma[i] = np.mean(values[i-period+1:i+1])
            
        return sma
    
    def calculate_dynamic_atr_multiplier(self, base_multiplier: float, 
                                       volatility_factor: float, 
                                       atr_value: float) -> float:
        """Calculate dynamic ATR multiplier"""
        if np.isnan(volatility_factor) or np.isnan(atr_value) or atr_value == 0:
            return base_multiplier
            
        dynamic_multiplier = base_multiplier * (volatility_factor / atr_value)
        
        if np.isnan(dynamic_multiplier) or dynamic_multiplier == 0:
            return base_multiplier
            
        return dynamic_multiplier
    
    def calculate_stop_levels(self, close_price: float, atr_value: float,
                            dynamic_multiplier: float, 
                            prev_stop_level: Optional[float]) -> Tuple[float, float, float]:
        """Calculate stop levels for long/short positions"""
        long_stop = close_price - (atr_value * dynamic_multiplier)
        short_stop = close_price + (atr_value * dynamic_multiplier)
        
        if prev_stop_level is None:
            stop_level = long_stop
        else:
            if close_price > prev_stop_level:
                stop_level = max(long_stop, prev_stop_level)
            else:
                stop_level = min(short_stop, prev_stop_level)
                
        return stop_level, long_stop, short_stop
    
    def htf_calculations(self, close: np.ndarray, high: np.ndarray, 
                        low: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate higher timeframe stop levels and trends"""
        # Smooth close price
        htf_close = self.calculate_sma(close, self.config.smooth_period)
        
        # Calculate ATR
        htf_atr = self.calculate_atr(high, low, close, self.config.atr_length)
        
        # Calculate volatility factor
        volatility_factor = self.calculate_stdev(close, self.config.atr_length)
        
        # Calculate stop levels
        htf_stop_levels = np.zeros_like(close)
        is_uptrend = np.zeros_like(close, dtype=bool)
        
        prev_stop = None
        
        for i in range(len(close)):
            if i < max(self.config.atr_length, self.config.smooth_period):
                htf_stop_levels[i] = close[i]
                is_uptrend[i] = True
                continue
                
            dynamic_multiplier = self.calculate_dynamic_atr_multiplier(
                self.config.base_atr_multiplier,
                volatility_factor[i],
                htf_atr[i]
            )
            
            stop_level, _, _ = self.calculate_stop_levels(
                htf_close[i], htf_atr[i], dynamic_multiplier, prev_stop
            )
            
            htf_stop_levels[i] = stop_level
            is_uptrend[i] = htf_close[i] > stop_level
            prev_stop = stop_level
            
        return htf_stop_levels, is_uptrend
    
    def calculate(self, ohlc_data: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """
        Calculate Triple Power Stop indicator
        
        Args:
            ohlc_data: Dictionary with 'open', 'high', 'low', 'close', 'volume'
            
        Returns:
            Dictionary with stop levels, trends, and signals
        """
        close = ohlc_data['close']
        high = ohlc_data['high'] 
        low = ohlc_data['low']
        
        # For simplification, we'll simulate different timeframes by 
        # downsampling the data (in real implementation, you'd use actual timeframe data)
        
        # Calculate stop levels for all 3 timeframes
        htf_stop_level1, is_uptrend1 = self.htf_calculations(close, high, low)
        
        # For timeframe 2 (simulate 2x timeframe)
        # Sample every 2nd point to simulate higher timeframe
        step2 = max(1, self.config.multiplier2)
        close2 = close[::step2]
        high2 = high[::step2]
        low2 = low[::step2]
        
        htf_stop_2, is_up_2 = self.htf_calculations(close2, high2, low2)
        
        # Interpolate back to original length
        htf_stop_level2 = np.interp(range(len(close)), 
                                   range(0, len(close), step2), htf_stop_2)
        is_uptrend2 = np.interp(range(len(close)), 
                               range(0, len(close), step2), 
                               is_up_2.astype(float)) > 0.5
        
        # For timeframe 3 (simulate 3x timeframe)
        step3 = max(1, self.config.multiplier3)
        close3 = close[::step3]
        high3 = high[::step3] 
        low3 = low[::step3]
        
        htf_stop_3, is_up_3 = self.htf_calculations(close3, high3, low3)
        
        # Interpolate back to original length
        htf_stop_level3 = np.interp(range(len(close)), 
                                   range(0, len(close), step3), htf_stop_3)
        is_uptrend3 = np.interp(range(len(close)), 
                               range(0, len(close), step3), 
                               is_up_3.astype(float)) > 0.5
        
        # Generate trading conditions
        long_condition = is_uptrend1 & is_uptrend2 & is_uptrend3
        short_condition = ~is_uptrend1 & ~is_uptrend2 & ~is_uptrend3
        
        # Track position state
        position_states = np.zeros_like(close, dtype=int)
        position_states[0] = 0
        
        for i in range(1, len(close)):
            if long_condition[i]:
                position_states[i] = 1
            elif short_condition[i]:
                position_states[i] = -1
            else:
                position_states[i] = position_states[i-1]
        
        # Generate entry signals
        go_long = np.zeros_like(close, dtype=bool)
        go_short = np.zeros_like(close, dtype=bool)
        
        for i in range(1, len(close)):
            go_long[i] = (long_condition[i] and position_states[i] == 1 
                         and position_states[i-1] != 1)
            go_short[i] = (short_condition[i] and position_states[i] == -1 
                          and position_states[i-1] != -1)
        
        return {
            'tps_stop_level1': htf_stop_level1,
            'tps_stop_level2': htf_stop_level2,
            'tps_stop_level3': htf_stop_level3,
            'is_uptrend1': is_uptrend1,
            'is_uptrend2': is_uptrend2,
            'is_uptrend3': is_uptrend3,
            'long_condition': long_condition,
            'short_condition': short_condition,
            'position_states': position_states,
            'go_long': go_long,
            'go_short': go_short,
            'long_signals': np.sum(go_long),
            'short_signals': np.sum(go_short)
        }
    
    def calculate_single(self, ohlc_data: Dict[str, np.ndarray], 
                        index: int) -> Dict[str, Any]:
        """
        Calculate indicator for single bar (for real-time use)
        
        Args:
            ohlc_data: OHLC data up to current bar
            index: Current bar index
            
        Returns:
            Current bar indicator values
        """
        # For single bar calculation, we need enough history
        if index < max(self.config.atr_length, self.config.smooth_period):
            return {
                'tps_stop_level1': ohlc_data['close'][index],
                'tps_stop_level2': ohlc_data['close'][index],
                'tps_stop_level3': ohlc_data['close'][index],
                'is_uptrend1': True,
                'is_uptrend2': True,
                'is_uptrend3': True,
                'go_long': False,
                'go_short': False
            }
        
        # Calculate full results up to current index
        subset_data = {
            key: values[:index+1] for key, values in ohlc_data.items()
        }
        
        full_results = self.calculate(subset_data)
        
        # Return values for current bar
        return {
            key: value[index] if hasattr(value, '__getitem__') else value
            for key, value in full_results.items()
        }


# Example usage and testing
if __name__ == "__main__":
    print("🚀 Triple Power Stop (CHE) - Python Implementation")
    print("="*60)
    
    # Generate sample OHLCV data
    np.random.seed(42)
    n_bars = 500
    
    # Simulate realistic price data
    returns = np.random.randn(n_bars) * 0.01
    close_prices = 100 * np.exp(np.cumsum(returns))
    
    # Generate OHLC from close
    high_prices = close_prices * (1 + np.abs(np.random.randn(n_bars) * 0.005))
    low_prices = close_prices * (1 - np.abs(np.random.randn(n_bars) * 0.005))
    open_prices = np.roll(close_prices, 1)
    open_prices[0] = close_prices[0]
    volumes = np.random.randint(1000, 10000, n_bars)
    
    ohlc_data = {
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes
    }
    
    # Create TPS indicator with custom config
    config = TPSConfig(
        atr_length=14,
        base_atr_multiplier=2.0,
        multiplier1=1,
        multiplier2=2,
        multiplier3=3
    )
    
    tps = TriplePowerStop(config)
    
    print(f"📊 Calculating TPS for {n_bars} bars...")
    results = tps.calculate(ohlc_data)
    
    print(f"✅ Calculation complete!")
    print(f"   Long signals: {results['long_signals']}")
    print(f"   Short signals: {results['short_signals']}")
    print(f"   Final stop level 1: {results['tps_stop_level1'][-1]:.4f}")
    print(f"   Final stop level 2: {results['tps_stop_level2'][-1]:.4f}")
    print(f"   Final stop level 3: {results['tps_stop_level3'][-1]:.4f}")
    print(f"   Final trends: {results['is_uptrend1'][-1]}, {results['is_uptrend2'][-1]}, {results['is_uptrend3'][-1]}")
    
    print(f"\n📈 Last 5 signals:")
    for i in range(-5, 0):
        if results['go_long'][i]:
            print(f"   Bar {len(close_prices)+i}: LONG at {close_prices[i]:.4f}")
        elif results['go_short'][i]:
            print(f"   Bar {len(close_prices)+i}: SHORT at {close_prices[i]:.4f}")