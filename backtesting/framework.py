#!/usr/bin/env python3
"""
MQL4 to Python Backtesting Framework
Provides tools for validating converted MQL4 indicators in Python
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import struct
from pathlib import Path


@dataclass
class MT4Bar:
    """Represents a single MT4 bar/candle"""
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    

class MT4HistoryReader:
    """Reads MT4 .hst history files"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.header = {}
        self.bars = []
        
    def read_header(self, file_handle):
        """Read MT4 history file header (148 bytes)"""
        # Version - 4 bytes
        self.header['version'] = struct.unpack('<I', file_handle.read(4))[0]
        
        # Copyright - 64 bytes
        self.header['copyright'] = file_handle.read(64).decode('ascii', 'ignore').strip('\x00')
        
        # Symbol - 12 bytes
        self.header['symbol'] = file_handle.read(12).decode('ascii', 'ignore').strip('\x00')
        
        # Period (timeframe in minutes) - 4 bytes
        self.header['period'] = struct.unpack('<I', file_handle.read(4))[0]
        
        # Digits (decimal places) - 4 bytes
        self.header['digits'] = struct.unpack('<I', file_handle.read(4))[0]
        
        # Timesign - 4 bytes
        self.header['timesign'] = struct.unpack('<I', file_handle.read(4))[0]
        
        # Last sync - 4 bytes
        self.header['last_sync'] = struct.unpack('<I', file_handle.read(4))[0]
        
        # Unused - 52 bytes
        file_handle.read(52)
        
    def read_bars(self, file_handle):
        """Read all bars from history file"""
        bars = []
        
        while True:
            # Each bar is 60 bytes for version 401
            bar_data = file_handle.read(60)
            if len(bar_data) < 60:
                break
                
            # Parse bar structure
            time = struct.unpack('<I', bar_data[0:4])[0]
            open_price = struct.unpack('<d', bar_data[4:12])[0]
            high = struct.unpack('<d', bar_data[12:20])[0]
            low = struct.unpack('<d', bar_data[20:28])[0]
            close = struct.unpack('<d', bar_data[28:36])[0]
            volume = struct.unpack('<Q', bar_data[36:44])[0]
            
            bar = MT4Bar(
                time=datetime.fromtimestamp(time),
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume
            )
            bars.append(bar)
            
        return bars
    
    def load(self) -> pd.DataFrame:
        """Load history file and return as DataFrame"""
        with open(self.file_path, 'rb') as f:
            self.read_header(f)
            self.bars = self.read_bars(f)
            
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'time': bar.time,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume
            }
            for bar in self.bars
        ])
        
        if not df.empty:
            df.set_index('time', inplace=True)
            
        return df
    
    def get_info(self) -> Dict:
        """Get history file information"""
        return {
            'symbol': self.header.get('symbol'),
            'period': self.header.get('period'),
            'digits': self.header.get('digits'),
            'bar_count': len(self.bars),
            'date_range': (
                self.bars[0].time if self.bars else None,
                self.bars[-1].time if self.bars else None
            )
        }


class IndicatorBase:
    """Base class for Python indicators"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.results = {}
        
    def calculate(self):
        """Calculate indicator values - to be implemented by subclasses"""
        raise NotImplementedError
        
    def get_signals(self) -> pd.Series:
        """Get trading signals - to be implemented by subclasses"""
        raise NotImplementedError


class SimpleMA(IndicatorBase):
    """Python implementation of SimpleMA_Test.mq4"""
    
    def __init__(self, data: pd.DataFrame, fast_period: int = 10, slow_period: int = 20, 
                 ma_method: str = 'SMA', applied_price: str = 'close'):
        super().__init__(data)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.ma_method = ma_method
        self.applied_price = applied_price
        
    def calculate(self):
        """Calculate moving averages"""
        price_series = self.data[self.applied_price]
        
        if self.ma_method == 'SMA':
            self.results['fast_ma'] = price_series.rolling(window=self.fast_period).mean()
            self.results['slow_ma'] = price_series.rolling(window=self.slow_period).mean()
        elif self.ma_method == 'EMA':
            self.results['fast_ma'] = price_series.ewm(span=self.fast_period, adjust=False).mean()
            self.results['slow_ma'] = price_series.ewm(span=self.slow_period, adjust=False).mean()
        else:
            raise ValueError(f"Unsupported MA method: {self.ma_method}")
            
        return self.results
    
    def get_crossover_signals(self) -> pd.Series:
        """
        Get crossover signals
        Returns: 1 for bullish crossover, -1 for bearish crossover, 0 for no signal
        """
        if 'fast_ma' not in self.results:
            self.calculate()
            
        fast_ma = self.results['fast_ma']
        slow_ma = self.results['slow_ma']
        
        # Calculate crossovers
        signals = pd.Series(0, index=self.data.index)
        
        # Fast MA crosses above Slow MA (bullish)
        bullish = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
        signals[bullish] = 1
        
        # Fast MA crosses below Slow MA (bearish)
        bearish = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))
        signals[bearish] = -1
        
        return signals


class BacktestEngine:
    """Simple backtesting engine for strategy validation"""
    
    def __init__(self, data: pd.DataFrame, initial_balance: float = 10000):
        self.data = data
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
    def run_strategy(self, signals: pd.Series, position_size: float = 0.1):
        """
        Run backtest with given signals
        signals: Series with 1 (buy), -1 (sell), 0 (hold)
        position_size: Fraction of balance to use per trade
        """
        position = None
        
        for timestamp, signal in signals.items():
            if timestamp not in self.data.index:
                continue
                
            current_price = self.data.loc[timestamp, 'close']
            
            # Open position
            if signal == 1 and position is None:  # Buy signal
                position = {
                    'type': 'long',
                    'entry_time': timestamp,
                    'entry_price': current_price,
                    'size': self.balance * position_size / current_price
                }
                
            elif signal == -1 and position is None:  # Sell signal
                position = {
                    'type': 'short',
                    'entry_time': timestamp,
                    'entry_price': current_price,
                    'size': self.balance * position_size / current_price
                }
                
            # Close position on opposite signal
            elif position is not None:
                if (position['type'] == 'long' and signal == -1) or \
                   (position['type'] == 'short' and signal == 1):
                    # Calculate P&L
                    if position['type'] == 'long':
                        pnl = (current_price - position['entry_price']) * position['size']
                    else:
                        pnl = (position['entry_price'] - current_price) * position['size']
                    
                    self.balance += pnl
                    
                    # Record trade
                    self.trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': timestamp,
                        'type': position['type'],
                        'entry_price': position['entry_price'],
                        'exit_price': current_price,
                        'pnl': pnl,
                        'return': pnl / (position['entry_price'] * position['size'])
                    })
                    
                    position = None
            
            # Record equity
            self.equity_curve.append({
                'time': timestamp,
                'balance': self.balance
            })
    
    def get_statistics(self) -> Dict:
        """Calculate backtest statistics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'sharpe_ratio': 0
            }
        
        trades_df = pd.DataFrame(self.trades)
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] < 0]
        
        total_return = (self.balance - self.initial_balance) / self.initial_balance
        
        # Calculate Sharpe ratio (simplified)
        if len(trades_df) > 1:
            returns = trades_df['return'].values
            sharpe = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe = 0
        
        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(self.trades) if self.trades else 0,
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'final_balance': self.balance,
            'max_win': winning_trades['pnl'].max() if len(winning_trades) > 0 else 0,
            'max_loss': losing_trades['pnl'].min() if len(losing_trades) > 0 else 0,
            'avg_win': winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0,
            'avg_loss': losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
        }


def compare_indicators(mql4_values: np.array, python_values: np.array, 
                       tolerance: float = 1e-5) -> Dict:
    """
    Compare MQL4 and Python indicator values
    Returns statistics about the comparison
    """
    # Ensure same length
    min_len = min(len(mql4_values), len(python_values))
    mql4_values = mql4_values[:min_len]
    python_values = python_values[:min_len]
    
    # Remove NaN values
    mask = ~(np.isnan(mql4_values) | np.isnan(python_values))
    mql4_values = mql4_values[mask]
    python_values = python_values[mask]
    
    if len(mql4_values) == 0:
        return {
            'matches': False,
            'reason': 'No valid values to compare'
        }
    
    # Calculate differences
    differences = np.abs(mql4_values - python_values)
    max_diff = np.max(differences)
    mean_diff = np.mean(differences)
    
    # Calculate correlation
    correlation = np.corrcoef(mql4_values, python_values)[0, 1]
    
    return {
        'matches': max_diff <= tolerance,
        'max_difference': max_diff,
        'mean_difference': mean_diff,
        'correlation': correlation,
        'values_compared': len(mql4_values),
        'tolerance': tolerance
    }


if __name__ == "__main__":
    # Example usage
    print("MQL4 to Python Backtesting Framework")
    print("=" * 50)
    
    # Load historical data
    history_file = "/home/developer/mql-python-converter/server/mt4-terminal/history/default/EURUSD240.hst"
    
    if Path(history_file).exists():
        reader = MT4HistoryReader(history_file)
        data = reader.load()
        info = reader.get_info()
        
        print(f"Loaded {info['symbol']} {info['period']}M data")
        print(f"Date range: {info['date_range'][0]} to {info['date_range'][1]}")
        print(f"Total bars: {info['bar_count']}")
        
        # Calculate indicator
        indicator = SimpleMA(data)
        indicator.calculate()
        signals = indicator.get_crossover_signals()
        
        print(f"\nIndicator calculated")
        print(f"Bullish signals: {(signals == 1).sum()}")
        print(f"Bearish signals: {(signals == -1).sum()}")
        
        # Run backtest
        engine = BacktestEngine(data)
        engine.run_strategy(signals)
        stats = engine.get_statistics()
        
        print("\nBacktest Results:")
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"{key}: {value:.4f}")
            else:
                print(f"{key}: {value}")
    else:
        print(f"History file not found: {history_file}")