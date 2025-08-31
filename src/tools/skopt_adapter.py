"""
Scikit-Optimize integration adapter for the optimization framework
Provides Gaussian Process-based Bayesian optimization
"""

from typing import Dict, List, Tuple, Optional, Callable, Any, Union
import numpy as np
from dataclasses import dataclass
import warnings

try:
    from skopt import gp_minimize, forest_minimize, gbrt_minimize, dummy_minimize
    from skopt.space import Real, Integer, Categorical
    from skopt.utils import use_named_args
    from skopt import dump, load
    SKOPT_AVAILABLE = True
except ImportError:
    SKOPT_AVAILABLE = False
    warnings.warn("Scikit-Optimize not installed. Install with: pip install scikit-optimize")

# Import base optimization framework
try:
    from optimization_adapter import OptimizationAdapter, OptimizationResult
except ImportError:
    from .optimization_adapter import OptimizationAdapter, OptimizationResult


class SkoptAdapter(OptimizationAdapter):
    """Adapter for Scikit-Optimize framework"""
    
    def __init__(self, objective_function: Callable, metric_adapter: Any):
        """
        Initialize Scikit-Optimize adapter
        
        Args:
            objective_function: Function that takes parameters and returns score
            metric_adapter: Metric adapter to use for scoring
        """
        super().__init__(objective_function, metric_adapter)
        if not SKOPT_AVAILABLE:
            raise ImportError("Scikit-Optimize is not installed. Install with: pip install scikit-optimize")
        
        self.result = None
        self.dimensions = None
        self.param_names = None
        
    def optimize(self, param_space: Dict, n_calls: int = 100,
                base_estimator: str = 'gp', n_initial_points: int = 10,
                acq_func: str = 'EI', direction: str = 'maximize',
                verbose: bool = False, seed: Optional[int] = None,
                n_jobs: int = 1, **kwargs) -> OptimizationResult:
        """
        Perform Scikit-Optimize optimization
        
        Args:
            param_space: Dict defining parameter search space
                - For continuous: {'param': (min, max)} or {'param': {'type': 'float', 'low': min, 'high': max}}
                - For discrete: {'param': [val1, val2, ...]} or {'param': {'type': 'categorical', 'choices': [...]}}
                - For integers: {'param': {'type': 'int', 'low': min, 'high': max}}
                - For log scale: {'param': {'type': 'float', 'low': min, 'high': max, 'log': True}}
            n_calls: Number of function evaluations
            base_estimator: Surrogate model ('gp', 'rf', 'et', 'gbrt')
            n_initial_points: Number of random initial points
            acq_func: Acquisition function ('EI', 'LCB', 'PI', 'gp_hedge')
            direction: Optimization direction ('maximize' or 'minimize')
            verbose: Whether to print progress
            seed: Random seed
            n_jobs: Number of parallel jobs for model fitting
        """
        self.iteration_count = 0
        self.convergence_history = []
        self.direction = direction
        
        # Convert parameter space to skopt format
        self.dimensions, self.param_names = self._create_skopt_space(param_space)
        
        # Create objective wrapper with named arguments
        @use_named_args(self.dimensions)
        def skopt_objective(**params):
            # Evaluate parameters
            score, metrics = self._evaluate(params)
            self.convergence_history.append(score)
            
            # Skopt minimizes, so negate if maximizing
            return -score if direction == 'maximize' else score
        
        # Select optimization function based on base_estimator
        optimize_func = self._get_optimizer(base_estimator)
        
        # Run optimization
        self.result = optimize_func(
            func=skopt_objective,
            dimensions=self.dimensions,
            n_calls=n_calls,
            n_initial_points=n_initial_points,
            acq_func=acq_func,
            verbose=verbose,
            random_state=seed,
            n_jobs=n_jobs
        )
        
        # Extract best parameters
        best_params = dict(zip(self.param_names, self.result.x))
        best_score = -self.result.fun if direction == 'maximize' else self.result.fun
        
        # Calculate metrics for best parameters
        _, best_metrics = self._evaluate(best_params)
        
        return OptimizationResult(
            parameters=best_params,
            score=best_score,
            metrics=best_metrics,
            method=self.get_name(),
            iterations=len(self.result.func_vals),
            convergence_history=self.convergence_history
        )
    
    def _create_skopt_space(self, param_space: Dict) -> Tuple[List, List[str]]:
        """Convert parameter space to Scikit-Optimize format"""
        dimensions = []
        param_names = []
        
        for param_name, param_def in param_space.items():
            param_names.append(param_name)
            
            if isinstance(param_def, dict):
                param_type = param_def.get('type', 'float')
                
                if param_type == 'float':
                    prior = 'log-uniform' if param_def.get('log', False) else 'uniform'
                    dimensions.append(Real(
                        param_def['low'],
                        param_def['high'],
                        prior=prior,
                        name=param_name
                    ))
                elif param_type == 'int':
                    dimensions.append(Integer(
                        param_def['low'],
                        param_def['high'],
                        name=param_name
                    ))
                elif param_type in ['categorical', 'choice']:
                    choices = param_def.get('choices', param_def.get('options', []))
                    dimensions.append(Categorical(
                        choices,
                        name=param_name
                    ))
                else:
                    raise ValueError(f"Unknown parameter type: {param_type}")
                    
            elif isinstance(param_def, tuple) and len(param_def) == 2:
                # Simple range format
                if isinstance(param_def[0], int) and isinstance(param_def[1], int):
                    dimensions.append(Integer(param_def[0], param_def[1], name=param_name))
                else:
                    dimensions.append(Real(float(param_def[0]), float(param_def[1]), name=param_name))
                    
            elif isinstance(param_def, list):
                # Categorical choices
                dimensions.append(Categorical(param_def, name=param_name))
            else:
                raise ValueError(f"Invalid parameter definition for {param_name}")
        
        return dimensions, param_names
    
    def _get_optimizer(self, base_estimator: str):
        """Get optimization function based on base estimator"""
        optimizers = {
            'gp': gp_minimize,           # Gaussian Process
            'rf': forest_minimize,        # Random Forest
            'et': forest_minimize,        # Extra Trees (same function as RF)
            'gbrt': gbrt_minimize,        # Gradient Boosted Trees
            'dummy': dummy_minimize       # Random search baseline
        }
        
        if base_estimator not in optimizers:
            raise ValueError(f"Unknown base_estimator: {base_estimator}. Choose from: {list(optimizers.keys())}")
        
        return optimizers[base_estimator]
    
    def get_name(self) -> str:
        return "scikit_optimize"
    
    def get_description(self) -> str:
        return "Gaussian Process-based Bayesian optimization"
    
    def save_result(self, filepath: str):
        """Save optimization result to file"""
        if self.result:
            dump(self.result, filepath)
    
    def load_result(self, filepath: str):
        """Load optimization result from file"""
        self.result = load(filepath)
    
    def plot_convergence(self):
        """Plot convergence of the optimization"""
        if not self.result:
            warnings.warn("No optimization result available")
            return
        
        try:
            from skopt.plots import plot_convergence
            import matplotlib.pyplot as plt
            
            plot_convergence(self.result)
            plt.show()
        except ImportError:
            warnings.warn("Matplotlib not installed. Cannot create visualization.")
    
    def plot_objective(self):
        """Plot the objective function (for 1D or 2D problems)"""
        if not self.result:
            warnings.warn("No optimization result available")
            return
        
        try:
            from skopt.plots import plot_objective
            import matplotlib.pyplot as plt
            
            plot_objective(self.result, dimensions=self.param_names)
            plt.show()
        except ImportError:
            warnings.warn("Matplotlib not installed. Cannot create visualization.")
    
    def plot_evaluations(self):
        """Plot evaluated points"""
        if not self.result:
            warnings.warn("No optimization result available")
            return
        
        try:
            from skopt.plots import plot_evaluations
            import matplotlib.pyplot as plt
            
            plot_evaluations(self.result, dimensions=self.param_names)
            plt.show()
        except ImportError:
            warnings.warn("Matplotlib not installed. Cannot create visualization.")
    
    def get_expected_minimum(self) -> Tuple[Dict, float]:
        """Get the expected minimum location according to the surrogate model"""
        if not self.result:
            return None, None
        
        # Get expected minimum from the surrogate model
        if hasattr(self.result, 'space') and hasattr(self.result.space, 'transform'):
            x_min = self.result.space.transform(self.result.space.rvs(n_samples=10000))
            y_min = self.result.models[-1].predict(x_min)
            idx_min = np.argmin(y_min)
            
            params = dict(zip(self.param_names, self.result.space.inverse_transform(x_min[idx_min:idx_min+1])[0]))
            expected_score = -y_min[idx_min] if self.direction == 'maximize' else y_min[idx_min]
            
            return params, expected_score
        
        return None, None


class ParallelSkoptAdapter(SkoptAdapter):
    """Parallel version of Scikit-Optimize using joblib"""
    
    def optimize(self, param_space: Dict, n_calls: int = 100,
                n_points: int = 1, **kwargs) -> OptimizationResult:
        """
        Perform parallel Scikit-Optimize optimization
        
        Args:
            param_space: Parameter search space
            n_calls: Total number of function evaluations
            n_points: Number of points to evaluate in parallel per iteration
            **kwargs: Additional arguments passed to parent
        """
        # Scikit-optimize has built-in parallelism through n_points parameter
        kwargs['n_points'] = n_points
        return super().optimize(param_space, n_calls, **kwargs)


# Register Scikit-Optimize adapters with the factory
def register_skopt_adapters():
    """Register Scikit-Optimize adapters with the optimization factory"""
    try:
        try:
            from optimization_adapter import OptimizationFactory
        except ImportError:
            from .optimization_adapter import OptimizationFactory
        
        if SKOPT_AVAILABLE:
            OptimizationFactory.register('scikit_optimize', SkoptAdapter)
            OptimizationFactory.register('skopt', SkoptAdapter)  # Alias
            OptimizationFactory.register('skopt_parallel', ParallelSkoptAdapter)
            return True
        else:
            warnings.warn("Scikit-Optimize not available. Install with: pip install scikit-optimize")
            return False
    except (ImportError, AttributeError) as e:
        warnings.warn(f"Could not register Scikit-Optimize adapters with factory: {e}")
        return False