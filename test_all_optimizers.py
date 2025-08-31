#!/usr/bin/env python3
"""
Comprehensive test script for all optimization methods
Tests each optimizer on the same problem and compares results
"""

import sys
import os
import json
import time
import numpy as np
from typing import Dict, List
import warnings

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import optimization adapters
from tools.optimization_adapter import OptimizationFactory, OptimizationResult
from tools.metrics_adapter import MetricFactory, TradeResult

# Try to register all available optimizers
registered_optimizers = []

# Original optimizers (always available)
registered_optimizers.extend(['grid_search', 'random_search', 'genetic_algorithm', 'bayesian_optimization'])

# Try to register Optuna
try:
    from tools.optuna_adapter import register_optuna_adapters
    if register_optuna_adapters():
        registered_optimizers.extend(['optuna', 'optuna_multi'])
        print("✓ Optuna registered successfully")
except Exception as e:
    print(f"✗ Optuna not available: {e}")

# Try to register Hyperopt
try:
    from tools.hyperopt_adapter import register_hyperopt_adapters
    if register_hyperopt_adapters():
        registered_optimizers.extend(['hyperopt'])
        print("✓ Hyperopt registered successfully")
except Exception as e:
    print(f"✗ Hyperopt not available: {e}")

# Try to register Scikit-Optimize
try:
    from tools.skopt_adapter import register_skopt_adapters
    if register_skopt_adapters():
        registered_optimizers.extend(['scikit_optimize', 'skopt'])
        print("✓ Scikit-Optimize registered successfully")
except Exception as e:
    print(f"✗ Scikit-Optimize not available: {e}")

# Try to register Ray Tune
try:
    from tools.raytune_adapter import register_raytune_adapters
    if register_raytune_adapters():
        registered_optimizers.extend(['ray_tune'])
        print("✓ Ray Tune registered successfully")
except Exception as e:
    print(f"✗ Ray Tune not available: {e}")

# Try to register Nevergrad
try:
    from tools.nevergrad_adapter import register_nevergrad_adapters
    if register_nevergrad_adapters():
        registered_optimizers.extend(['nevergrad'])
        print("✓ Nevergrad registered successfully")
except Exception as e:
    print(f"✗ Nevergrad not available: {e}")

print(f"\nTotal optimizers available: {len(set(registered_optimizers))}")
print("="*70)


def rosenbrock_function(params: Dict) -> Dict:
    """
    Rosenbrock function - a classic optimization test function
    Global minimum at (1, 1) with value 0
    """
    x = params.get('x', 0)
    y = params.get('y', 0)
    
    # Rosenbrock function: f(x,y) = (1-x)^2 + 100*(y-x^2)^2
    value = (1 - x)**2 + 100 * (y - x**2)**2
    
    # We want to minimize, so return negative for maximization
    score = -value
    
    # Return metrics
    return {
        'score': score,
        'rosenbrock_value': value,
        'distance_from_optimum': np.sqrt((x - 1)**2 + (y - 1)**2)
    }


def trading_strategy_function(params: Dict) -> Dict:
    """
    Simulated trading strategy optimization
    """
    # Parameters
    fast_period = int(params.get('fast_period', 10))
    slow_period = int(params.get('slow_period', 20))
    threshold = params.get('threshold', 0.02)
    
    # Simulate some trading results
    np.random.seed(42)  # For reproducibility
    
    # Generate synthetic price data
    n_days = 100
    returns = np.random.randn(n_days) * 0.02
    prices = 100 * np.exp(np.cumsum(returns))
    
    # Simple moving average crossover strategy
    fast_ma = np.convolve(prices, np.ones(fast_period)/fast_period, mode='valid')
    slow_ma = np.convolve(prices, np.ones(slow_period)/slow_period, mode='valid')
    
    # Align arrays
    min_len = min(len(fast_ma), len(slow_ma))
    fast_ma = fast_ma[:min_len]
    slow_ma = slow_ma[:min_len]
    
    # Generate signals
    signals = (fast_ma > slow_ma * (1 + threshold)).astype(int)
    trades = np.diff(signals)
    
    # Calculate metrics
    n_trades = np.sum(np.abs(trades))
    if n_trades > 0:
        # Simulate returns
        strategy_returns = trades[:-1] * returns[slow_period:slow_period+len(trades)-1]
        total_return = np.sum(strategy_returns) * 100
        
        # Calculate Sharpe ratio
        if np.std(strategy_returns) > 0:
            sharpe_ratio = np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0
    else:
        total_return = 0
        sharpe_ratio = 0
    
    return {
        'sharpe_ratio': sharpe_ratio,
        'total_return': total_return,
        'n_trades': n_trades
    }


def test_optimizer(optimizer_name: str, objective_func, param_space: Dict, 
                  n_trials: int = 50, verbose: bool = False) -> Dict:
    """
    Test a single optimizer
    """
    print(f"\nTesting {optimizer_name}...")
    
    try:
        # Create metric adapter
        metric_adapter = MetricFactory.create('score' if 'x' in param_space else 'sharpe_ratio')
        
        # Create optimizer
        optimizer = OptimizationFactory.create(
            optimizer_name,
            objective_func,
            metric_adapter
        )
        
        # Set up optimizer-specific parameters
        kwargs = {'verbose': verbose, 'seed': 42}
        
        if optimizer_name == 'grid_search':
            # Convert continuous space to discrete for grid search
            if 'x' in param_space:
                param_space_grid = {
                    'x': np.linspace(param_space['x'][0], param_space['x'][1], 10).tolist(),
                    'y': np.linspace(param_space['y'][0], param_space['y'][1], 10).tolist()
                }
            else:
                param_space_grid = {
                    'fast_period': [5, 10, 15, 20],
                    'slow_period': [20, 30, 40, 50],
                    'threshold': [0.01, 0.02, 0.03, 0.05]
                }
            param_space_to_use = param_space_grid
        else:
            param_space_to_use = param_space
            
        # Adjust parameters based on optimizer
        if optimizer_name in ['optuna', 'hyperopt', 'scikit_optimize', 'skopt']:
            kwargs['n_trials'] = n_trials
        elif optimizer_name == 'scikit_optimize':
            kwargs['n_calls'] = n_trials
        elif optimizer_name == 'ray_tune':
            kwargs['num_samples'] = n_trials
            kwargs['local_mode'] = True  # Run locally for testing
        elif optimizer_name == 'nevergrad':
            kwargs['budget'] = n_trials
        elif optimizer_name == 'genetic_algorithm':
            kwargs['population_size'] = 20
            kwargs['generations'] = n_trials // 20
        elif optimizer_name == 'random_search':
            kwargs['n_iter'] = n_trials
        elif optimizer_name == 'bayesian_optimization':
            kwargs['n_iter'] = n_trials
        
        # Run optimization
        start_time = time.time()
        result = optimizer.optimize(param_space_to_use, **kwargs)
        end_time = time.time()
        
        # Clean up Ray if used
        if optimizer_name == 'ray_tune':
            try:
                import ray
                if ray.is_initialized():
                    ray.shutdown()
            except:
                pass
        
        return {
            'optimizer': optimizer_name,
            'best_params': result.parameters,
            'best_score': result.score,
            'metrics': result.metrics,
            'iterations': result.iterations,
            'time_seconds': end_time - start_time,
            'success': True
        }
        
    except Exception as e:
        print(f"  Error: {e}")
        return {
            'optimizer': optimizer_name,
            'error': str(e),
            'success': False
        }


def main():
    """
    Main test function
    """
    print("\n" + "="*70)
    print(" COMPREHENSIVE OPTIMIZER COMPARISON TEST")
    print("="*70)
    
    # Test 1: Rosenbrock function (continuous optimization)
    print("\n" + "-"*70)
    print(" TEST 1: ROSENBROCK FUNCTION (Continuous Optimization)")
    print("-"*70)
    print("Optimal solution: x=1.0, y=1.0, value=0.0")
    
    rosenbrock_space = {
        'x': (-2.0, 2.0),
        'y': (-2.0, 2.0)
    }
    
    rosenbrock_results = []
    for optimizer in set(registered_optimizers):
        if optimizer.endswith('_multi'):
            continue  # Skip multi-objective for now
        result = test_optimizer(optimizer, rosenbrock_function, rosenbrock_space, n_trials=50)
        if result['success']:
            rosenbrock_results.append(result)
    
    # Test 2: Trading strategy optimization (mixed parameters)
    print("\n" + "-"*70)
    print(" TEST 2: TRADING STRATEGY (Mixed Parameter Types)")
    print("-"*70)
    
    trading_space = {
        'fast_period': (5, 20),  # Integer
        'slow_period': (20, 50),  # Integer
        'threshold': (0.005, 0.1)  # Float
    }
    
    trading_results = []
    for optimizer in set(registered_optimizers):
        if optimizer.endswith('_multi'):
            continue  # Skip multi-objective for now
        result = test_optimizer(optimizer, trading_strategy_function, trading_space, n_trials=50)
        if result['success']:
            trading_results.append(result)
    
    # Display results
    print("\n" + "="*70)
    print(" RESULTS SUMMARY")
    print("="*70)
    
    # Rosenbrock results
    if rosenbrock_results:
        print("\nRosenbrock Function Results:")
        print("-"*50)
        print(f"{'Optimizer':<20} {'Best X':<10} {'Best Y':<10} {'Value':<10} {'Time (s)':<10}")
        print("-"*50)
        
        rosenbrock_results.sort(key=lambda x: -x['best_score'])  # Sort by score (descending)
        
        for result in rosenbrock_results:
            x = result['best_params'].get('x', 0)
            y = result['best_params'].get('y', 0)
            value = -(result['best_score'])  # Convert back to minimization value
            time_taken = result['time_seconds']
            
            print(f"{result['optimizer']:<20} {x:<10.4f} {y:<10.4f} {value:<10.4f} {time_taken:<10.2f}")
    
    # Trading strategy results
    if trading_results:
        print("\nTrading Strategy Results:")
        print("-"*60)
        print(f"{'Optimizer':<20} {'Sharpe':<10} {'Return %':<10} {'Trades':<10} {'Time (s)':<10}")
        print("-"*60)
        
        trading_results.sort(key=lambda x: x.get('metrics', {}).get('sharpe_ratio', 0), reverse=True)
        
        for result in trading_results:
            sharpe = result.get('metrics', {}).get('sharpe_ratio', 0)
            returns = result.get('metrics', {}).get('total_return', 0)
            trades = result.get('metrics', {}).get('n_trades', 0)
            time_taken = result['time_seconds']
            
            print(f"{result['optimizer']:<20} {sharpe:<10.4f} {returns:<10.2f} {trades:<10.0f} {time_taken:<10.2f}")
    
    # Best overall
    print("\n" + "="*70)
    print(" BEST PERFORMERS")
    print("="*70)
    
    if rosenbrock_results:
        best_rosenbrock = min(rosenbrock_results, key=lambda x: abs(x['best_score']))
        print(f"\nBest for Rosenbrock: {best_rosenbrock['optimizer']}")
        print(f"  Solution: x={best_rosenbrock['best_params']['x']:.4f}, y={best_rosenbrock['best_params']['y']:.4f}")
        print(f"  Distance from optimum: {best_rosenbrock['metrics']['distance_from_optimum']:.6f}")
    
    if trading_results:
        best_trading = max(trading_results, key=lambda x: x.get('metrics', {}).get('sharpe_ratio', 0))
        print(f"\nBest for Trading: {best_trading['optimizer']}")
        print(f"  Sharpe Ratio: {best_trading['metrics']['sharpe_ratio']:.4f}")
        print(f"  Parameters: {best_trading['best_params']}")
    
    print("\n✅ All tests completed!")
    
    # Save results to file
    results = {
        'rosenbrock': rosenbrock_results,
        'trading': trading_results,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open('optimization_comparison_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to optimization_comparison_results.json")


if __name__ == "__main__":
    main()