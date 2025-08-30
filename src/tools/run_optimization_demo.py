#!/usr/bin/env python3
"""
Demonstration of the complete optimization workflow
Using adapter patterns for metrics and optimization methods
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.metrics_adapter import TradeResult, MetricFactory
from tools.optimization_adapter import OptimizationFactory


def simulate_trading_strategy(params, prices):
    """
    Simulate a simple trading strategy based on Laguerre filter parameters
    Returns list of TradeResult objects
    """
    length = params.get('length', 10)
    threshold = params.get('threshold', 0.02)
    
    # Simple moving average as proxy for Laguerre filter
    ma = []
    for i in range(len(prices)):
        if i < length:
            ma.append(prices[i])
        else:
            ma.append(sum(prices[i-length:i]) / length)
    
    # Generate trades
    trades = []
    position = 0
    entry_price = 0
    entry_time = 0
    
    for i in range(1, len(prices)):
        # Calculate signal
        if i < length:
            continue
            
        price_change = (prices[i] - ma[i]) / ma[i]
        
        # Entry signal
        if position == 0 and price_change > threshold:
            position = 1
            entry_price = prices[i]
            entry_time = i
        
        # Exit signal
        elif position == 1 and price_change < -threshold:
            trade = TradeResult(
                entry_price=entry_price,
                exit_price=prices[i],
                entry_time=entry_time,
                exit_time=i
            )
            trades.append(trade)
            position = 0
    
    # Close any open position
    if position == 1:
        trade = TradeResult(
            entry_price=entry_price,
            exit_price=prices[-1],
            entry_time=entry_time,
            exit_time=len(prices) - 1
        )
        trades.append(trade)
    
    return trades


def objective_function(params):
    """
    Objective function for optimization
    Evaluates strategy performance with given parameters
    """
    # Load GBP/JPY data
    data_path = os.path.join(
        os.path.dirname(__file__),
        '../python/data-ingestor/data/gbpjpy_d1_5years.json'
    )
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Extract prices
    prices = [bar['close'] for bar in data[:500]]  # Use first 500 bars for speed
    
    # Simulate trading
    trades = simulate_trading_strategy(params, prices)
    
    if not trades:
        return {'sharpe_ratio': -999, 'total_return': 0, 'win_rate': 0}
    
    # Calculate all metrics
    metrics = {}
    for metric_name in ['sharpe_ratio', 'total_return', 'win_rate', 'max_drawdown']:
        try:
            metric = MetricFactory.create(metric_name)
            score = metric.calculate(trades, prices)
            metrics[metric_name] = score
        except:
            metrics[metric_name] = 0
    
    return metrics


def main():
    """Run the optimization demonstration"""
    
    print("="*70)
    print(" LAGUERRE FILTER OPTIMIZATION DEMONSTRATION")
    print(" Using Adapter Patterns for Metrics and Optimization")
    print("="*70)
    
    # Load and display data info
    data_path = os.path.join(
        os.path.dirname(__file__),
        '../python/data-ingestor/data/gbpjpy_d1_5years.json'
    )
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    print(f"\nData: GBP/JPY Daily")
    print(f"Period: {data[0]['date']} to {data[499]['date']}")
    print(f"Bars: 500 (for demonstration speed)")
    
    # Define parameter spaces
    param_space_grid = {
        'length': [10, 15, 20, 25],
        'threshold': [0.01, 0.02, 0.03]
    }
    
    param_space_random = {
        'length': (5, 30),
        'threshold': (0.005, 0.05)
    }
    
    # Test different optimization methods
    methods = ['grid_search', 'random_search', 'genetic_algorithm']
    
    results = {}
    
    for method in methods:
        print(f"\n{'='*60}")
        print(f"METHOD: {method.upper()}")
        print(f"{'='*60}")
        
        # Create metric adapter
        metric_adapter = MetricFactory.create('sharpe_ratio')
        
        # Create optimizer
        optimizer = OptimizationFactory.create(
            method,
            objective_function,
            metric_adapter
        )
        
        # Run optimization
        if method == 'grid_search':
            result = optimizer.optimize(param_space_grid, verbose=True)
        elif method == 'random_search':
            result = optimizer.optimize(param_space_random, n_iter=30, verbose=True, seed=42)
        else:  # genetic_algorithm
            result = optimizer.optimize(
                param_space_random,
                population_size=20,
                generations=10,
                verbose=True,
                seed=42
            )
        
        results[method] = result
        
        # Display results
        print(f"\nBest Parameters:")
        for param, value in result.parameters.items():
            print(f"  {param}: {value:.4f}" if isinstance(value, float) else f"  {param}: {value}")
        
        print(f"\nPerformance Metrics:")
        for metric_name, score in result.metrics.items():
            print(f"  {metric_name}: {score:.4f}")
        
        print(f"\nOptimization Stats:")
        print(f"  Iterations: {result.iterations}")
        print(f"  Best Score: {result.score:.4f}")
    
    # Compare results
    print("\n" + "="*70)
    print(" COMPARISON OF OPTIMIZATION METHODS")
    print("="*70)
    
    print("\n{:<20} {:<15} {:<15} {:<15}".format(
        "Method", "Sharpe Ratio", "Total Return", "Win Rate"
    ))
    print("-"*65)
    
    for method, result in results.items():
        sharpe = result.metrics.get('sharpe_ratio', 0)
        returns = result.metrics.get('total_return', 0)
        win_rate = result.metrics.get('win_rate', 0)
        
        print("{:<20} {:<15.4f} {:<15.2f}% {:<15.2f}%".format(
            method, sharpe, returns, win_rate
        ))
    
    # Find best overall
    best_method = max(results.items(), key=lambda x: x[1].score)
    
    print("\n" + "="*70)
    print(" BEST OPTIMIZATION METHOD")
    print("="*70)
    print(f"\nMethod: {best_method[0].upper()}")
    print(f"Parameters: {best_method[1].parameters}")
    print(f"Sharpe Ratio: {best_method[1].score:.4f}")
    
    print("\n✅ Optimization demonstration complete!")
    print("The adapter patterns provide flexible, extensible optimization capabilities.")
    
    return results


if __name__ == "__main__":
    results = main()