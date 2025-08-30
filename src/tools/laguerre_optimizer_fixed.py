"""
Fixed Laguerre Optimizer with proper metric calculations using adapter pattern
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.adaptive_laguerre_filter import AdaptiveLaguerreFilter, SmoothMode
from tools.metrics_adapter import (
    MetricFactory, TradeResult, CompositeMetric
)
from tools.optimization_adapter import OptimizationFactory


class LaguerreOptimizer:
    """
    Optimizer for Adaptive Laguerre Filter using adapter patterns
    """
    
    def __init__(self, 
                 price_data: np.ndarray,
                 metric_name: str = 'sharpe_ratio',
                 train_ratio: float = 0.7):
        """
        Initialize optimizer with metric adapter
        
        Args:
            price_data: Historical price data
            metric_name: Name of metric to optimize
            train_ratio: Ratio of data for training
        """
        self.price_data = np.asarray(price_data)
        self.metric_name = metric_name
        self.train_ratio = train_ratio
        
        # Create metric adapter
        self.metric_adapter = MetricFactory.create(metric_name)
        
        # Split data
        split_idx = int(len(price_data) * train_ratio)
        self.train_data = price_data[:split_idx]
        self.test_data = price_data[split_idx:]
        
        print(f"Optimizer initialized:")
        print(f"  Metric: {self.metric_adapter.get_description()}")
        print(f"  Training samples: {len(self.train_data)}")
        print(f"  Test samples: {len(self.test_data)}")
    
    def generate_trades(self, prices: np.ndarray, filter_params: Dict) -> List[TradeResult]:
        """
        Generate trades based on Laguerre filter signals
        
        Args:
            prices: Price data
            filter_params: Filter parameters
            
        Returns:
            List of TradeResult objects
        """
        # Create and run filter
        alf = AdaptiveLaguerreFilter(**filter_params)
        result = alf.calculate(prices)
        
        laguerre = result['laguerre']
        trend = result['trend']
        
        trades = []
        position = 0  # 0: no position, 1: long
        entry_price = 0
        entry_time = 0
        
        for i in range(1, len(trend)):
            # Entry signal
            if position == 0 and trend[i] == 1 and trend[i-1] != 1:
                position = 1
                entry_price = prices[i]
                entry_time = i
            
            # Exit signal
            elif position == 1 and trend[i] == 2:
                exit_price = prices[i]
                exit_time = i
                
                trade = TradeResult(
                    entry_price=entry_price,
                    exit_price=exit_price,
                    entry_time=entry_time,
                    exit_time=exit_time
                )
                trades.append(trade)
                
                position = 0
                entry_price = 0
                entry_time = 0
        
        # Close any open position at the end
        if position == 1 and entry_price > 0:
            trade = TradeResult(
                entry_price=entry_price,
                exit_price=prices[-1],
                entry_time=entry_time,
                exit_time=len(prices) - 1
            )
            trades.append(trade)
        
        return trades
    
    def objective_function(self, params: Dict) -> Dict[str, float]:
        """
        Objective function for optimization
        
        Args:
            params: Filter parameters to evaluate
            
        Returns:
            Dictionary of metric values
        """
        try:
            # Generate trades
            trades = self.generate_trades(self.train_data, params)
            
            if not trades:
                return {self.metric_name: -999.0}
            
            # Calculate all metrics
            all_metrics = {}
            for metric_name in MetricFactory.list_available():
                try:
                    metric = MetricFactory.create(metric_name)
                    score = metric.calculate(trades, self.train_data)
                    all_metrics[metric_name] = score
                except:
                    all_metrics[metric_name] = 0.0
            
            return all_metrics
            
        except Exception as e:
            print(f"Error evaluating params {params}: {e}")
            return {self.metric_name: -999.0}
    
    def optimize(self, 
                method: str,
                param_space: Dict,
                **kwargs) -> Dict:
        """
        Run optimization using specified method
        
        Args:
            method: Optimization method name
            param_space: Parameter space definition
            **kwargs: Additional arguments for the optimization method
            
        Returns:
            Optimization results dictionary
        """
        # Create optimization adapter
        optimizer = OptimizationFactory.create(
            method, 
            self.objective_function,
            self.metric_adapter
        )
        
        # Run optimization
        result = optimizer.optimize(param_space, **kwargs)
        
        # Validate on test set
        test_trades = self.generate_trades(self.test_data, result.parameters)
        test_metrics = {}
        
        for metric_name in MetricFactory.list_available():
            try:
                metric = MetricFactory.create(metric_name)
                score = metric.calculate(test_trades, self.test_data)
                test_metrics[metric_name] = score
            except:
                test_metrics[metric_name] = 0.0
        
        # Prepare final results
        final_results = {
            'method': result.method,
            'best_parameters': result.parameters,
            'training_metrics': result.metrics,
            'test_metrics': test_metrics,
            'iterations': result.iterations,
            'train_trades': len(self.generate_trades(self.train_data, result.parameters)),
            'test_trades': len(test_trades)
        }
        
        return final_results
    
    def compare_methods(self, 
                       param_space: Dict,
                       methods: List[str] = None,
                       **kwargs) -> Dict:
        """
        Compare multiple optimization methods
        
        Args:
            param_space: Parameter space definition
            methods: List of method names to compare
            **kwargs: Additional arguments for optimization
            
        Returns:
            Comparison results
        """
        if methods is None:
            methods = ['grid_search', 'random_search', 'genetic_algorithm']
        
        comparison = {}
        
        print(f"\nComparing optimization methods for {self.metric_name}:")
        print("="*60)
        
        for method in methods:
            print(f"\nRunning {method}...")
            
            try:
                result = self.optimize(method, param_space, **kwargs)
                comparison[method] = result
                
                # Print summary
                train_score = result['training_metrics'].get(self.metric_name, 0)
                test_score = result['test_metrics'].get(self.metric_name, 0)
                
                print(f"  Best parameters: {result['best_parameters']}")
                print(f"  Training {self.metric_name}: {train_score:.4f}")
                print(f"  Test {self.metric_name}: {test_score:.4f}")
                print(f"  Test trades: {result['test_trades']}")
                
            except Exception as e:
                print(f"  Error: {e}")
                comparison[method] = {'error': str(e)}
        
        # Find best method
        best_method = None
        best_score = float('-inf')
        
        for method, result in comparison.items():
            if 'error' not in result:
                test_score = result['test_metrics'].get(self.metric_name, -999)
                if test_score > best_score:
                    best_score = test_score
                    best_method = method
        
        print("\n" + "="*60)
        print(f"BEST METHOD: {best_method}")
        print(f"Test {self.metric_name}: {best_score:.4f}")
        
        comparison['best_method'] = best_method
        comparison['best_score'] = best_score
        
        return comparison


def run_example():
    """Example usage of the fixed optimizer"""
    
    # Generate sample data
    np.random.seed(42)
    prices = 100 * np.exp(np.cumsum(np.random.randn(1000) * 0.01))
    
    # Define parameter space
    param_space_grid = {
        'length': [10, 15, 20],
        'order': [3, 4, 5],
        'adaptive_mode': [True],
        'adaptive_smooth': [5, 7]
    }
    
    param_space_random = {
        'length': (5, 30),
        'order': (2, 6),
        'adaptive_mode': [True, False],
        'adaptive_smooth': (3, 10)
    }
    
    # Test different metrics
    metrics_to_test = ['sharpe_ratio', 'total_return', 'win_rate', 'calmar_ratio']
    
    for metric in metrics_to_test:
        print(f"\n{'='*70}")
        print(f"OPTIMIZING FOR: {metric}")
        print(f"{'='*70}")
        
        optimizer = LaguerreOptimizer(prices, metric_name=metric)
        
        # Compare methods
        comparison = optimizer.compare_methods(
            param_space_grid,
            methods=['grid_search', 'random_search'],
            verbose=False,
            n_iter=20  # For random search
        )
        
        print(f"\nSummary for {metric}:")
        for method, result in comparison.items():
            if method not in ['best_method', 'best_score'] and 'error' not in result:
                print(f"  {method}: {result['test_metrics'].get(metric, 0):.4f}")


if __name__ == "__main__":
    run_example()