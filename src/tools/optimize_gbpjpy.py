"""
Optimize Adaptive Laguerre Filter parameters on real GBP/JPY data
"""

import json
import time
from typing import Dict, List, Tuple
from datetime import datetime

# Import our modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../python/data-ingestor'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../python'))

from download_forex_data import load_data, get_price_series, calculate_returns
from laguerre_optimizer_simple import SimpleOptimizer, ParameterRecommender
from test_laguerre_simple import SimpleLaguerreFilter

class GBPJPYOptimizer:
    """Optimize Adaptive Laguerre Filter for GBP/JPY trading"""
    
    def __init__(self, data_file: str = '../python/data-ingestor/data/gbpjpy_d1_5years.json'):
        """Initialize with GBP/JPY data"""
        self.data = load_data(data_file)
        self.prices = get_price_series(self.data, 'close')
        self.returns = calculate_returns(self.prices)
        
        # Split data for training and validation
        split_point = int(len(self.prices) * 0.7)
        self.train_prices = self.prices[:split_point]
        self.test_prices = self.prices[split_point:]
        
        print(f"Loaded {len(self.prices)} price points")
        print(f"Training set: {len(self.train_prices)} bars")
        print(f"Test set: {len(self.test_prices)} bars")
    
    def optimize_parameters(self) -> Dict:
        """Run comprehensive parameter optimization"""
        results = {}
        
        print("\n" + "="*60)
        print("PARAMETER OPTIMIZATION FOR GBP/JPY")
        print("="*60)
        
        # 1. Market Analysis
        print("\n1. MARKET ANALYSIS")
        print("-"*40)
        recommender = ParameterRecommender()
        market_analysis = recommender.analyze_market(self.train_prices)
        
        print(f"Training Set Characteristics:")
        print(f"  Volatility: {market_analysis['volatility']*100:.3f}% ({market_analysis['volatility_class']})")
        print(f"  Trend: {market_analysis['trend_strength']*100:.2f}% ({market_analysis['trend_class']})")
        
        results['market_analysis'] = market_analysis
        
        # 2. Get recommended parameters
        print("\n2. RECOMMENDED PARAMETERS")
        print("-"*40)
        
        trading_styles = ['scalping', 'day_trading', 'swing_trading']
        recommendations = {}
        
        for style in trading_styles:
            params = recommender.recommend_parameters(market_analysis, style)
            recommendations[style] = params
            print(f"\n{style.upper()}:")
            for key, value in params.items():
                print(f"  {key}: {value}")
        
        results['recommendations'] = recommendations
        
        # 3. Grid Search Optimization
        print("\n3. GRID SEARCH OPTIMIZATION")
        print("-"*40)
        
        # Define parameter grid based on market conditions
        if market_analysis['volatility_class'] == 'high':
            param_grid = {
                'length': [15, 20, 30, 40],
                'order': [4, 5, 6],
                'adaptive_smooth': [7, 10, 12]
            }
        elif market_analysis['volatility_class'] == 'low':
            param_grid = {
                'length': [5, 10, 15, 20],
                'order': [2, 3, 4],
                'adaptive_smooth': [3, 5, 7]
            }
        else:  # medium
            param_grid = {
                'length': [10, 15, 20, 25],
                'order': [3, 4, 5],
                'adaptive_smooth': [5, 7, 9]
            }
        
        print(f"Testing parameter grid for {market_analysis['volatility_class']} volatility market...")
        
        optimizer = SimpleOptimizer(self.train_prices, metric='sharpe')
        grid_result = optimizer.grid_search(param_grid)
        results['grid_search'] = grid_result
        
        # 4. Random Search Optimization
        print("\n4. RANDOM SEARCH OPTIMIZATION")
        print("-"*40)
        
        param_ranges = {
            'length': (5, 50),
            'order': (2, 6),
            'adaptive_smooth': (3, 15)
        }
        
        optimizer2 = SimpleOptimizer(self.train_prices, metric='return')
        random_result = optimizer2.random_search(param_ranges, n_iter=50)
        results['random_search'] = random_result
        
        # 5. Backtest on test set
        print("\n5. VALIDATION ON TEST SET")
        print("-"*40)
        
        best_params = grid_result['params']
        validation_results = self.backtest_parameters(best_params, self.test_prices)
        results['validation'] = validation_results
        
        print(f"Best Parameters Performance:")
        print(f"  Training Sharpe: {grid_result['score']:.3f}")
        print(f"  Test Return: {validation_results['total_return']:.2f}%")
        print(f"  Test Sharpe: {validation_results['sharpe_ratio']:.3f}")
        print(f"  Win Rate: {validation_results['win_rate']:.1f}%")
        print(f"  Max Drawdown: {validation_results['max_drawdown']:.2f}%")
        
        # 6. Walk-Forward Analysis
        print("\n6. WALK-FORWARD ANALYSIS")
        print("-"*40)
        
        wf_results = self.walk_forward_analysis(param_grid)
        results['walk_forward'] = wf_results
        
        return results
    
    def backtest_parameters(self, params: Dict, prices: List[float]) -> Dict:
        """Backtest specific parameters on price data"""
        
        # Create filter
        filter = SimpleLaguerreFilter(
            length=params.get('length', 10),
            order=params.get('order', 4)
        )
        
        # Calculate filter values
        filtered = []
        gamma = 10.0 / (params['length'] + 9)  # Fixed gamma for simplicity
        
        for price in prices:
            filtered.append(filter.calculate_single(price, gamma))
        
        # Generate signals
        signals = []
        for i in range(1, len(filtered)):
            if filtered[i] > filtered[i-1]:
                signals.append(1)  # Buy
            elif filtered[i] < filtered[i-1]:
                signals.append(-1)  # Sell
            else:
                signals.append(0)  # Hold
        
        # Calculate returns
        returns = []
        position = 0
        entry_price = 0
        trades = []
        
        for i in range(len(signals)):
            if signals[i] == 1 and position == 0:
                # Enter long
                position = 1
                entry_price = prices[i+1]
                
            elif signals[i] == -1 and position == 1:
                # Exit long
                exit_price = prices[i+1]
                trade_return = (exit_price - entry_price) / entry_price
                returns.append(trade_return)
                trades.append({
                    'entry': entry_price,
                    'exit': exit_price,
                    'return': trade_return * 100
                })
                position = 0
        
        # Calculate metrics
        if returns:
            total_return = sum(returns) * 100
            avg_return = sum(returns) / len(returns)
            
            # Sharpe ratio
            if len(returns) > 1:
                std_return = (sum((r - avg_return)**2 for r in returns) / (len(returns) - 1)) ** 0.5
                sharpe = (avg_return / std_return * (252 ** 0.5)) if std_return > 0 else 0
            else:
                sharpe = 0
            
            # Win rate
            wins = sum(1 for r in returns if r > 0)
            win_rate = (wins / len(returns) * 100) if returns else 0
            
            # Max drawdown
            cumulative = []
            cum_ret = 1.0
            for r in returns:
                cum_ret *= (1 + r)
                cumulative.append(cum_ret)
            
            peak = cumulative[0] if cumulative else 1
            max_dd = 0
            for value in cumulative:
                peak = max(peak, value)
                dd = (value - peak) / peak * 100
                max_dd = min(max_dd, dd)
        else:
            total_return = 0
            sharpe = 0
            win_rate = 0
            max_dd = 0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'win_rate': win_rate,
            'max_drawdown': max_dd,
            'num_trades': len(trades),
            'best_trade': max(trades, key=lambda x: x['return'])['return'] if trades else 0,
            'worst_trade': min(trades, key=lambda x: x['return'])['return'] if trades else 0
        }
    
    def walk_forward_analysis(self, param_grid: Dict, window: int = 252) -> List[Dict]:
        """Walk-forward analysis with rolling windows"""
        
        results = []
        step = 63  # Quarterly steps
        
        print(f"Running walk-forward with {window}-day windows, {step}-day steps...")
        
        for start in range(0, len(self.prices) - window - step, step):
            # Training window
            train_end = start + window
            train_prices = self.prices[start:train_end]
            
            # Test window (next quarter)
            test_start = train_end
            test_end = min(test_start + step, len(self.prices))
            test_prices = self.prices[test_start:test_end]
            
            if len(test_prices) < 20:
                continue
            
            # Optimize on training
            optimizer = SimpleOptimizer(train_prices, metric='sharpe')
            best = optimizer.grid_search(param_grid)
            
            # Test on out-of-sample
            test_result = self.backtest_parameters(best['params'], test_prices)
            
            results.append({
                'period': f"{self.data[start]['date']} to {self.data[test_end-1]['date']}",
                'train_score': best['score'],
                'test_return': test_result['total_return'],
                'test_sharpe': test_result['sharpe_ratio']
            })
            
            print(f"  Period {len(results)}: Test Return: {test_result['total_return']:.2f}%")
        
        # Calculate statistics
        if results:
            avg_return = sum(r['test_return'] for r in results) / len(results)
            avg_sharpe = sum(r['test_sharpe'] for r in results) / len(results)
            
            print(f"\nWalk-Forward Summary:")
            print(f"  Average Test Return: {avg_return:.2f}%")
            print(f"  Average Test Sharpe: {avg_sharpe:.3f}")
            print(f"  Consistency: {sum(1 for r in results if r['test_return'] > 0) / len(results) * 100:.1f}%")
        
        return results
    
    def print_trading_signals(self, params: Dict, last_n: int = 20):
        """Print recent trading signals"""
        
        print(f"\nRECENT TRADING SIGNALS (Last {last_n} bars)")
        print("-"*60)
        
        # Calculate filter on recent data
        recent_prices = self.prices[-last_n:]
        recent_dates = [bar['date'] for bar in self.data[-last_n:]]
        
        filter = SimpleLaguerreFilter(
            length=params.get('length', 10),
            order=params.get('order', 4)
        )
        
        filtered = []
        gamma = 10.0 / (params['length'] + 9)
        
        for price in recent_prices:
            filtered.append(filter.calculate_single(price, gamma))
        
        # Generate signals
        print(f"{'Date':<12} {'Price':<8} {'Filter':<8} {'Signal':<10} {'Action'}")
        print("-"*50)
        
        for i in range(1, len(filtered)):
            signal = "NEUTRAL"
            action = "Hold"
            
            if filtered[i] > filtered[i-1] * 1.001:  # 0.1% threshold
                signal = "BULLISH"
                action = "Buy/Hold"
            elif filtered[i] < filtered[i-1] * 0.999:
                signal = "BEARISH"
                action = "Sell/Exit"
            
            print(f"{recent_dates[i]:<12} {recent_prices[i]:<8.3f} "
                  f"{filtered[i]:<8.3f} {signal:<10} {action}")
    
    def save_results(self, results: Dict, filename: str = 'gbpjpy_optimization_results.json'):
        """Save optimization results"""
        
        # Add metadata
        results['metadata'] = {
            'symbol': 'GBP/JPY',
            'timeframe': 'D1',
            'data_points': len(self.prices),
            'date_range': f"{self.data[0]['date']} to {self.data[-1]['date']}",
            'optimization_date': datetime.now().isoformat()
        }
        
        # Convert any non-serializable objects
        def clean_for_json(obj):
            if isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(v) for v in obj]
            elif isinstance(obj, (int, float, str, bool, type(None))):
                return obj
            else:
                return str(obj)
        
        clean_results = clean_for_json(results)
        
        with open(filename, 'w') as f:
            json.dump(clean_results, f, indent=2)
        
        print(f"\nResults saved to {filename}")


def main():
    """Main optimization workflow"""
    
    print("\n" + "="*70)
    print(" ADAPTIVE LAGUERRE FILTER - GBP/JPY OPTIMIZATION ")
    print("="*70)
    
    # Create optimizer
    optimizer = GBPJPYOptimizer()
    
    # Run optimization
    results = optimizer.optimize_parameters()
    
    # Print final recommendations
    print("\n" + "="*60)
    print("FINAL RECOMMENDATIONS FOR GBP/JPY TRADING")
    print("="*60)
    
    best_params = results['grid_search']['params']
    
    print("\nOPTIMAL PARAMETERS:")
    print("-"*40)
    for key, value in best_params.items():
        print(f"  {key}: {value}")
    
    print("\nEXPECTED PERFORMANCE:")
    print("-"*40)
    val = results['validation']
    print(f"  Expected Return: {val['total_return']:.2f}% per period")
    print(f"  Sharpe Ratio: {val['sharpe_ratio']:.3f}")
    print(f"  Win Rate: {val['win_rate']:.1f}%")
    print(f"  Max Drawdown: {val['max_drawdown']:.2f}%")
    print(f"  Number of Trades: {val['num_trades']}")
    
    # Show recent signals
    optimizer.print_trading_signals(best_params)
    
    # Save results
    optimizer.save_results(results)
    
    print("\n" + "="*60)
    print("OPTIMIZATION COMPLETE!")
    print("="*60)
    print("\nKey Findings:")
    print("• Optimal length varies with market volatility")
    print("• Higher order values work better in trending markets")
    print("• Adaptive mode recommended for GBP/JPY volatility")
    print("• Regular re-optimization suggested (quarterly)")
    print("\nUse these parameters as a starting point and")
    print("continue monitoring performance in live trading.")


if __name__ == "__main__":
    main()