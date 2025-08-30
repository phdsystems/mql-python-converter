"""
Unit tests for optimization adapter pattern implementation
"""

import unittest
import numpy as np
import sys
import os
from typing import Dict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.optimization_adapter import (
    OptimizationResult, OptimizationFactory,
    GridSearchAdapter, RandomSearchAdapter,
    GeneticAlgorithmAdapter, BayesianOptimizationAdapter,
    HybridOptimizer
)
from tools.metrics_adapter import SharpeRatioAdapter


class TestOptimizationResult(unittest.TestCase):
    """Test OptimizationResult class"""
    
    def test_optimization_result_creation(self):
        """Test creating optimization result"""
        result = OptimizationResult(
            parameters={'a': 1, 'b': 2},
            score=0.5,
            metrics={'sharpe': 0.5, 'return': 10.0},
            method='test_method',
            iterations=100
        )
        
        self.assertEqual(result.parameters['a'], 1)
        self.assertEqual(result.score, 0.5)
        self.assertEqual(result.method, 'test_method')
        self.assertEqual(result.iterations, 100)
    
    def test_optimization_result_to_dict(self):
        """Test converting result to dictionary"""
        result = OptimizationResult(
            parameters={'a': 1},
            score=0.5,
            metrics={'sharpe': 0.5},
            method='test',
            iterations=10,
            convergence_history=[0.1, 0.3, 0.5]
        )
        
        dict_result = result.to_dict()
        self.assertIn('parameters', dict_result)
        self.assertIn('score', dict_result)
        self.assertIn('convergence_history', dict_result)
        self.assertEqual(len(dict_result['convergence_history']), 3)


class TestOptimizationAdapters(unittest.TestCase):
    """Test individual optimization adapters"""
    
    def setUp(self):
        """Set up test objective function"""
        # Simple quadratic function: -(x-5)^2 - (y-3)^2
        # Maximum at x=5, y=3
        def objective(params: Dict) -> Dict:
            x = params.get('x', 0)
            y = params.get('y', 0)
            score = -(x - 5)**2 - (y - 3)**2
            return {'test_metric': score}
        
        self.objective = objective
        self.metric = SharpeRatioAdapter()  # Use any metric adapter
        
        # Override metric name for testing
        self.metric.get_name = lambda: 'test_metric'
    
    def test_grid_search_adapter(self):
        """Test Grid Search optimization"""
        adapter = GridSearchAdapter(self.objective, self.metric)
        
        param_space = {
            'x': [3, 4, 5, 6, 7],
            'y': [1, 2, 3, 4, 5]
        }
        
        result = adapter.optimize(param_space, verbose=False)
        
        # Should find optimum at x=5, y=3
        self.assertEqual(result.parameters['x'], 5)
        self.assertEqual(result.parameters['y'], 3)
        self.assertEqual(result.score, 0.0)  # Maximum value
        self.assertEqual(result.method, 'grid_search')
        self.assertEqual(result.iterations, 25)  # 5x5 grid
    
    def test_random_search_adapter(self):
        """Test Random Search optimization"""
        adapter = RandomSearchAdapter(self.objective, self.metric)
        
        param_space = {
            'x': (0, 10),
            'y': (0, 6)
        }
        
        result = adapter.optimize(param_space, n_iter=100, seed=42, verbose=False)
        
        # Should find something close to optimum
        self.assertAlmostEqual(result.parameters['x'], 5, delta=2)
        self.assertAlmostEqual(result.parameters['y'], 3, delta=2)
        self.assertGreater(result.score, -10)  # Should be reasonably good
        self.assertEqual(result.method, 'random_search')
        self.assertEqual(result.iterations, 100)
    
    def test_genetic_algorithm_adapter(self):
        """Test Genetic Algorithm optimization"""
        adapter = GeneticAlgorithmAdapter(self.objective, self.metric)
        
        param_space = {
            'x': (0, 10),
            'y': (0, 6)
        }
        
        result = adapter.optimize(
            param_space,
            population_size=20,
            generations=10,
            mutation_rate=0.1,
            crossover_rate=0.8,
            elite_size=3,
            seed=42,
            verbose=False
        )
        
        # Should converge near optimum
        self.assertAlmostEqual(result.parameters['x'], 5, delta=2)
        self.assertAlmostEqual(result.parameters['y'], 3, delta=2)
        self.assertGreater(result.score, -5)
        self.assertEqual(result.method, 'genetic_algorithm')
        self.assertGreater(result.iterations, 0)
    
    def test_bayesian_optimization_adapter(self):
        """Test Bayesian Optimization"""
        adapter = BayesianOptimizationAdapter(self.objective, self.metric)
        
        param_space = {
            'x': (0, 10),
            'y': (0, 6)
        }
        
        result = adapter.optimize(
            param_space,
            n_iter=30,
            n_initial=5,
            seed=42,
            verbose=False
        )
        
        # Should find good solution
        self.assertIsNotNone(result.parameters)
        self.assertIn('x', result.parameters)
        self.assertIn('y', result.parameters)
        self.assertEqual(result.method, 'bayesian_optimization')
        self.assertEqual(result.iterations, 30)


class TestOptimizationFactory(unittest.TestCase):
    """Test OptimizationFactory functionality"""
    
    def setUp(self):
        """Set up test function and metric"""
        self.objective = lambda x: {'metric': sum(x.values())}
        self.metric = SharpeRatioAdapter()
        self.metric.get_name = lambda: 'metric'
    
    def test_create_optimizer(self):
        """Test creating optimizers by name"""
        optimizer = OptimizationFactory.create('grid_search', self.objective, self.metric)
        self.assertIsInstance(optimizer, GridSearchAdapter)
        
        optimizer = OptimizationFactory.create('random_search', self.objective, self.metric)
        self.assertIsInstance(optimizer, RandomSearchAdapter)
        
        optimizer = OptimizationFactory.create('genetic_algorithm', self.objective, self.metric)
        self.assertIsInstance(optimizer, GeneticAlgorithmAdapter)
    
    def test_list_available_methods(self):
        """Test listing available methods"""
        methods = OptimizationFactory.list_available()
        self.assertIn('grid_search', methods)
        self.assertIn('random_search', methods)
        self.assertIn('genetic_algorithm', methods)
        self.assertIn('bayesian_optimization', methods)
    
    def test_invalid_method(self):
        """Test creating invalid method raises error"""
        with self.assertRaises(ValueError):
            OptimizationFactory.create('invalid_method', self.objective, self.metric)


class TestHybridOptimizer(unittest.TestCase):
    """Test HybridOptimizer functionality"""
    
    def setUp(self):
        """Set up test objective"""
        # Rosenbrock function (challenging optimization problem)
        def rosenbrock(params: Dict) -> Dict:
            x = params.get('x', 0)
            y = params.get('y', 0)
            score = -((1 - x)**2 + 100 * (y - x**2)**2)
            return {'metric': score}
        
        self.objective = rosenbrock
        self.metric = SharpeRatioAdapter()
        self.metric.get_name = lambda: 'metric'
    
    def test_hybrid_optimization(self):
        """Test hybrid optimization with multiple methods"""
        optimizer = HybridOptimizer(
            self.objective,
            self.metric,
            methods=['random_search', 'genetic_algorithm']
        )
        
        param_space = {
            'x': (-2, 2),
            'y': (-2, 2)
        }
        
        # Note: Different methods accept different parameters
        # HybridOptimizer should handle this internally
        result = optimizer.optimize(
            param_space,
            verbose=False
        )
        
        # Should find reasonable solution
        self.assertIsNotNone(result.parameters)
        self.assertIn('random_search', result.method)
        self.assertIn('genetic_algorithm', result.method)
        self.assertGreater(result.iterations, 0)
    
    def test_hybrid_search_space_refinement(self):
        """Test that hybrid optimizer refines search space"""
        optimizer = HybridOptimizer(
            self.objective,
            self.metric,
            methods=['random_search']
        )
        
        # Test _refine_search_space method
        original_space = {
            'x': (-10, 10),
            'y': (-10, 10)
        }
        
        best_params = {'x': 0, 'y': 0}
        
        refined_space = optimizer._refine_search_space(original_space, best_params)
        
        # Should narrow the search space
        self.assertGreater(refined_space['x'][0], original_space['x'][0])
        self.assertLess(refined_space['x'][1], original_space['x'][1])
        self.assertGreater(refined_space['y'][0], original_space['y'][0])
        self.assertLess(refined_space['y'][1], original_space['y'][1])


class TestOptimizationConsistency(unittest.TestCase):
    """Test consistency across optimization methods"""
    
    def setUp(self):
        """Set up simple objective for consistency testing"""
        # Simple convex function with known optimum
        def simple_objective(params: Dict) -> Dict:
            x = params.get('x', 0)
            score = -(x - 10)**2 + 100  # Maximum at x=10, value=100
            return {'metric': score}
        
        self.objective = simple_objective
        self.metric = SharpeRatioAdapter()
        self.metric.get_name = lambda: 'metric'
    
    def test_all_methods_find_optimum(self):
        """Test that all methods can find simple optimum"""
        param_space_discrete = {'x': list(range(0, 21))}
        param_space_continuous = {'x': (0, 20)}
        
        methods_to_test = [
            ('grid_search', param_space_discrete, {}),
            ('random_search', param_space_continuous, {'n_iter': 50, 'seed': 42}),
            ('genetic_algorithm', param_space_continuous, 
             {'population_size': 20, 'generations': 10, 'seed': 42}),
            ('bayesian_optimization', param_space_continuous,
             {'n_iter': 30, 'seed': 42})
        ]
        
        for method_name, param_space, kwargs in methods_to_test:
            optimizer = OptimizationFactory.create(
                method_name, self.objective, self.metric
            )
            
            result = optimizer.optimize(param_space, verbose=False, **kwargs)
            
            # All methods should find x close to 10
            self.assertAlmostEqual(result.parameters['x'], 10, delta=2,
                                 msg=f"{method_name} failed to find optimum")
            self.assertGreater(result.score, 90,
                             msg=f"{method_name} score too low")
    
    def test_convergence_history(self):
        """Test that convergence history is tracked"""
        optimizer = RandomSearchAdapter(self.objective, self.metric)
        
        result = optimizer.optimize(
            {'x': (0, 20)},
            n_iter=20,
            seed=42,
            verbose=False
        )
        
        self.assertIsNotNone(result.convergence_history)
        self.assertEqual(len(result.convergence_history), 20)
        
        # Should generally improve over time (best score should be near end)
        max_score = max(result.convergence_history)
        self.assertEqual(result.score, max_score)
    
    def test_discrete_vs_continuous_parameters(self):
        """Test handling of discrete and continuous parameters"""
        def multi_param_objective(params: Dict) -> Dict:
            x = params.get('x', 0)  # Continuous
            y = params.get('y', 0)  # Discrete
            score = -(x - 5)**2 - abs(y - 3)
            return {'metric': score}
        
        optimizer = RandomSearchAdapter(multi_param_objective, self.metric)
        
        param_space = {
            'x': (0, 10),  # Continuous
            'y': [1, 2, 3, 4, 5]  # Discrete
        }
        
        result = optimizer.optimize(param_space, n_iter=50, seed=42, verbose=False)
        
        # Should handle mixed parameter types
        self.assertIn('x', result.parameters)
        self.assertIn('y', result.parameters)
        self.assertIn(result.parameters['y'], [1, 2, 3, 4, 5])
        self.assertTrue(0 <= result.parameters['x'] <= 10)


def run_tests():
    """Run all tests with summary"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()