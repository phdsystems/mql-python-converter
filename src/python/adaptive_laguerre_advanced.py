"""
Advanced Adaptive Laguerre Filter with Real Market Data Support
Includes backtesting capabilities and performance metrics
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List, Tuple
from adaptive_laguerre_filter import AdaptiveLaguerreFilter, SmoothMode
import warnings

class AdaptiveLaguerreTrader:
    """
    Trading system based on Adaptive Laguerre Filter with backtesting capabilities.
    """
    
    def __init__(self, 
                 filter_params: Optional[Dict] = None,
                 risk_params: Optional[Dict] = None):
        """
        Initialize the trading system.
        
        Parameters:
        -----------
        filter_params : dict
            Parameters for the Adaptive Laguerre Filter
        risk_params : dict
            Risk management parameters
        """
        # Default filter parameters
        self.filter_params = filter_params or {
            'length': 10,
            'order': 4,
            'adaptive_mode': True,
            'adaptive_smooth': 5,
            'adaptive_smooth_mode': SmoothMode.MEDIAN
        }
        
        # Default risk parameters
        self.risk_params = risk_params or {
            'position_size': 1.0,
            'stop_loss_pct': 0.02,  # 2% stop loss
            'take_profit_pct': 0.04,  # 4% take profit
            'use_trailing_stop': True,
            'trailing_stop_pct': 0.015  # 1.5% trailing stop
        }
        
        self.filter = AdaptiveLaguerreFilter(**self.filter_params)
        
    def generate_signals(self, prices: pd.Series) -> pd.DataFrame:
        """
        Generate trading signals from price data.
        
        Parameters:
        -----------
        prices : pd.Series
            Price series with datetime index
            
        Returns:
        --------
        pd.DataFrame : DataFrame with signals and indicators
        """
        # Calculate filter values
        result = self.filter.calculate(prices.values)
        
        # Create DataFrame with results
        df = pd.DataFrame(index=prices.index)
        df['price'] = prices
        df['laguerre'] = result['laguerre']
        df['trend'] = result['trend']
        df['gamma'] = result['gamma']
        
        # Generate trading signals
        df['signal'] = 0
        df['position'] = 0
        
        # Basic signal generation
        df.loc[df['trend'] == 1, 'signal'] = 1  # Buy
        df.loc[df['trend'] == 2, 'signal'] = -1  # Sell
        
        # Enhanced signals with filters
        df = self._apply_signal_filters(df)
        
        # Calculate positions
        df['position'] = df['signal'].fillna(0)
        
        return df
    
    def _apply_signal_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply additional filters to reduce false signals.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with basic signals
            
        Returns:
        --------
        pd.DataFrame : DataFrame with filtered signals
        """
        # Filter 1: Minimum price-filter distance
        df['filter_distance'] = abs(df['price'] - df['laguerre']) / df['price']
        min_distance = 0.001  # 0.1% minimum distance
        
        # Filter 2: Gamma stability (avoid signals during rapid gamma changes)
        df['gamma_change'] = df['gamma'].diff().abs()
        max_gamma_change = 0.3
        
        # Filter 3: Trend consistency (trend must persist for N bars)
        trend_consistency = 2
        df['trend_consistent'] = (df['trend'] == df['trend'].shift(1)) & \
                                 (df['trend'] == df['trend'].shift(2))
        
        # Apply filters
        df['signal_filtered'] = df['signal']
        
        # Remove signals that don't meet filter criteria
        mask = (df['filter_distance'] < min_distance) | \
               (df['gamma_change'] > max_gamma_change) | \
               (~df['trend_consistent'])
        
        df.loc[mask, 'signal_filtered'] = 0
        
        # Use filtered signals
        df['signal'] = df['signal_filtered']
        
        return df
    
    def backtest(self, df: pd.DataFrame, initial_capital: float = 10000) -> Dict:
        """
        Perform backtesting on the signals.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with prices and signals
        initial_capital : float
            Starting capital for backtesting
            
        Returns:
        --------
        dict : Backtesting results and performance metrics
        """
        # Initialize backtesting variables
        capital = initial_capital
        position = 0
        entry_price = 0
        trades = []
        equity_curve = []
        
        # Track peak for drawdown calculation
        peak_equity = initial_capital
        
        for i in range(len(df)):
            current_price = df.iloc[i]['price']
            signal = df.iloc[i]['signal']
            
            # Record equity
            current_equity = capital + position * current_price
            equity_curve.append(current_equity)
            
            # Update peak equity
            peak_equity = max(peak_equity, current_equity)
            
            # Execute trades based on signals
            if signal == 1 and position == 0:  # Buy signal
                # Enter long position
                position = (capital * self.risk_params['position_size']) / current_price
                entry_price = current_price
                capital -= position * current_price
                
                trades.append({
                    'entry_time': df.index[i],
                    'entry_price': entry_price,
                    'position_size': position,
                    'type': 'long'
                })
                
            elif signal == -1 and position > 0:  # Sell signal
                # Close long position
                exit_price = current_price
                pnl = position * (exit_price - entry_price)
                capital += position * exit_price
                
                if trades and 'exit_time' not in trades[-1]:
                    trades[-1].update({
                        'exit_time': df.index[i],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'return_pct': (exit_price - entry_price) / entry_price * 100
                    })
                
                position = 0
                entry_price = 0
            
            # Apply stop loss and take profit
            if position > 0:
                # Calculate current P&L percentage
                current_pnl_pct = (current_price - entry_price) / entry_price
                
                # Stop loss
                if current_pnl_pct <= -self.risk_params['stop_loss_pct']:
                    exit_price = current_price
                    pnl = position * (exit_price - entry_price)
                    capital += position * exit_price
                    
                    if trades and 'exit_time' not in trades[-1]:
                        trades[-1].update({
                            'exit_time': df.index[i],
                            'exit_price': exit_price,
                            'pnl': pnl,
                            'return_pct': (exit_price - entry_price) / entry_price * 100,
                            'exit_reason': 'stop_loss'
                        })
                    
                    position = 0
                    entry_price = 0
                
                # Take profit
                elif current_pnl_pct >= self.risk_params['take_profit_pct']:
                    exit_price = current_price
                    pnl = position * (exit_price - entry_price)
                    capital += position * exit_price
                    
                    if trades and 'exit_time' not in trades[-1]:
                        trades[-1].update({
                            'exit_time': df.index[i],
                            'exit_price': exit_price,
                            'pnl': pnl,
                            'return_pct': (exit_price - entry_price) / entry_price * 100,
                            'exit_reason': 'take_profit'
                        })
                    
                    position = 0
                    entry_price = 0
        
        # Close any remaining position
        if position > 0:
            exit_price = df.iloc[-1]['price']
            pnl = position * (exit_price - entry_price)
            capital += position * exit_price
            
            if trades and 'exit_time' not in trades[-1]:
                trades[-1].update({
                    'exit_time': df.index[-1],
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'return_pct': (exit_price - entry_price) / entry_price * 100,
                    'exit_reason': 'end_of_data'
                })
        
        # Calculate performance metrics
        equity_curve = np.array(equity_curve)
        returns = pd.Series(equity_curve).pct_change().dropna()
        
        # Filter completed trades
        completed_trades = [t for t in trades if 'exit_time' in t]
        
        metrics = self._calculate_metrics(
            equity_curve, 
            returns, 
            completed_trades, 
            initial_capital
        )
        
        return {
            'metrics': metrics,
            'trades': completed_trades,
            'equity_curve': equity_curve
        }
    
    def _calculate_metrics(self, 
                          equity_curve: np.ndarray, 
                          returns: pd.Series,
                          trades: List[Dict],
                          initial_capital: float) -> Dict:
        """
        Calculate comprehensive performance metrics.
        """
        final_equity = equity_curve[-1] if len(equity_curve) > 0 else initial_capital
        
        # Basic metrics
        total_return = (final_equity - initial_capital) / initial_capital * 100
        
        # Trade statistics
        n_trades = len(trades)
        if n_trades > 0:
            winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
            losing_trades = [t for t in trades if t.get('pnl', 0) <= 0]
            
            win_rate = len(winning_trades) / n_trades * 100 if n_trades > 0 else 0
            
            avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
            
            profit_factor = abs(sum(t['pnl'] for t in winning_trades) / 
                               sum(t['pnl'] for t in losing_trades)) if losing_trades else 0
        else:
            win_rate = avg_win = avg_loss = profit_factor = 0
        
        # Risk metrics
        if len(returns) > 0:
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            max_drawdown = self._calculate_max_drawdown(equity_curve)
            volatility = returns.std() * np.sqrt(252) * 100  # Annualized
        else:
            sharpe_ratio = max_drawdown = volatility = 0
        
        return {
            'total_return_pct': total_return,
            'final_equity': final_equity,
            'n_trades': n_trades,
            'win_rate_pct': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown,
            'volatility_pct': volatility
        }
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe Ratio."""
        if len(returns) == 0 or returns.std() == 0:
            return 0
        
        excess_returns = returns - risk_free_rate / 252
        return np.sqrt(252) * excess_returns.mean() / returns.std()
    
    def _calculate_max_drawdown(self, equity_curve: np.ndarray) -> float:
        """Calculate maximum drawdown percentage."""
        if len(equity_curve) == 0:
            return 0
        
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - peak) / peak * 100
        return abs(drawdown.min())


def load_market_data(symbol: str = 'sample', period: str = '1D') -> pd.DataFrame:
    """
    Load or generate sample market data.
    
    In production, this would connect to a real data source.
    For demonstration, we'll generate realistic sample data.
    """
    # Generate sample OHLCV data
    np.random.seed(42)
    n_days = 252  # One year of daily data
    
    dates = pd.date_range(end=pd.Timestamp.now(), periods=n_days, freq='D')
    
    # Generate realistic price movement
    returns = np.random.normal(0.0005, 0.02, n_days)  # Daily returns
    price = 100 * np.exp(np.cumsum(returns))
    
    # Add some trend
    trend = np.linspace(0, 20, n_days)
    price = price + trend
    
    # Create OHLCV data
    df = pd.DataFrame(index=dates)
    df['open'] = price * (1 + np.random.uniform(-0.01, 0.01, n_days))
    df['high'] = price * (1 + np.random.uniform(0, 0.02, n_days))
    df['low'] = price * (1 + np.random.uniform(-0.02, 0, n_days))
    df['close'] = price
    df['volume'] = np.random.uniform(1000000, 5000000, n_days)
    
    return df


# Example usage with backtesting
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    
    # Load sample market data
    print("Loading market data...")
    df = load_market_data('SAMPLE', '1D')
    
    # Initialize trader with custom parameters
    trader = AdaptiveLaguerreTrader(
        filter_params={
            'length': 10,
            'order': 4,
            'adaptive_mode': True,
            'adaptive_smooth': 5,
            'adaptive_smooth_mode': SmoothMode.MEDIAN
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
    print("Generating trading signals...")
    signals_df = trader.generate_signals(df['close'])
    
    # Perform backtesting
    print("Running backtest...")
    backtest_results = trader.backtest(signals_df, initial_capital=10000)
    
    # Print performance metrics
    print("\n" + "="*60)
    print("BACKTEST RESULTS - Adaptive Laguerre Trading System")
    print("="*60)
    
    metrics = backtest_results['metrics']
    for key, value in metrics.items():
        if isinstance(value, float):
            if 'pct' in key or 'ratio' in key or 'factor' in key:
                print(f"{key.replace('_', ' ').title()}: {value:.2f}")
            else:
                print(f"{key.replace('_', ' ').title()}: ${value:.2f}")
        else:
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Plot results
    fig, axes = plt.subplots(4, 1, figsize=(14, 12))
    
    # Plot 1: Price and Laguerre Filter
    ax1 = axes[0]
    ax1.plot(signals_df.index, signals_df['price'], label='Price', alpha=0.7)
    ax1.plot(signals_df.index, signals_df['laguerre'], label='Adaptive Laguerre', 
             linewidth=2, color='blue')
    
    # Mark buy/sell signals
    buy_signals = signals_df[signals_df['signal'] == 1]
    sell_signals = signals_df[signals_df['signal'] == -1]
    
    if not buy_signals.empty:
        ax1.scatter(buy_signals.index, buy_signals['price'], 
                   color='green', marker='^', s=100, label='Buy', zorder=5)
    if not sell_signals.empty:
        ax1.scatter(sell_signals.index, sell_signals['price'], 
                   color='red', marker='v', s=100, label='Sell', zorder=5)
    
    ax1.set_title('Price Action with Adaptive Laguerre Filter')
    ax1.set_ylabel('Price ($)')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Equity Curve
    ax2 = axes[1]
    equity_dates = signals_df.index[:len(backtest_results['equity_curve'])]
    ax2.plot(equity_dates, backtest_results['equity_curve'], 
             label='Equity Curve', linewidth=2, color='green')
    ax2.axhline(y=10000, color='gray', linestyle='--', alpha=0.5, label='Initial Capital')
    ax2.set_title('Equity Curve')
    ax2.set_ylabel('Equity ($)')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Drawdown
    ax3 = axes[2]
    equity = backtest_results['equity_curve']
    peak = np.maximum.accumulate(equity)
    drawdown = (equity - peak) / peak * 100
    ax3.fill_between(equity_dates, 0, drawdown, color='red', alpha=0.3)
    ax3.plot(equity_dates, drawdown, color='red', linewidth=1)
    ax3.set_title('Drawdown')
    ax3.set_ylabel('Drawdown (%)')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Adaptive Gamma
    ax4 = axes[3]
    ax4.plot(signals_df.index, signals_df['gamma'], 
             label='Adaptive Gamma', color='orange', alpha=0.7)
    ax4.set_title('Adaptive Gamma (Market Efficiency)')
    ax4.set_xlabel('Date')
    ax4.set_ylabel('Gamma')
    ax4.legend(loc='best')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/home/developer/adaptive_laguerre_backtest.png', dpi=100)
    plt.show()
    
    # Print trade summary
    if backtest_results['trades']:
        print("\n" + "="*60)
        print("TRADE SUMMARY (Last 10 Trades)")
        print("="*60)
        
        trades_df = pd.DataFrame(backtest_results['trades'][-10:])
        if not trades_df.empty:
            print(trades_df[['entry_time', 'exit_time', 'return_pct']].to_string())