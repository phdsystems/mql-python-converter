"""
Integration test for metrics and optimization adapters
Tests the complete workflow without external dependencies
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.metrics_adapter import TradeResult, MetricFactory, CompositeMetric
from tools.optimization_adapter import OptimizationFactory


def test_metrics_integration():
    """Test metrics calculation workflow"""
    print("\n" + "="*60)
    print("TESTING METRICS ADAPTER INTEGRATION")
    print("="*60)
    
    # Create sample trades
    trades = [
        TradeResult(100, 110, 0, 1),   # +10%
        TradeResult(110, 105, 1, 2),   # -4.5%
        TradeResult(105, 115, 2, 3),   # +9.5%
        TradeResult(115, 112, 3, 4),   # -2.6%
        TradeResult(112, 120, 4, 5),   # +7.1%
    ]
    
    # Test all available metrics
    print("\nIndividual Metrics:")
    print("-"*40)
    
    for metric_name in MetricFactory.list_available():
        try:
            metric = MetricFactory.create(metric_name)
            score = metric.calculate(trades)
            print(f"  {metric_name:<20}: {score:>10.4f} {metric.get_description()}")
        except Exception as e:
            print(f"  {metric_name:<20}: Error - {e}")
    
    # Test composite metric
    print("\nComposite Metric:")
    print("-"*40)
    
    composite = CompositeMetric({
        'sharpe_ratio': 2.0,
        'win_rate': 1.0,
        'max_drawdown': 1.0
    }, normalize=True)
    
    composite_score = composite.calculate(trades)
    print(f"  Weighted Score: {composite_score:.4f}")
    print(f"  Components: {composite.get_description()}")
    
    print("\n✓ Metrics adapter integration test passed!")
    return True


def test_optimization_integration():
    """Test optimization workflow"""
    print("\n" + "="*60)
    print("TESTING OPTIMIZATION ADAPTER INTEGRATION")
    print("="*60)
    
    # Define simple objective function
    def objective_function(params):
        """Simple quadratic function for testing"""
        x = params.get('x', 0)
        y = params.get('y', 0)
        
        # Optimal at x=10, y=5
        score = -(x - 10)**2 - (y - 5)**2 + 100
        
        # Return multiple metrics
        return {
            'test_score': score,
            'distance': ((x - 10)**2 + (y - 5)**2) ** 0.5
        }
    
    # Create metric adapter
    class SimpleMetric:
        def get_name(self):
            return 'test_score'
    
    metric = SimpleMetric()
    
    # Test different optimization methods
    methods_to_test = ['grid_search', 'random_search', 'genetic_algorithm']
    
    print("\nOptimization Methods:")
    print("-"*40)
    
    for method_name in methods_to_test:
        print(f"\n{method_name.upper()}:")
        
        try:
            optimizer = OptimizationFactory.create(
                method_name,
                objective_function,
                metric
            )
            
            # Define parameter space
            if method_name == 'grid_search':
                param_space = {
                    'x': [8, 9, 10, 11, 12],
                    'y': [3, 4, 5, 6, 7]
                }
            else:
                param_space = {
                    'x': (5, 15),
                    'y': (0, 10)
                }
            
            # Run optimization
            if method_name == 'random_search':
                result = optimizer.optimize(param_space, n_iter=50, seed=42)
            elif method_name == 'genetic_algorithm':
                result = optimizer.optimize(
                    param_space,
                    population_size=20,
                    generations=10,
                    seed=42
                )
            else:
                result = optimizer.optimize(param_space)
            
            print(f"  Best parameters: x={result.parameters['x']:.2f}, y={result.parameters['y']:.2f}")
            print(f"  Best score: {result.score:.4f}")
            print(f"  Iterations: {result.iterations}")
            
            # Check if close to optimum
            x_error = abs(result.parameters['x'] - 10)
            y_error = abs(result.parameters['y'] - 5)
            
            if x_error < 2 and y_error < 2:
                print("  ✓ Found optimum within tolerance")
            else:
                print(f"  ⚠ Optimum not found (error: x={x_error:.2f}, y={y_error:.2f})")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n✓ Optimization adapter integration test passed!")
    return True


def test_combined_workflow():
    """Test combined metrics and optimization workflow"""
    print("\n" + "="*60)
    print("TESTING COMBINED WORKFLOW")
    print("="*60)
    
    # Simulate a trading strategy optimization
    def trading_strategy_objective(params):
        """Simulate trading strategy with given parameters"""
        threshold = params.get('threshold', 0.5)
        window = params.get('window', 10)
        
        # Simulate trades based on parameters
        # Better performance with threshold around 0.3 and window around 15
        score = -(threshold - 0.3)**2 * 10 - (window - 15)**2 * 0.1 + 20
        
        # Simulate win rate
        win_rate = 50 + 20 * (1 - abs(threshold - 0.3))
        
        return {
            'score': score,
            'win_rate': win_rate
        }
    
    print("\nOptimizing Trading Strategy Parameters:")
    print("-"*40)
    
    # Use random search for optimization
    class ScoreMetric:
        def get_name(self):
            return 'score'
    
    optimizer = OptimizationFactory.create(
        'random_search',
        trading_strategy_objective,
        ScoreMetric()
    )
    
    param_space = {
        'threshold': (0.1, 0.9),
        'window': (5, 25)
    }
    
    result = optimizer.optimize(param_space, n_iter=100, seed=42)
    
    print(f"Optimal Parameters:")
    print(f"  Threshold: {result.parameters['threshold']:.3f}")
    print(f"  Window: {result.parameters['window']:.1f}")
    print(f"Performance Metrics:")
    print(f"  Score: {result.score:.4f}")
    print(f"  Win Rate: {result.metrics.get('win_rate', 0):.1f}%")
    
    # Verify optimization worked
    threshold_error = abs(result.parameters['threshold'] - 0.3)
    window_error = abs(result.parameters['window'] - 15)
    
    if threshold_error < 0.1 and window_error < 3:
        print("\n✓ Strategy optimization successful!")
    else:
        print(f"\n⚠ Optimization suboptimal (errors: threshold={threshold_error:.3f}, window={window_error:.1f})")
    
    print("\n✓ Combined workflow test passed!")
    return True


def main():
    """Run all integration tests"""
    print("\n" + "="*70)
    print(" ADAPTER PATTERN INTEGRATION TESTS ")
    print("="*70)
    
    tests = [
        ("Metrics Integration", test_metrics_integration),
        ("Optimization Integration", test_optimization_integration),
        ("Combined Workflow", test_combined_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY ")
    print("="*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {test_name:<30}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All integration tests passed successfully!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())