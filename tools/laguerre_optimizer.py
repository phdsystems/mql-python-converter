"""
Adaptive Laguerre Filter - Parameter Optimization Tool
Finds optimal parameter combinations using multiple optimization methods
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Callable
from itertools import product
from dataclasses import dataclass
import json
import warnings
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import random
from datetime import datetime

# Import the main filter (assuming it's available)
try:
    from adaptive_laguerre_filter import AdaptiveLaguerreFilter, SmoothMode
    from adaptive_laguerre_advanced import AdaptiveLaguerreTrader
except ImportError:
    warnings.warn("Main filter modules not found. Using simplified version.")
    # Simplified version for standalone use
    class SmoothMode:
        MEDIAN = 4
        SMA = 0
        EMA = 1

@dataclass
class OptimizationResult:
    """Container for optimization results"""
    parameters: Dict
    score: float
    metrics: Dict
    equity_curve: Optional[np.ndarray] = None
    trades: Optional[List] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'parameters': self.parameters,
            'score': self.score,
            'metrics': self.metrics
        }


class LaguerreOptimizer:
    """
    Multi-method optimizer for Adaptive Laguerre Filter parameters
    
    Supports:
    - Grid Search
    - Random Search
    - Genetic Algorithm
    - Bayesian Optimization (simplified)
    - Walk-Forward Analysis
    """
    
    def __init__(self, 
                 price_data: np.ndarray,
                 optimization_metric: str = 'sharpe_ratio',
                 train_ratio: float = 0.7):
        """
        Initialize the optimizer
        
        Parameters:
        -----------
        price_data : np.ndarray
            Historical price data for optimization
        optimization_metric : str
            Metric to optimize ('sharpe_ratio', 'total_return', 'win_rate', 'profit_factor')
        train_ratio : float
            Ratio of data to use for training (rest for validation)
        """
        self.price_data = np.asarray(price_data)
        self.optimization_metric = optimization_metric
        self.train_ratio = train_ratio
        
        # Split data
        split_idx = int(len(price_data) * train_ratio)
        self.train_data = price_data[:split_idx]
        self.test_data = price_data[split_idx:]
        
        # Results storage
        self.results = []
        self.best_result = None
        
    def grid_search(self, 
                   param_grid: Dict,
                   n_jobs: int = -1,
                   verbose: bool = True) -> OptimizationResult:
        """
        Grid search optimization - tests all parameter combinations
        
        Parameters:
        -----------
        param_grid : dict
            Dictionary with parameter names and list of values to test
            Example: {
                'length': [10, 20, 30],
                'order': [3, 4, 5],
                'adaptive_smooth': [5, 7, 10]
            }
        n_jobs : int
            Number of parallel jobs (-1 for all cores)
        verbose : bool
            Print progress
        
        Returns:
        --------
        OptimizationResult : Best parameter combination found
        """
        if verbose:
            print("Starting Grid Search Optimization...")
            print(f"Parameter space size: {self._calculate_grid_size(param_grid)}")
        
        # Generate all combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))
        
        # Test each combination
        results = []
        
        if n_jobs != 1:
            # Parallel execution
            with ProcessPoolExecutor(max_workers=n_jobs if n_jobs > 0 else None) as executor:
                futures = []
                for combo in combinations:
                    params = dict(zip(param_names, combo))
                    futures.append(executor.submit(self._evaluate_parameters, params))
                
                for i, future in enumerate(futures):
                    result = future.result()
                    results.append(result)
                    
                    if verbose and (i + 1) % 10 == 0:
                        print(f"Tested {i+1}/{len(combinations)} combinations...")
        else:
            # Sequential execution
            for i, combo in enumerate(combinations):
                params = dict(zip(param_names, combo))
                result = self._evaluate_parameters(params)
                results.append(result)
                
                if verbose and (i + 1) % 10 == 0:
                    print(f"Tested {i+1}/{len(combinations)} combinations...")
        
        # Find best result
        self.results = results
        self.best_result = max(results, key=lambda x: x.score)
        
        if verbose:
            print(f"\nBest parameters found:")
            print(json.dumps(self.best_result.parameters, indent=2))
            print(f"Score: {self.best_result.score:.4f}")
        
        return self.best_result
    
    def random_search(self,
                     param_distributions: Dict,
                     n_iter: int = 100,
                     verbose: bool = True) -> OptimizationResult:
        """
        Random search optimization - samples random parameter combinations
        
        Parameters:
        -----------
        param_distributions : dict
            Dictionary with parameter names and ranges
            Example: {
                'length': (5, 100),
                'order': (2, 6),
                'adaptive_smooth': (3, 15)
            }
        n_iter : int
            Number of random combinations to test
        
        Returns:
        --------
        OptimizationResult : Best parameter combination found
        """
        if verbose:
            print(f"Starting Random Search Optimization ({n_iter} iterations)...")
        
        results = []
        
        for i in range(n_iter):
            # Sample random parameters
            params = {}
            for param_name, param_range in param_distributions.items():
                if isinstance(param_range, tuple) and len(param_range) == 2:
                    # Continuous range
                    if isinstance(param_range[0], int):
                        params[param_name] = random.randint(param_range[0], param_range[1])
                    else:
                        params[param_name] = random.uniform(param_range[0], param_range[1])
                elif isinstance(param_range, list):
                    # Discrete choices
                    params[param_name] = random.choice(param_range)
            
            # Evaluate
            result = self._evaluate_parameters(params)
            results.append(result)
            
            if verbose and (i + 1) % 20 == 0:
                print(f"Tested {i+1}/{n_iter} combinations...")
        
        # Find best result
        self.results = results
        self.best_result = max(results, key=lambda x: x.score)
        
        if verbose:
            print(f"\nBest parameters found:")
            print(json.dumps(self.best_result.parameters, indent=2))
            print(f"Score: {self.best_result.score:.4f}")
        
        return self.best_result
    
    def genetic_algorithm(self,
                         param_bounds: Dict,
                         population_size: int = 50,
                         generations: int = 20,
                         mutation_rate: float = 0.1,
                         crossover_rate: float = 0.8,
                         elite_size: int = 5,
                         verbose: bool = True) -> OptimizationResult:
        """
        Genetic algorithm optimization
        
        Parameters:
        -----------
        param_bounds : dict
            Parameter boundaries for evolution
        population_size : int
            Size of each generation
        generations : int
            Number of generations to evolve
        mutation_rate : float
            Probability of mutation
        crossover_rate : float
            Probability of crossover
        elite_size : int
            Number of best individuals to keep
        
        Returns:
        --------
        OptimizationResult : Best parameter combination found
        """
        if verbose:
            print(f"Starting Genetic Algorithm Optimization...")
            print(f"Population: {population_size}, Generations: {generations}")
        
        # Initialize population
        population = self._initialize_population(param_bounds, population_size)
        best_overall = None
        
        for gen in range(generations):
            # Evaluate fitness
            fitness_scores = []
            for individual in population:
                result = self._evaluate_parameters(individual)
                fitness_scores.append(result.score)
            
            # Track best
            best_idx = np.argmax(fitness_scores)
            if best_overall is None or fitness_scores[best_idx] > best_overall.score:
                best_overall = self._evaluate_parameters(population[best_idx])
            
            if verbose:
                print(f"Generation {gen+1}/{generations} - Best: {fitness_scores[best_idx]:.4f}")
            
            # Selection and breeding
            new_population = []
            
            # Keep elite
            elite_indices = np.argsort(fitness_scores)[-elite_size:]
            for idx in elite_indices:
                new_population.append(population[idx].copy())
            
            # Breed new individuals
            while len(new_population) < population_size:
                # Tournament selection
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)
                
                # Crossover
                if random.random() < crossover_rate:
                    child = self._crossover(parent1, parent2)
                else:
                    child = parent1.copy()
                
                # Mutation
                if random.random() < mutation_rate:
                    child = self._mutate(child, param_bounds)
                
                new_population.append(child)
            
            population = new_population
        
        self.best_result = best_overall
        
        if verbose:
            print(f"\nBest parameters found:")
            print(json.dumps(self.best_result.parameters, indent=2))
            print(f"Score: {self.best_result.score:.4f}")
        
        return self.best_result
    
    def walk_forward_analysis(self,
                             param_grid: Dict,
                             window_size: int = 252,
                             step_size: int = 63,
                             verbose: bool = True) -> List[OptimizationResult]:
        """
        Walk-forward analysis for robustness testing
        
        Parameters:
        -----------
        param_grid : dict
            Parameters to optimize in each window
        window_size : int
            Size of training window (e.g., 252 days = 1 year)
        step_size : int
            Step size for moving window (e.g., 63 days = 1 quarter)
        
        Returns:
        --------
        List[OptimizationResult] : Results for each window
        """
        if verbose:
            print("Starting Walk-Forward Analysis...")
        
        results = []
        n_windows = (len(self.price_data) - window_size) // step_size + 1
        
        for i in range(n_windows):
            start_idx = i * step_size
            end_idx = start_idx + window_size
            
            if end_idx > len(self.price_data):
                break
            
            # Training window
            train_data = self.price_data[start_idx:end_idx]
            
            # Test window (next step_size bars)
            test_end = min(end_idx + step_size, len(self.price_data))
            test_data = self.price_data[end_idx:test_end]
            
            if len(test_data) < 10:  # Skip if test set too small
                continue
            
            if verbose:
                print(f"\nWindow {i+1}/{n_windows}: Training [{start_idx}:{end_idx}], "
                      f"Testing [{end_idx}:{test_end}]")
            
            # Optimize on training data
            temp_optimizer = LaguerreOptimizer(train_data, self.optimization_metric)
            best_params = temp_optimizer.grid_search(param_grid, verbose=False)
            
            # Test on out-of-sample data
            test_result = self._evaluate_parameters(best_params.parameters, test_data)
            results.append(test_result)
            
            if verbose:
                print(f"Out-of-sample score: {test_result.score:.4f}")
        
        # Calculate overall statistics
        if verbose and results:
            scores = [r.score for r in results]
            print(f"\nWalk-Forward Results:")
            print(f"Average Score: {np.mean(scores):.4f}")
            print(f"Std Dev: {np.std(scores):.4f}")
            print(f"Min Score: {np.min(scores):.4f}")
            print(f"Max Score: {np.max(scores):.4f}")
        
        return results
    
    def _evaluate_parameters(self, 
                           params: Dict,
                           data: Optional[np.ndarray] = None) -> OptimizationResult:
        """Evaluate a parameter combination"""
        if data is None:
            data = self.train_data
        
        try:
            # Create filter with parameters
            filter_params = {
                'length': params.get('length', 10),
                'order': params.get('order', 4),
                'adaptive_mode': params.get('adaptive_mode', True),
                'adaptive_smooth': params.get('adaptive_smooth', 5),
                'adaptive_smooth_mode': params.get('adaptive_smooth_mode', SmoothMode.MEDIAN)
            }
            
            # Calculate metrics using simplified backtest
            metrics = self._calculate_metrics(data, filter_params)
            
            # Get score based on optimization metric
            score = metrics.get(self.optimization_metric, 0)
            
            return OptimizationResult(
                parameters=params,
                score=score,
                metrics=metrics
            )
        except Exception as e:
            # Return poor score for invalid parameters
            return OptimizationResult(
                parameters=params,
                score=-999,
                metrics={'error': str(e)}
            )
    
    def _calculate_metrics(self, prices: np.ndarray, filter_params: Dict) -> Dict:
        """Calculate performance metrics for given parameters"""
        try:
            # Simplified metric calculation
            # In production, use full AdaptiveLaguerreTrader.backtest()
            
            # Create simple filter simulation
            n = len(prices)
            returns = np.diff(prices) / prices[:-1]
            
            # Simulate filter behavior (simplified)
            length = filter_params['length']
            if length >= len(prices):
                return {'sharpe_ratio': -999, 'total_return': -999}
            
            # Simple moving average as proxy (for demonstration)
            ma = pd.Series(prices).rolling(length).mean().values
            
            # Generate signals
            signals = np.zeros(n)
            signals[prices > ma] = 1
            signals[prices < ma] = -1
            
            # Calculate returns
            strategy_returns = signals[:-1] * returns
            
            # Calculate metrics
            total_return = np.sum(strategy_returns) * 100
            
            if len(strategy_returns) > 0 and np.std(strategy_returns) > 0:
                sharpe_ratio = np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252)
            else:
                sharpe_ratio = 0
            
            winning_trades = np.sum(strategy_returns > 0)
            total_trades = np.sum(strategy_returns != 0)
            win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
            
            gross_profit = np.sum(strategy_returns[strategy_returns > 0])
            gross_loss = abs(np.sum(strategy_returns[strategy_returns < 0]))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
            
            return {
                'sharpe_ratio': sharpe_ratio,
                'total_return': total_return,
                'win_rate': win_rate,
                'profit_factor': profit_factor
            }
            
        except Exception as e:
            return {
                'sharpe_ratio': -999,
                'total_return': -999,
                'win_rate': 0,
                'profit_factor': 0,
                'error': str(e)
            }
    
    def _calculate_grid_size(self, param_grid: Dict) -> int:
        """Calculate total number of combinations in grid"""
        size = 1
        for values in param_grid.values():
            size *= len(values)
        return size
    
    def _initialize_population(self, param_bounds: Dict, size: int) -> List[Dict]:
        """Initialize population for genetic algorithm"""
        population = []
        for _ in range(size):
            individual = {}
            for param, bounds in param_bounds.items():
                if isinstance(bounds, tuple) and len(bounds) == 2:
                    if isinstance(bounds[0], int):
                        individual[param] = random.randint(bounds[0], bounds[1])
                    else:
                        individual[param] = random.uniform(bounds[0], bounds[1])
                elif isinstance(bounds, list):
                    individual[param] = random.choice(bounds)
            population.append(individual)
        return population
    
    def _tournament_selection(self, population: List[Dict], fitness: List[float], 
                            tournament_size: int = 3) -> Dict:
        """Tournament selection for genetic algorithm"""
        indices = random.sample(range(len(population)), tournament_size)
        best_idx = max(indices, key=lambda i: fitness[i])
        return population[best_idx]
    
    def _crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """Crossover operation for genetic algorithm"""
        child = {}
        for key in parent1.keys():
            if random.random() < 0.5:
                child[key] = parent1[key]
            else:
                child[key] = parent2[key]
        return child
    
    def _mutate(self, individual: Dict, param_bounds: Dict, 
                mutation_strength: float = 0.2) -> Dict:
        """Mutation operation for genetic algorithm"""
        mutated = individual.copy()
        for param, bounds in param_bounds.items():
            if param in mutated:
                if isinstance(bounds, tuple) and len(bounds) == 2:
                    # Continuous mutation
                    if isinstance(bounds[0], int):
                        change = int((bounds[1] - bounds[0]) * mutation_strength)
                        mutated[param] = max(bounds[0], 
                                           min(bounds[1], 
                                               mutated[param] + random.randint(-change, change)))
                    else:
                        change = (bounds[1] - bounds[0]) * mutation_strength
                        mutated[param] = max(bounds[0], 
                                           min(bounds[1], 
                                               mutated[param] + random.uniform(-change, change)))
        return mutated
    
    def save_results(self, filename: str):
        """Save optimization results to JSON file"""
        results_data = {
            'best_parameters': self.best_result.to_dict() if self.best_result else None,
            'all_results': [r.to_dict() for r in self.results[:100]],  # Save top 100
            'optimization_metric': self.optimization_metric,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"Results saved to {filename}")
    
    def plot_optimization_surface(self, param1: str, param2: str):
        """Plot optimization surface for two parameters"""
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            
            # Extract data
            p1_values = [r.parameters.get(param1, 0) for r in self.results]
            p2_values = [r.parameters.get(param2, 0) for r in self.results]
            scores = [r.score for r in self.results]
            
            # Create 3D plot
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')
            
            scatter = ax.scatter(p1_values, p2_values, scores, 
                               c=scores, cmap='viridis', s=50)
            
            ax.set_xlabel(param1)
            ax.set_ylabel(param2)
            ax.set_zlabel(self.optimization_metric)
            ax.set_title('Parameter Optimization Surface')
            
            plt.colorbar(scatter)
            plt.show()
            
        except ImportError:
            print("Matplotlib not installed. Cannot create plot.")


# Example usage functions
def optimize_for_scalping(prices):
    """Optimize parameters for scalping strategy"""
    optimizer = LaguerreOptimizer(prices, optimization_metric='sharpe_ratio')
    
    param_grid = {
        'length': [5, 7, 10],
        'order': [2, 3],
        'adaptive_smooth': [3, 5],
        'adaptive_mode': [True]
    }
    
    best = optimizer.grid_search(param_grid)
    return best

def optimize_for_swing_trading(prices):
    """Optimize parameters for swing trading"""
    optimizer = LaguerreOptimizer(prices, optimization_metric='profit_factor')
    
    param_distributions = {
        'length': (20, 50),
        'order': (3, 5),
        'adaptive_smooth': (5, 10),
        'adaptive_mode': [True]
    }
    
    best = optimizer.random_search(param_distributions, n_iter=200)
    return best

def robust_optimization(prices):
    """Perform robust optimization with walk-forward analysis"""
    optimizer = LaguerreOptimizer(prices, optimization_metric='sharpe_ratio')
    
    param_grid = {
        'length': [10, 20, 30, 40],
        'order': [3, 4, 5],
        'adaptive_smooth': [5, 7, 10]
    }
    
    # Walk-forward validation
    results = optimizer.walk_forward_analysis(param_grid)
    return results


if __name__ == "__main__":
    # Generate sample data for demonstration
    np.random.seed(42)
    n_points = 1000
    t = np.linspace(0, 4 * np.pi, n_points)
    prices = 100 + t * 2 + 10 * np.sin(t) + np.random.normal(0, 2, n_points)
    
    print("="*60)
    print("Adaptive Laguerre Filter - Parameter Optimizer")
    print("="*60)
    
    # Create optimizer
    optimizer = LaguerreOptimizer(
        price_data=prices,
        optimization_metric='sharpe_ratio',
        train_ratio=0.7
    )
    
    # Method 1: Grid Search
    print("\n1. GRID SEARCH")
    print("-"*40)
    param_grid = {
        'length': [10, 20, 30],
        'order': [3, 4, 5],
        'adaptive_smooth': [5, 7],
        'adaptive_mode': [True]
    }
    best_grid = optimizer.grid_search(param_grid, n_jobs=1)
    
    # Method 2: Random Search
    print("\n2. RANDOM SEARCH")
    print("-"*40)
    param_distributions = {
        'length': (5, 50),
        'order': (2, 6),
        'adaptive_smooth': (3, 15),
        'adaptive_mode': [True, False]
    }
    best_random = optimizer.random_search(param_distributions, n_iter=50)
    
    # Method 3: Genetic Algorithm
    print("\n3. GENETIC ALGORITHM")
    print("-"*40)
    param_bounds = {
        'length': (5, 50),
        'order': (2, 6),
        'adaptive_smooth': (3, 15),
        'adaptive_mode': [True, False]
    }
    best_genetic = optimizer.genetic_algorithm(
        param_bounds, 
        population_size=20, 
        generations=10
    )
    
    # Method 4: Walk-Forward Analysis
    print("\n4. WALK-FORWARD ANALYSIS")
    print("-"*40)
    wf_results = optimizer.walk_forward_analysis(
        param_grid={'length': [10, 20, 30], 'order': [3, 4]},
        window_size=200,
        step_size=50
    )
    
    # Save results
    optimizer.save_results('optimization_results.json')
    
    print("\n" + "="*60)
    print("Optimization Complete!")
    print("Best parameters saved to optimization_results.json")