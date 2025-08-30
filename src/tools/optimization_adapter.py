"""
Adapter pattern implementation for parameter optimization methods
Provides a unified interface for various optimization strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Callable, Any
import numpy as np
import random
from dataclasses import dataclass
from itertools import product
import json


@dataclass
class OptimizationResult:
    """Result from an optimization run"""
    parameters: Dict[str, Any]
    score: float
    metrics: Dict[str, float]
    method: str
    iterations: int
    convergence_history: Optional[List[float]] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'parameters': self.parameters,
            'score': self.score,
            'metrics': self.metrics,
            'method': self.method,
            'iterations': self.iterations,
            'convergence_history': self.convergence_history
        }


class OptimizationAdapter(ABC):
    """Abstract base class for optimization method adapters"""
    
    def __init__(self, objective_function: Callable, metric_adapter: Any):
        """
        Initialize optimization adapter
        
        Args:
            objective_function: Function that takes parameters and returns score
            metric_adapter: Metric adapter to use for scoring
        """
        self.objective_function = objective_function
        self.metric_adapter = metric_adapter
        self.iteration_count = 0
        self.best_result = None
        self.convergence_history = []
    
    @abstractmethod
    def optimize(self, param_space: Dict, **kwargs) -> OptimizationResult:
        """Run optimization and return best result"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get optimization method name"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get method description"""
        pass
    
    def _evaluate(self, parameters: Dict) -> Tuple[float, Dict]:
        """Evaluate parameters and return score and metrics"""
        self.iteration_count += 1
        metrics = self.objective_function(parameters)
        
        # If metrics is a dict, extract score using metric adapter
        if isinstance(metrics, dict):
            score = metrics.get(self.metric_adapter.get_name(), 0.0)
        else:
            score = metrics
            metrics = {self.metric_adapter.get_name(): score}
        
        return score, metrics


class GridSearchAdapter(OptimizationAdapter):
    """Adapter for Grid Search optimization"""
    
    def optimize(self, param_space: Dict, verbose: bool = False) -> OptimizationResult:
        """
        Perform exhaustive grid search
        
        Args:
            param_space: Dict of parameter_name -> list of values
            verbose: Whether to print progress
        """
        self.iteration_count = 0
        self.convergence_history = []
        
        # Generate all parameter combinations
        param_names = list(param_space.keys())
        param_values = list(param_space.values())
        combinations = list(product(*param_values))
        
        total_combinations = len(combinations)
        if verbose:
            print(f"Grid Search: Testing {total_combinations} combinations...")
        
        best_score = float('-inf')
        best_params = None
        best_metrics = None
        
        for i, combo in enumerate(combinations):
            params = dict(zip(param_names, combo))
            score, metrics = self._evaluate(params)
            
            self.convergence_history.append(score)
            
            if score > best_score:
                best_score = score
                best_params = params
                best_metrics = metrics
                
                if verbose:
                    print(f"  [{i+1}/{total_combinations}] New best: {score:.4f}")
            elif verbose and (i + 1) % 10 == 0:
                print(f"  [{i+1}/{total_combinations}] Current best: {best_score:.4f}")
        
        return OptimizationResult(
            parameters=best_params,
            score=best_score,
            metrics=best_metrics,
            method=self.get_name(),
            iterations=self.iteration_count,
            convergence_history=self.convergence_history
        )
    
    def get_name(self) -> str:
        return "grid_search"
    
    def get_description(self) -> str:
        return "Exhaustive search through all parameter combinations"


class RandomSearchAdapter(OptimizationAdapter):
    """Adapter for Random Search optimization"""
    
    def optimize(self, param_space: Dict, n_iter: int = 100, 
                verbose: bool = False, seed: Optional[int] = None) -> OptimizationResult:
        """
        Perform random search optimization
        
        Args:
            param_space: Dict of parameter_name -> (min, max) for continuous
                        or parameter_name -> list for discrete
            n_iter: Number of random samples
            verbose: Whether to print progress
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        self.iteration_count = 0
        self.convergence_history = []
        
        if verbose:
            print(f"Random Search: Testing {n_iter} random combinations...")
        
        best_score = float('-inf')
        best_params = None
        best_metrics = None
        
        for i in range(n_iter):
            # Sample random parameters
            params = {}
            for param_name, param_range in param_space.items():
                if isinstance(param_range, tuple) and len(param_range) == 2:
                    # Continuous parameter
                    if isinstance(param_range[0], int):
                        params[param_name] = random.randint(param_range[0], param_range[1])
                    else:
                        params[param_name] = random.uniform(param_range[0], param_range[1])
                elif isinstance(param_range, list):
                    # Discrete parameter
                    params[param_name] = random.choice(param_range)
                else:
                    raise ValueError(f"Invalid parameter range for {param_name}")
            
            score, metrics = self._evaluate(params)
            self.convergence_history.append(score)
            
            if score > best_score:
                best_score = score
                best_params = params
                best_metrics = metrics
                
                if verbose:
                    print(f"  [{i+1}/{n_iter}] New best: {score:.4f}")
            elif verbose and (i + 1) % 20 == 0:
                print(f"  [{i+1}/{n_iter}] Current best: {best_score:.4f}")
        
        return OptimizationResult(
            parameters=best_params,
            score=best_score,
            metrics=best_metrics,
            method=self.get_name(),
            iterations=self.iteration_count,
            convergence_history=self.convergence_history
        )
    
    def get_name(self) -> str:
        return "random_search"
    
    def get_description(self) -> str:
        return "Random sampling of parameter space"


class GeneticAlgorithmAdapter(OptimizationAdapter):
    """Adapter for Genetic Algorithm optimization"""
    
    def optimize(self, param_space: Dict, population_size: int = 50,
                generations: int = 20, mutation_rate: float = 0.1,
                crossover_rate: float = 0.8, elite_size: int = 5,
                verbose: bool = False, seed: Optional[int] = None) -> OptimizationResult:
        """
        Perform genetic algorithm optimization
        
        Args:
            param_space: Dict of parameter_name -> (min, max)
            population_size: Size of each generation
            generations: Number of generations
            mutation_rate: Probability of mutation
            crossover_rate: Probability of crossover
            elite_size: Number of best individuals to keep
            verbose: Whether to print progress
            seed: Random seed
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        self.iteration_count = 0
        self.convergence_history = []
        
        if verbose:
            print(f"Genetic Algorithm: {generations} generations, population {population_size}")
        
        # Initialize population
        population = self._initialize_population(param_space, population_size)
        
        best_overall_score = float('-inf')
        best_overall_params = None
        best_overall_metrics = None
        
        for gen in range(generations):
            # Evaluate fitness
            fitness_scores = []
            all_metrics = []
            
            for individual in population:
                score, metrics = self._evaluate(individual)
                fitness_scores.append(score)
                all_metrics.append(metrics)
            
            # Track best in generation
            best_idx = np.argmax(fitness_scores)
            gen_best_score = fitness_scores[best_idx]
            
            self.convergence_history.append(gen_best_score)
            
            if gen_best_score > best_overall_score:
                best_overall_score = gen_best_score
                best_overall_params = population[best_idx].copy()
                best_overall_metrics = all_metrics[best_idx]
                
                if verbose:
                    print(f"  Generation {gen+1}: New best: {gen_best_score:.4f}")
            elif verbose:
                print(f"  Generation {gen+1}: Best: {gen_best_score:.4f}")
            
            # Select parents
            parents = self._selection(population, fitness_scores, elite_size)
            
            # Create next generation
            next_population = parents[:elite_size]  # Keep elite
            
            while len(next_population) < population_size:
                if random.random() < crossover_rate:
                    parent1 = random.choice(parents)
                    parent2 = random.choice(parents)
                    child = self._crossover(parent1, parent2)
                else:
                    child = random.choice(parents).copy()
                
                if random.random() < mutation_rate:
                    child = self._mutate(child, param_space)
                
                next_population.append(child)
            
            population = next_population[:population_size]
        
        return OptimizationResult(
            parameters=best_overall_params,
            score=best_overall_score,
            metrics=best_overall_metrics,
            method=self.get_name(),
            iterations=self.iteration_count,
            convergence_history=self.convergence_history
        )
    
    def _initialize_population(self, param_space: Dict, size: int) -> List[Dict]:
        """Initialize random population"""
        population = []
        for _ in range(size):
            individual = {}
            for param_name, (min_val, max_val) in param_space.items():
                if isinstance(min_val, int):
                    individual[param_name] = random.randint(min_val, max_val)
                else:
                    individual[param_name] = random.uniform(min_val, max_val)
            population.append(individual)
        return population
    
    def _selection(self, population: List[Dict], fitness: List[float], 
                  elite_size: int) -> List[Dict]:
        """Select parents using tournament selection"""
        # Sort by fitness
        sorted_pop = [p for _, p in sorted(zip(fitness, population), 
                                          key=lambda x: x[0], reverse=True)]
        
        # Keep elite
        parents = sorted_pop[:elite_size]
        
        # Tournament selection for rest
        tournament_size = 3
        while len(parents) < len(population):
            tournament = random.sample(list(zip(fitness, population)), 
                                      min(tournament_size, len(population)))
            winner = max(tournament, key=lambda x: x[0])[1]
            parents.append(winner.copy())
        
        return parents
    
    def _crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """Uniform crossover"""
        child = {}
        for param in parent1:
            if random.random() < 0.5:
                child[param] = parent1[param]
            else:
                child[param] = parent2[param]
        return child
    
    def _mutate(self, individual: Dict, param_space: Dict) -> Dict:
        """Gaussian mutation"""
        mutated = individual.copy()
        for param_name, (min_val, max_val) in param_space.items():
            if random.random() < 0.3:  # 30% chance to mutate each gene
                if isinstance(min_val, int):
                    # Integer mutation
                    range_size = max_val - min_val
                    mutation = random.randint(-range_size // 10, range_size // 10)
                    mutated[param_name] = max(min_val, 
                                            min(max_val, individual[param_name] + mutation))
                else:
                    # Float mutation
                    range_size = max_val - min_val
                    mutation = random.gauss(0, range_size * 0.1)
                    mutated[param_name] = max(min_val, 
                                            min(max_val, individual[param_name] + mutation))
        return mutated
    
    def get_name(self) -> str:
        return "genetic_algorithm"
    
    def get_description(self) -> str:
        return "Evolutionary optimization using selection, crossover, and mutation"


class BayesianOptimizationAdapter(OptimizationAdapter):
    """Simplified Bayesian Optimization adapter"""
    
    def optimize(self, param_space: Dict, n_iter: int = 50,
                n_initial: int = 10, verbose: bool = False,
                seed: Optional[int] = None) -> OptimizationResult:
        """
        Perform simplified Bayesian optimization
        Uses expected improvement acquisition function
        
        Args:
            param_space: Dict of parameter_name -> (min, max)
            n_iter: Total number of iterations
            n_initial: Number of random initial points
            verbose: Whether to print progress
            seed: Random seed
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        self.iteration_count = 0
        self.convergence_history = []
        
        if verbose:
            print(f"Bayesian Optimization: {n_iter} iterations")
        
        # Store observations
        observations = []
        
        # Initial random sampling
        for i in range(n_initial):
            params = self._sample_random(param_space)
            score, metrics = self._evaluate(params)
            observations.append((params, score, metrics))
            self.convergence_history.append(score)
            
            if verbose:
                print(f"  Initial [{i+1}/{n_initial}]: {score:.4f}")
        
        # Bayesian optimization iterations
        for i in range(n_initial, n_iter):
            # Find next point to evaluate (simplified acquisition)
            next_params = self._acquisition_function(observations, param_space)
            score, metrics = self._evaluate(next_params)
            observations.append((next_params, score, metrics))
            self.convergence_history.append(score)
            
            if verbose and (i + 1) % 10 == 0:
                best_score = max(obs[1] for obs in observations)
                print(f"  [{i+1}/{n_iter}] Best so far: {best_score:.4f}")
        
        # Find best result
        best_obs = max(observations, key=lambda x: x[1])
        
        return OptimizationResult(
            parameters=best_obs[0],
            score=best_obs[1],
            metrics=best_obs[2],
            method=self.get_name(),
            iterations=self.iteration_count,
            convergence_history=self.convergence_history
        )
    
    def _sample_random(self, param_space: Dict) -> Dict:
        """Sample random point from parameter space"""
        params = {}
        for param_name, (min_val, max_val) in param_space.items():
            if isinstance(min_val, int):
                params[param_name] = random.randint(min_val, max_val)
            else:
                params[param_name] = random.uniform(min_val, max_val)
        return params
    
    def _acquisition_function(self, observations: List, param_space: Dict) -> Dict:
        """
        Simplified acquisition function
        Uses Upper Confidence Bound (UCB) strategy
        """
        # Get best observed score
        best_score = max(obs[1] for obs in observations)
        
        # Generate candidate points
        n_candidates = 100
        candidates = []
        
        for _ in range(n_candidates):
            candidate = self._sample_random(param_space)
            
            # Calculate distance to observed points (simplified)
            min_distance = float('inf')
            for obs_params, obs_score, _ in observations:
                distance = self._parameter_distance(candidate, obs_params, param_space)
                min_distance = min(min_distance, distance)
            
            # UCB: balance exploration (distance) and exploitation (proximity to best)
            exploration_weight = 2.0
            score_estimate = best_score + exploration_weight * min_distance
            
            candidates.append((candidate, score_estimate))
        
        # Select best candidate
        best_candidate = max(candidates, key=lambda x: x[1])
        return best_candidate[0]
    
    def _parameter_distance(self, params1: Dict, params2: Dict, param_space: Dict) -> float:
        """Calculate normalized distance between parameter sets"""
        distance = 0.0
        for param_name in params1:
            min_val, max_val = param_space[param_name]
            range_size = max_val - min_val
            if range_size > 0:
                normalized_diff = (params1[param_name] - params2[param_name]) / range_size
                distance += normalized_diff ** 2
        return np.sqrt(distance)
    
    def get_name(self) -> str:
        return "bayesian_optimization"
    
    def get_description(self) -> str:
        return "Probabilistic model-based optimization"


class OptimizationFactory:
    """Factory class for creating optimization adapters"""
    
    _methods = {
        'grid_search': GridSearchAdapter,
        'random_search': RandomSearchAdapter,
        'genetic_algorithm': GeneticAlgorithmAdapter,
        'bayesian_optimization': BayesianOptimizationAdapter
    }
    
    @classmethod
    def create(cls, method_name: str, objective_function: Callable, 
              metric_adapter: Any) -> OptimizationAdapter:
        """Create an optimization adapter by name"""
        if method_name not in cls._methods:
            raise ValueError(f"Unknown method: {method_name}. Available: {list(cls._methods.keys())}")
        
        method_class = cls._methods[method_name]
        return method_class(objective_function, metric_adapter)
    
    @classmethod
    def list_available(cls) -> List[str]:
        """List all available optimization methods"""
        return list(cls._methods.keys())
    
    @classmethod
    def register(cls, name: str, method_class: type):
        """Register a new optimization method"""
        if not issubclass(method_class, OptimizationAdapter):
            raise TypeError("Method class must inherit from OptimizationAdapter")
        cls._methods[name] = method_class


class HybridOptimizer(OptimizationAdapter):
    """Hybrid optimizer that combines multiple methods"""
    
    def __init__(self, objective_function: Callable, metric_adapter: Any,
                methods: List[str] = None):
        """
        Initialize hybrid optimizer
        
        Args:
            objective_function: Objective to optimize
            metric_adapter: Metric for scoring
            methods: List of method names to use in sequence
        """
        super().__init__(objective_function, metric_adapter)
        self.methods = methods or ['random_search', 'genetic_algorithm']
    
    def optimize(self, param_space: Dict, verbose: bool = False, **kwargs) -> OptimizationResult:
        """
        Run multiple optimization methods in sequence
        Use best result from each as starting point for next
        """
        if verbose:
            print(f"Hybrid Optimization: {' -> '.join(self.methods)}")
        
        best_result = None
        all_results = []
        
        for i, method_name in enumerate(self.methods):
            if verbose:
                print(f"\nPhase {i+1}: {method_name}")
            
            # Create adapter for this method
            adapter = OptimizationFactory.create(
                method_name, self.objective_function, self.metric_adapter
            )
            
            # If we have a previous best, use it to refine search space
            if best_result is not None:
                param_space = self._refine_search_space(
                    param_space, best_result.parameters
                )
            
            # Run optimization
            result = adapter.optimize(param_space, verbose=verbose, **kwargs)
            all_results.append(result)
            
            # Update best
            if best_result is None or result.score > best_result.score:
                best_result = result
        
        # Combine convergence histories
        combined_history = []
        for result in all_results:
            if result.convergence_history:
                combined_history.extend(result.convergence_history)
        
        best_result.method = f"hybrid_{'+'.join(self.methods)}"
        best_result.convergence_history = combined_history
        
        return best_result
    
    def _refine_search_space(self, param_space: Dict, best_params: Dict) -> Dict:
        """Refine search space around best parameters"""
        refined = {}
        
        for param_name, param_range in param_space.items():
            if isinstance(param_range, tuple) and len(param_range) == 2:
                # Continuous parameter - narrow range around best
                best_val = best_params[param_name]
                range_size = param_range[1] - param_range[0]
                margin = range_size * 0.3  # Search within 30% of original range
                
                new_min = max(param_range[0], best_val - margin)
                new_max = min(param_range[1], best_val + margin)
                
                if isinstance(param_range[0], int):
                    refined[param_name] = (int(new_min), int(new_max))
                else:
                    refined[param_name] = (new_min, new_max)
            else:
                # Discrete parameter - keep as is
                refined[param_name] = param_range
        
        return refined
    
    def get_name(self) -> str:
        return f"hybrid_{'+'.join(self.methods)}"
    
    def get_description(self) -> str:
        return f"Sequential optimization using: {', '.join(self.methods)}"