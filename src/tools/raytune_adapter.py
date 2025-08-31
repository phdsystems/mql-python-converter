"""
Ray Tune integration adapter for the optimization framework
Provides distributed hyperparameter tuning with advanced schedulers
"""

from typing import Dict, List, Tuple, Optional, Callable, Any, Union
import numpy as np
from dataclasses import dataclass
import warnings
import tempfile
import os

try:
    import ray
    from ray import tune
    from ray.tune import CLIReporter
    from ray.tune.schedulers import ASHAScheduler, PopulationBasedTraining, HyperBandScheduler
    from ray.tune.suggest import ConcurrencyLimiter
    from ray.tune.suggest.hyperopt import HyperOptSearch
    from ray.tune.suggest.optuna import OptunaSearch
    from ray.tune.suggest.skopt import SkOptSearch
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False
    warnings.warn("Ray Tune not installed. Install with: pip install 'ray[tune]'")

# Import base optimization framework
try:
    from optimization_adapter import OptimizationAdapter, OptimizationResult
except ImportError:
    from .optimization_adapter import OptimizationAdapter, OptimizationResult


class RayTuneAdapter(OptimizationAdapter):
    """Adapter for Ray Tune distributed optimization framework"""
    
    def __init__(self, objective_function: Callable, metric_adapter: Any):
        """
        Initialize Ray Tune adapter
        
        Args:
            objective_function: Function that takes parameters and returns score
            metric_adapter: Metric adapter to use for scoring
        """
        super().__init__(objective_function, metric_adapter)
        if not RAY_AVAILABLE:
            raise ImportError("Ray Tune is not installed. Install with: pip install 'ray[tune]'")
        
        self.analysis = None
        self.config_space = None
        
    def optimize(self, param_space: Dict, num_samples: int = 100,
                search_alg: str = 'random', scheduler: str = 'asha',
                direction: str = 'maximize', max_concurrent_trials: int = 4,
                verbose: bool = False, seed: Optional[int] = None,
                resources_per_trial: Dict = None, local_mode: bool = False,
                **kwargs) -> OptimizationResult:
        """
        Perform Ray Tune optimization
        
        Args:
            param_space: Dict defining parameter search space
                - For continuous: {'param': tune.uniform(min, max)}
                - For discrete: {'param': tune.choice([val1, val2, ...])}
                - For integers: {'param': tune.randint(min, max)}
                - For log scale: {'param': tune.loguniform(min, max)}
            num_samples: Number of trials to run
            search_alg: Search algorithm ('random', 'hyperopt', 'optuna', 'skopt', 'grid')
            scheduler: Trial scheduler ('asha', 'hyperband', 'pbt', 'fifo')
            direction: Optimization direction ('maximize' or 'minimize')
            max_concurrent_trials: Maximum concurrent trials
            verbose: Whether to print progress
            seed: Random seed
            resources_per_trial: Resources per trial (e.g., {'cpu': 1, 'gpu': 0})
            local_mode: Run Ray in local mode (for debugging)
        """
        self.iteration_count = 0
        self.convergence_history = []
        self.direction = direction
        
        # Initialize Ray if not already initialized
        if not ray.is_initialized():
            ray.init(local_mode=local_mode)
        
        # Convert parameter space to Ray Tune format
        self.config_space = self._create_tune_space(param_space)
        
        # Create trainable function for Ray Tune
        def trainable(config):
            # Evaluate parameters
            score, metrics = self._evaluate(config)
            
            # Report to Ray Tune
            tune.report(
                score=score,
                **metrics
            )
        
        # Create search algorithm
        search_algorithm = self._create_search_algorithm(
            search_alg, seed, max_concurrent_trials
        )
        
        # Create scheduler
        trial_scheduler = self._create_scheduler(scheduler)
        
        # Set up progress reporter
        reporter = CLIReporter(
            metric_columns=["score", "training_iteration"]
        ) if verbose else None
        
        # Default resources if not specified
        if resources_per_trial is None:
            resources_per_trial = {"cpu": 1}
        
        # Run optimization
        self.analysis = tune.run(
            trainable,
            config=self.config_space,
            num_samples=num_samples,
            search_alg=search_algorithm,
            scheduler=trial_scheduler,
            metric="score",
            mode="max" if direction == "maximize" else "min",
            resources_per_trial=resources_per_trial,
            progress_reporter=reporter,
            verbose=verbose and verbose > 1,
            raise_on_failed_trial=False
        )
        
        # Get best result
        best_config = self.analysis.get_best_config(metric="score", mode="max" if direction == "maximize" else "min")
        best_trial = self.analysis.get_best_trial(metric="score", mode="max" if direction == "maximize" else "min")
        
        # Get metrics for best configuration
        best_score = best_trial.last_result["score"]
        best_metrics = {k: v for k, v in best_trial.last_result.items() 
                       if k not in ["score", "training_iteration", "trial_id", "done"]}
        
        # Get convergence history
        for trial in self.analysis.trials:
            if "score" in trial.last_result:
                self.convergence_history.append(trial.last_result["score"])
        
        return OptimizationResult(
            parameters=best_config,
            score=best_score,
            metrics=best_metrics,
            method=self.get_name(),
            iterations=len(self.analysis.trials),
            convergence_history=self.convergence_history
        )
    
    def _create_tune_space(self, param_space: Dict) -> Dict:
        """Convert parameter space to Ray Tune format"""
        tune_space = {}
        
        for param_name, param_def in param_space.items():
            if isinstance(param_def, dict):
                param_type = param_def.get('type', 'float')
                
                if param_type == 'float':
                    if param_def.get('log', False):
                        tune_space[param_name] = tune.loguniform(
                            param_def['low'],
                            param_def['high']
                        )
                    else:
                        tune_space[param_name] = tune.uniform(
                            param_def['low'],
                            param_def['high']
                        )
                elif param_type == 'int':
                    tune_space[param_name] = tune.randint(
                        param_def['low'],
                        param_def['high'] + 1  # Ray Tune uses exclusive upper bound
                    )
                elif param_type in ['categorical', 'choice']:
                    choices = param_def.get('choices', param_def.get('options', []))
                    tune_space[param_name] = tune.choice(choices)
                else:
                    raise ValueError(f"Unknown parameter type: {param_type}")
                    
            elif isinstance(param_def, tuple) and len(param_def) == 2:
                # Simple range format
                if isinstance(param_def[0], int) and isinstance(param_def[1], int):
                    tune_space[param_name] = tune.randint(param_def[0], param_def[1] + 1)
                else:
                    tune_space[param_name] = tune.uniform(float(param_def[0]), float(param_def[1]))
                    
            elif isinstance(param_def, list):
                # Categorical choices
                tune_space[param_name] = tune.choice(param_def)
            elif hasattr(tune, '__version__'):  # Check if it's already a Ray Tune object
                tune_space[param_name] = param_def
            else:
                raise ValueError(f"Invalid parameter definition for {param_name}")
        
        return tune_space
    
    def _create_search_algorithm(self, search_alg: str, seed: Optional[int], 
                                 max_concurrent: int):
        """Create search algorithm for Ray Tune"""
        if search_alg == 'random':
            from ray.tune.suggest.basic_variant import BasicVariantGenerator
            return BasicVariantGenerator(random_state=seed)
        elif search_alg == 'grid':
            from ray.tune.suggest.basic_variant import BasicVariantGenerator
            return BasicVariantGenerator()
        elif search_alg == 'hyperopt':
            try:
                from ray.tune.suggest.hyperopt import HyperOptSearch
                search = HyperOptSearch(random_state_seed=seed)
                return ConcurrencyLimiter(search, max_concurrent=max_concurrent)
            except ImportError:
                warnings.warn("Hyperopt not installed. Using random search.")
                return None
        elif search_alg == 'optuna':
            try:
                from ray.tune.suggest.optuna import OptunaSearch
                search = OptunaSearch(seed=seed)
                return ConcurrencyLimiter(search, max_concurrent=max_concurrent)
            except ImportError:
                warnings.warn("Optuna not installed. Using random search.")
                return None
        elif search_alg == 'skopt':
            try:
                from ray.tune.suggest.skopt import SkOptSearch
                search = SkOptSearch()
                return ConcurrencyLimiter(search, max_concurrent=max_concurrent)
            except ImportError:
                warnings.warn("Scikit-Optimize not installed. Using random search.")
                return None
        else:
            raise ValueError(f"Unknown search algorithm: {search_alg}")
    
    def _create_scheduler(self, scheduler: str):
        """Create trial scheduler for Ray Tune"""
        if scheduler == 'asha':
            return ASHAScheduler(
                metric="score",
                mode="max" if self.direction == "maximize" else "min",
                grace_period=1,
                reduction_factor=2
            )
        elif scheduler == 'hyperband':
            return HyperBandScheduler(
                metric="score",
                mode="max" if self.direction == "maximize" else "min"
            )
        elif scheduler == 'pbt':
            return PopulationBasedTraining(
                metric="score",
                mode="max" if self.direction == "maximize" else "min",
                perturbation_interval=4,
                hyperparam_mutations={
                    # Define mutations based on config space
                }
            )
        elif scheduler == 'fifo':
            return None  # FIFO is default
        else:
            raise ValueError(f"Unknown scheduler: {scheduler}")
    
    def get_name(self) -> str:
        return "ray_tune"
    
    def get_description(self) -> str:
        return "Distributed hyperparameter tuning with Ray Tune"
    
    def get_all_trials(self) -> List[Dict]:
        """Get data from all trials"""
        if not self.analysis:
            return []
        
        trials_data = []
        for trial in self.analysis.trials:
            trials_data.append({
                'config': trial.config,
                'score': trial.last_result.get('score'),
                'metrics': trial.last_result,
                'trial_id': trial.trial_id
            })
        
        return trials_data
    
    def plot_parallel_coordinates(self):
        """Plot parallel coordinates of trials"""
        if not self.analysis:
            warnings.warn("No analysis available")
            return
        
        try:
            from ray.tune.analysis import ExperimentAnalysis
            import matplotlib.pyplot as plt
            
            # This would require additional implementation
            warnings.warn("Parallel coordinates plot not yet implemented for Ray Tune")
        except ImportError:
            warnings.warn("Visualization dependencies not installed")
    
    def shutdown(self):
        """Shutdown Ray"""
        if ray.is_initialized():
            ray.shutdown()


class DistributedRayTuneAdapter(RayTuneAdapter):
    """Distributed version of Ray Tune for cluster deployment"""
    
    def optimize(self, param_space: Dict, num_samples: int = 100,
                ray_address: str = "auto", **kwargs) -> OptimizationResult:
        """
        Perform distributed Ray Tune optimization on a cluster
        
        Args:
            param_space: Parameter search space
            num_samples: Number of trials
            ray_address: Ray cluster address (or "auto" to detect)
            **kwargs: Additional arguments passed to parent
        """
        # Connect to Ray cluster
        if not ray.is_initialized():
            ray.init(address=ray_address)
            print(f"Connected to Ray cluster with {ray.cluster_resources()}")
        
        # Run optimization on cluster
        return super().optimize(param_space, num_samples, **kwargs)


# Register Ray Tune adapters with the factory
def register_raytune_adapters():
    """Register Ray Tune adapters with the optimization factory"""
    try:
        try:
            from optimization_adapter import OptimizationFactory
        except ImportError:
            from .optimization_adapter import OptimizationFactory
        
        if RAY_AVAILABLE:
            OptimizationFactory.register('ray_tune', RayTuneAdapter)
            OptimizationFactory.register('raytune', RayTuneAdapter)  # Alias
            OptimizationFactory.register('ray_tune_distributed', DistributedRayTuneAdapter)
            return True
        else:
            warnings.warn("Ray Tune not available. Install with: pip install 'ray[tune]'")
            return False
    except (ImportError, AttributeError) as e:
        warnings.warn(f"Could not register Ray Tune adapters with factory: {e}")
        return False