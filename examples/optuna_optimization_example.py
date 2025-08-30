"""
Example demonstrating Optuna integration with the optimization framework
Shows how to use advanced Optuna features alongside existing optimizers
"""

import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.optimization_adapter import OptimizationFactory
from src.tools.optuna_adapter import OptunaAdapter, MultiObjectiveOptunaAdapter, register_optuna_adapters
from src.tools.metrics_adapter import SharpeRatioAdapter, TotalReturnAdapter, CalmarRatioAdapter
import warnings

# Suppress Optuna experimental warnings
warnings.filterwarnings('ignore', category=FutureWarning)


def simulate_trading_strategy(params):
    """
    Simulated trading strategy for demonstration
    In real use, this would be your actual strategy backtest
    """
    np.random.seed(42)  # For reproducibility
    
    # Extract parameters
    lookback = int(params.get('lookback', 20))
    threshold = params.get('threshold', 0.5)
    stop_loss = params.get('stop_loss', 0.02)
    take_profit = params.get('take_profit', 0.05)
    
    # Simulate returns based on parameters
    base_returns = np.random.randn(252) * 0.01
    
    # Apply strategy logic (simplified)
    signal_strength = 1.0 / (1.0 + lookback * 0.01)
    risk_adjustment = (1.0 - stop_loss) * (1.0 + take_profit)
    threshold_effect = 1.0 - abs(threshold - 0.5)
    
    strategy_returns = base_returns * signal_strength * risk_adjustment * threshold_effect
    
    # Calculate metrics
    total_return = np.prod(1 + strategy_returns) - 1
    sharpe_ratio = np.mean(strategy_returns) / (np.std(strategy_returns) + 1e-8) * np.sqrt(252)
    max_drawdown = np.min(np.minimum.accumulate(strategy_returns))
    calmar_ratio = total_return / abs(max_drawdown + 1e-8)
    win_rate = np.mean(strategy_returns > 0)
    
    return {
        'sharpe_ratio': sharpe_ratio,
        'total_return': total_return,
        'calmar_ratio': calmar_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate
    }


def compare_optimization_methods():
    """Compare different optimization methods including Optuna"""
    
    # Register Optuna adapters
    register_optuna_adapters()
    
    # Define parameter space
    param_space = {
        'lookback': (10, 50),  # Integer range
        'threshold': (0.1, 0.9),  # Float range
        'stop_loss': (0.01, 0.05),  # Float range
        'take_profit': (0.02, 0.10)  # Float range
    }
    
    # Define metric adapter
    metric_adapter = SharpeRatioAdapter()
    
    # Methods to compare
    methods = [
        'random_search',
        'genetic_algorithm',
        'bayesian_optimization',
        'optuna'
    ]
    
    results = {}
    
    print("=" * 80)
    print("Comparing Optimization Methods")
    print("=" * 80)
    
    for method_name in methods:
        print(f"\n{method_name.upper()}")
        print("-" * 40)
        
        # Create optimizer
        if method_name == 'optuna':
            # Use Optuna with TPE sampler
            optimizer = OptunaAdapter(simulate_trading_strategy, metric_adapter)
            result = optimizer.optimize(
                param_space,
                n_trials=50,
                sampler='tpe',
                verbose=False,
                seed=42
            )
        else:
            # Use existing optimizers
            optimizer = OptimizationFactory.create(
                method_name,
                simulate_trading_strategy,
                metric_adapter
            )
            
            if method_name == 'random_search':
                result = optimizer.optimize(param_space, n_iter=50, verbose=False, seed=42)
            elif method_name == 'genetic_algorithm':
                result = optimizer.optimize(
                    param_space,
                    population_size=20,
                    generations=10,
                    verbose=False,
                    seed=42
                )
            else:  # bayesian_optimization
                result = optimizer.optimize(param_space, n_iter=50, verbose=False, seed=42)
        
        results[method_name] = result
        
        # Print results
        print(f"Best Parameters:")
        for param, value in result.parameters.items():
            print(f"  {param}: {value:.4f}")
        print(f"\nMetrics:")
        for metric, value in result.metrics.items():
            print(f"  {metric}: {value:.4f}")
        print(f"\nScore: {result.score:.4f}")
        print(f"Iterations: {result.iterations}")
    
    # Compare results
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    
    best_method = max(results.items(), key=lambda x: x[1].score)
    print(f"\nBest Method: {best_method[0].upper()}")
    print(f"Best Score: {best_method[1].score:.4f}")
    
    print("\nRanking by Score:")
    sorted_results = sorted(results.items(), key=lambda x: x[1].score, reverse=True)
    for i, (method, result) in enumerate(sorted_results, 1):
        print(f"  {i}. {method}: {result.score:.4f}")


def demonstrate_optuna_advanced_features():
    """Demonstrate advanced Optuna features"""
    
    print("\n" + "=" * 80)
    print("Advanced Optuna Features")
    print("=" * 80)
    
    metric_adapter = SharpeRatioAdapter()
    
    # 1. Dynamic parameter space with conditions
    print("\n1. CONDITIONAL PARAMETER SPACE")
    print("-" * 40)
    
    def strategy_with_conditions(params):
        """Strategy where some parameters depend on others"""
        # Use adaptive parameters only if enabled
        if params.get('use_adaptive', False):
            adaptive_factor = params.get('adaptive_factor', 1.0)
        else:
            adaptive_factor = 1.0
        
        base_metrics = simulate_trading_strategy(params)
        
        # Apply adaptive factor
        for key in base_metrics:
            if key != 'win_rate':
                base_metrics[key] *= adaptive_factor
        
        return base_metrics
    
    # Create custom Optuna study with conditional parameters
    import optuna
    
    def objective_with_conditions(trial):
        params = {
            'lookback': trial.suggest_int('lookback', 10, 50),
            'threshold': trial.suggest_float('threshold', 0.1, 0.9),
            'stop_loss': trial.suggest_float('stop_loss', 0.01, 0.05),
            'take_profit': trial.suggest_float('take_profit', 0.02, 0.10),
            'use_adaptive': trial.suggest_categorical('use_adaptive', [True, False])
        }
        
        # Conditional parameter
        if params['use_adaptive']:
            params['adaptive_factor'] = trial.suggest_float('adaptive_factor', 0.5, 2.0)
        
        metrics = strategy_with_conditions(params)
        return metrics['sharpe_ratio']
    
    study = optuna.create_study(direction='maximize')
    study.optimize(objective_with_conditions, n_trials=30, show_progress_bar=False)
    
    print(f"Best parameters with conditions:")
    for param, value in study.best_params.items():
        print(f"  {param}: {value}")
    print(f"Best value: {study.best_value:.4f}")
    
    # 2. Multi-objective optimization
    print("\n2. MULTI-OBJECTIVE OPTIMIZATION")
    print("-" * 40)
    
    adapter = MultiObjectiveOptunaAdapter(simulate_trading_strategy, metric_adapter)
    
    param_space = {
        'lookback': {'type': 'int', 'low': 10, 'high': 50},
        'threshold': {'type': 'float', 'low': 0.1, 'high': 0.9},
        'stop_loss': {'type': 'float', 'low': 0.01, 'high': 0.05},
        'take_profit': {'type': 'float', 'low': 0.02, 'high': 0.10}
    }
    
    # Optimize for both Sharpe ratio and Calmar ratio
    pareto_front = adapter.optimize(
        param_space,
        objectives=['sharpe_ratio', 'calmar_ratio'],
        n_trials=50,
        verbose=False
    )
    
    print(f"Found {len(pareto_front)} Pareto-optimal solutions")
    print("\nTop 3 solutions:")
    for i, solution in enumerate(pareto_front[:3], 1):
        print(f"\nSolution {i}:")
        print(f"  Sharpe Ratio: {solution.metrics['sharpe_ratio']:.4f}")
        print(f"  Calmar Ratio: {solution.metrics['calmar_ratio']:.4f}")
    
    # 3. Pruning unpromising trials
    print("\n3. PRUNING WITH MEDIAN PRUNER")
    print("-" * 40)
    
    optimizer = OptunaAdapter(simulate_trading_strategy, metric_adapter)
    
    param_space = {
        'lookback': (10, 50),
        'threshold': (0.1, 0.9),
        'stop_loss': (0.01, 0.05),
        'take_profit': (0.02, 0.10)
    }
    
    result = optimizer.optimize(
        param_space,
        n_trials=50,
        sampler='tpe',
        pruner='median',  # Enable pruning
        verbose=False,
        seed=42
    )
    
    stats = optimizer.get_study_statistics()
    print(f"Optimization Statistics:")
    print(f"  Total trials: {stats['n_trials']}")
    print(f"  Completed: {stats['n_complete']}")
    print(f"  Pruned: {stats['n_pruned']}")
    print(f"  Failed: {stats['n_failed']}")
    print(f"  Best value: {stats['best_value']:.4f}")
    
    # 4. Different samplers comparison
    print("\n4. SAMPLER COMPARISON")
    print("-" * 40)
    
    samplers = ['tpe', 'random', 'cmaes']
    sampler_results = {}
    
    for sampler_name in samplers:
        optimizer = OptunaAdapter(simulate_trading_strategy, metric_adapter)
        try:
            result = optimizer.optimize(
                param_space,
                n_trials=30,
                sampler=sampler_name,
                verbose=False,
                seed=42
            )
            sampler_results[sampler_name] = result.score
            print(f"  {sampler_name.upper()}: {result.score:.4f}")
        except Exception as e:
            print(f"  {sampler_name.upper()}: Failed - {str(e)}")


def main():
    """Run all examples"""
    
    # Install optuna if not available
    try:
        import optuna
    except ImportError:
        print("Installing Optuna...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'optuna'])
        print("Optuna installed successfully!")
    
    # Run comparisons
    compare_optimization_methods()
    
    # Demonstrate advanced features
    demonstrate_optuna_advanced_features()
    
    print("\n" + "=" * 80)
    print("Optuna Integration Complete!")
    print("=" * 80)
    print("\nKey Benefits of Optuna Integration:")
    print("  ✓ Advanced sampling algorithms (TPE, CMA-ES)")
    print("  ✓ Conditional parameter spaces")
    print("  ✓ Multi-objective optimization")
    print("  ✓ Automatic pruning of bad trials")
    print("  ✓ Parallel optimization support")
    print("  ✓ Visualization tools")
    print("\nUse Cases:")
    print("  • Complex strategy optimization with many parameters")
    print("  • Multi-objective optimization (e.g., maximize return while minimizing risk)")
    print("  • Large-scale hyperparameter search with pruning")
    print("  • Conditional parameters (e.g., use parameter B only if A is enabled)")


if __name__ == "__main__":
    main()