"""
Unit tests for Optuna adapter integration
"""

import unittest
import numpy as np
import warnings
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.optuna_adapter import OptunaAdapter, MultiObjectiveOptunaAdapter, register_optuna_adapters
from tools.optimization_adapter import OptimizationFactory
from tools.metrics_adapter import SharpeRatioAdapter, TotalReturnAdapter, CalmarRatioAdapter


class TestOptunaAdapter(unittest.TestCase):
    """Test cases for OptunaAdapter"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.metric_adapter = SharpeRatioAdapter()
        
        # Simple objective function for testing
        def test_objective(params):
            x = params.get('x', 0)
            y = params.get('y', 0)
            z = params.get('z', 'a')
            
            # Handle categorical y parameter in some test cases
            if isinstance(y, str):
                y = {'a': 5, 'b': 10, 'c': 15}.get(y, 10)
            
            # Simple function with optimum at x=5, y=10
            score = -(x - 5)**2 - (y - 10)**2
            
            # Add categorical effect
            if z == 'b':
                score += 5
            elif z == 'c':
                score += 10
            
            return {
                'sharpe_ratio': score,
                'total_return': score * 0.8,
                'max_drawdown': -abs(score * 0.1)
            }
        
        self.objective_function = test_objective
        
    def test_basic_optimization(self):
        """Test basic optimization functionality"""
        adapter = OptunaAdapter(self.objective_function, self.metric_adapter)
        
        param_space = {
            'x': (0, 10),
            'y': (0, 20),
            'z': ['a', 'b', 'c']
        }
        
        result = adapter.optimize(
            param_space,
            n_trials=30,
            sampler='tpe',
            verbose=False,
            seed=42
        )
        
        # Check result structure
        self.assertIsNotNone(result)
        self.assertIn('x', result.parameters)
        self.assertIn('y', result.parameters)
        self.assertIn('z', result.parameters)
        self.assertIsNotNone(result.score)
        self.assertIsNotNone(result.metrics)
        
        # Check that optimization improved from random
        self.assertGreater(result.score, -200)  # Should be better than random
        
        # Check convergence history
        self.assertEqual(len(result.convergence_history), 30)
    
    def test_different_samplers(self):
        """Test different sampling strategies"""
        adapter = OptunaAdapter(self.objective_function, self.metric_adapter)
        
        param_space = {
            'x': (0, 10),
            'y': (0, 20)
        }
        
        samplers = ['tpe', 'random']
        results = {}
        
        for sampler in samplers:
            result = adapter.optimize(
                param_space,
                n_trials=20,
                sampler=sampler,
                verbose=False,
                seed=42
            )
            results[sampler] = result
            
            # Basic checks
            self.assertIsNotNone(result)
            self.assertEqual(result.method, 'optuna')
        
        # TPE should generally perform better than random
        # Note: Due to randomness, we check if TPE is not significantly worse
        self.assertGreater(results['tpe'].score, results['random'].score - 50)
    
    def test_integer_parameters(self):
        """Test integer parameter optimization"""
        adapter = OptunaAdapter(self.objective_function, self.metric_adapter)
        
        param_space = {
            'x': {'type': 'int', 'low': 0, 'high': 10},
            'y': {'type': 'int', 'low': 0, 'high': 20}
        }
        
        result = adapter.optimize(
            param_space,
            n_trials=20,
            verbose=False
        )
        
        # Check that parameters are integers
        self.assertIsInstance(result.parameters['x'], int)
        self.assertIsInstance(result.parameters['y'], int)
        
        # Check bounds
        self.assertGreaterEqual(result.parameters['x'], 0)
        self.assertLessEqual(result.parameters['x'], 10)
        self.assertGreaterEqual(result.parameters['y'], 0)
        self.assertLessEqual(result.parameters['y'], 20)
    
    def test_log_scale_parameters(self):
        """Test log-scale parameter optimization"""
        def log_objective(params):
            # Function sensitive to log-scale parameters
            lr = params.get('learning_rate', 0.01)
            score = -abs(np.log10(lr) + 3)  # Optimum at lr=0.001
            return {'sharpe_ratio': score}
        
        adapter = OptunaAdapter(log_objective, self.metric_adapter)
        
        param_space = {
            'learning_rate': {
                'type': 'float',
                'low': 1e-5,
                'high': 1e-1,
                'log': True
            }
        }
        
        result = adapter.optimize(
            param_space,
            n_trials=30,
            verbose=False
        )
        
        # Check that optimization found something near 0.001
        self.assertGreater(result.parameters['learning_rate'], 1e-4)
        self.assertLess(result.parameters['learning_rate'], 1e-2)
    
    def test_pruning(self):
        """Test trial pruning functionality"""
        def slow_objective(params):
            # Objective that reports intermediate values
            x = params.get('x', 0)
            score = -(x - 5)**2
            return {'sharpe_ratio': score}
        
        adapter = OptunaAdapter(slow_objective, self.metric_adapter)
        
        param_space = {'x': (0, 10)}
        
        # Test with median pruner
        result = adapter.optimize(
            param_space,
            n_trials=20,
            pruner='median',
            verbose=False
        )
        
        self.assertIsNotNone(result)
        stats = adapter.get_study_statistics()
        
        # Check statistics structure
        self.assertIn('n_trials', stats)
        self.assertIn('n_complete', stats)
        self.assertIn('n_pruned', stats)
        self.assertIn('best_value', stats)
    
    def test_multi_objective_optimization(self):
        """Test multi-objective optimization"""
        adapter = MultiObjectiveOptunaAdapter(self.objective_function, self.metric_adapter)
        
        param_space = {
            'x': {'type': 'float', 'low': 0, 'high': 10},
            'y': {'type': 'float', 'low': 0, 'high': 20}
        }
        
        # Optimize for multiple objectives
        pareto_front = adapter.optimize(
            param_space,
            objectives=['sharpe_ratio', 'total_return'],
            n_trials=30,
            verbose=False
        )
        
        # Check that we got a list of solutions
        self.assertIsInstance(pareto_front, list)
        self.assertGreater(len(pareto_front), 0)
        
        # Check each solution
        for solution in pareto_front:
            self.assertIn('sharpe_ratio', solution.metrics)
            self.assertIn('total_return', solution.metrics)
            self.assertIsNotNone(solution.parameters)
    
    def test_param_space_parsing(self):
        """Test different parameter space formats"""
        adapter = OptunaAdapter(self.objective_function, self.metric_adapter)
        
        # Test various formats
        param_spaces = [
            # Tuple format for continuous
            {'x': (0, 10), 'y': (0.0, 20.0)},
            
            # List format for categorical
            {'x': [1, 2, 3, 4, 5], 'y': ['a', 'b', 'c']},
            
            # Dict format with type specification
            {
                'x': {'type': 'int', 'low': 0, 'high': 10},
                'y': {'type': 'float', 'low': 0, 'high': 20},
                'z': {'type': 'categorical', 'choices': ['a', 'b', 'c']}
            },
            
            # Mixed formats
            {
                'x': (0, 10),
                'y': ['option1', 'option2'],
                'z': {'type': 'float', 'low': 0.1, 'high': 0.9}
            }
        ]
        
        for param_space in param_spaces:
            result = adapter.optimize(
                param_space,
                n_trials=5,
                verbose=False
            )
            
            # Check that all parameters are present
            for param_name in param_space.keys():
                self.assertIn(param_name, result.parameters)
    
    def test_timeout(self):
        """Test optimization with timeout"""
        import time
        
        def slow_objective(params):
            time.sleep(0.01)  # Small delay
            x = params.get('x', 0)
            return {'sharpe_ratio': -(x - 5)**2}
        
        adapter = OptunaAdapter(slow_objective, self.metric_adapter)
        
        param_space = {'x': (0, 10)}
        
        # Run with 0.1 second timeout
        result = adapter.optimize(
            param_space,
            n_trials=100,  # Would take ~1 second without timeout
            timeout=0.1,
            verbose=False
        )
        
        # Should have completed fewer trials due to timeout
        self.assertIsNotNone(result)
        self.assertLess(len(adapter.convergence_history), 20)
    
    def test_parallel_optimization(self):
        """Test parallel optimization with n_jobs"""
        adapter = OptunaAdapter(self.objective_function, self.metric_adapter)
        
        param_space = {
            'x': (0, 10),
            'y': (0, 20)
        }
        
        # Test with 2 parallel jobs
        result = adapter.optimize(
            param_space,
            n_trials=20,
            n_jobs=2,
            verbose=False
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(len(adapter.convergence_history), 20)
    
    def test_grid_sampler(self):
        """Test grid search sampler"""
        adapter = OptunaAdapter(self.objective_function, self.metric_adapter)
        
        param_space = {
            'x': (0, 10),
            'z': ['a', 'b', 'c']  # Use z for categorical, not y
        }
        
        result = adapter.optimize(
            param_space,
            n_trials=30,
            sampler='grid',
            verbose=False
        )
        
        self.assertIsNotNone(result)
        # Grid search should explore systematically
        self.assertIn(result.parameters['z'], ['a', 'b', 'c'])
    
    def test_study_statistics(self):
        """Test study statistics retrieval"""
        adapter = OptunaAdapter(self.objective_function, self.metric_adapter)
        
        # Before optimization
        stats = adapter.get_study_statistics()
        self.assertEqual(stats, {})
        
        # After optimization
        param_space = {'x': (0, 10)}
        adapter.optimize(param_space, n_trials=10, verbose=False)
        
        stats = adapter.get_study_statistics()
        self.assertIn('n_trials', stats)
        self.assertIn('best_value', stats)
        self.assertIn('best_params', stats)
        self.assertIn('n_complete', stats)
        self.assertEqual(stats['n_trials'], 10)
    
    def test_factory_registration(self):
        """Test registration with OptimizationFactory"""
        # Register adapters
        success = register_optuna_adapters()
        
        if success:
            # Check that Optuna is available in factory
            available_methods = OptimizationFactory.list_available()
            self.assertIn('optuna', available_methods)
            
            # Create through factory
            adapter = OptimizationFactory.create(
                'optuna',
                self.objective_function,
                self.metric_adapter
            )
            
            self.assertIsInstance(adapter, OptunaAdapter)
            
            # Test optimization through factory-created adapter
            param_space = {'x': (0, 10)}
            result = adapter.optimize(param_space, n_trials=5, verbose=False)
            self.assertIsNotNone(result)
    
    def test_minimize_direction(self):
        """Test minimization instead of maximization"""
        def minimize_objective(params):
            x = params.get('x', 0)
            # Function to minimize (minimum at x=5)
            score = (x - 5)**2
            return {'sharpe_ratio': score}
        
        adapter = OptunaAdapter(minimize_objective, self.metric_adapter)
        
        param_space = {'x': (0, 10)}
        
        result = adapter.optimize(
            param_space,
            n_trials=30,
            direction='minimize',
            verbose=False
        )
        
        # Should find x near 5
        self.assertAlmostEqual(result.parameters['x'], 5, delta=2)
        # Score should be low (near 0)
        self.assertLess(result.score, 10)
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        adapter = OptunaAdapter(self.objective_function, self.metric_adapter)
        
        # Test invalid sampler
        with self.assertRaises(ValueError):
            adapter.optimize(
                {'x': (0, 10)},
                sampler='invalid_sampler',
                verbose=False
            )
        
        # Test invalid pruner
        with self.assertRaises(ValueError):
            adapter.optimize(
                {'x': (0, 10)},
                pruner='invalid_pruner',
                verbose=False
            )
        
        # Test invalid parameter definition
        with self.assertRaises(ValueError):
            adapter.optimize(
                {'x': 'invalid'},  # Invalid format
                verbose=False
            )


class TestOptunaIntegration(unittest.TestCase):
    """Integration tests comparing Optuna with other optimizers"""
    
    def setUp(self):
        """Set up test fixtures"""
        register_optuna_adapters()
        
        # Rosenbrock function for testing
        def rosenbrock(params):
            x = params.get('x', 0)
            y = params.get('y', 0)
            score = -((1 - x)**2 + 100 * (y - x**2)**2)
            return {
                'sharpe_ratio': score,
                'total_return': score * 0.9
            }
        
        self.objective = rosenbrock
        self.metric_adapter = SharpeRatioAdapter()
        self.param_space = {
            'x': (-2.0, 2.0),
            'y': (-2.0, 2.0)
        }
    
    def test_optuna_vs_random_search(self):
        """Compare Optuna TPE with Random Search"""
        # Random Search
        random_optimizer = OptimizationFactory.create(
            'random_search',
            self.objective,
            self.metric_adapter
        )
        random_result = random_optimizer.optimize(
            self.param_space,
            n_iter=50,
            verbose=False,
            seed=42
        )
        
        # Optuna TPE
        optuna_optimizer = OptimizationFactory.create(
            'optuna',
            self.objective,
            self.metric_adapter
        )
        optuna_result = optuna_optimizer.optimize(
            self.param_space,
            n_trials=50,
            sampler='tpe',
            verbose=False,
            seed=42
        )
        
        # Optuna should perform at least as well as random search
        self.assertGreaterEqual(optuna_result.score, random_result.score - 10)
    
    def test_optuna_vs_bayesian(self):
        """Compare Optuna with simplified Bayesian optimization"""
        # Bayesian Optimization
        bayesian_optimizer = OptimizationFactory.create(
            'bayesian_optimization',
            self.objective,
            self.metric_adapter
        )
        bayesian_result = bayesian_optimizer.optimize(
            self.param_space,
            n_iter=30,
            verbose=False,
            seed=42
        )
        
        # Optuna
        optuna_optimizer = OptimizationFactory.create(
            'optuna',
            self.objective,
            self.metric_adapter
        )
        optuna_result = optuna_optimizer.optimize(
            self.param_space,
            n_trials=30,
            verbose=False,
            seed=42
        )
        
        # Both should find reasonable solutions
        self.assertGreater(bayesian_result.score, -100)
        self.assertGreater(optuna_result.score, -100)
    
    def test_all_optimizers_consistency(self):
        """Test that all optimizers return consistent result formats"""
        methods = ['random_search', 'genetic_algorithm', 'bayesian_optimization', 'optuna']
        
        for method in methods:
            with self.subTest(method=method):
                optimizer = OptimizationFactory.create(
                    method,
                    self.objective,
                    self.metric_adapter
                )
                
                # Set appropriate parameters for each method
                if method == 'optuna':
                    result = optimizer.optimize(
                        self.param_space,
                        n_trials=10,
                        verbose=False
                    )
                elif method == 'genetic_algorithm':
                    result = optimizer.optimize(
                        self.param_space,
                        population_size=10,
                        generations=2,
                        verbose=False
                    )
                else:
                    result = optimizer.optimize(
                        self.param_space,
                        n_iter=10,
                        verbose=False
                    )
                
                # Check consistent result format
                self.assertIsNotNone(result.parameters)
                self.assertIsNotNone(result.score)
                self.assertIsNotNone(result.metrics)
                self.assertIsNotNone(result.method)
                self.assertIsNotNone(result.iterations)
                self.assertIn('x', result.parameters)
                self.assertIn('y', result.parameters)


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)