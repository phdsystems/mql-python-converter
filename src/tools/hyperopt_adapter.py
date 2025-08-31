"""
Hyperopt integration adapter for the optimization framework
Provides Tree-structured Parzen Estimator (TPE) optimization
"""

from typing import Dict, List, Tuple, Optional, Callable, Any, Union
import numpy as np
from dataclasses import dataclass
import warnings

try:
    import hyperopt
    from hyperopt import hp, fmin, tpe, Trials, STATUS_OK, STATUS_FAIL
    from hyperopt.pyll import scope
    HYPEROPT_AVAILABLE = True
except ImportError:
    HYPEROPT_AVAILABLE = False
    warnings.warn("Hyperopt not installed. Install with: pip install hyperopt")

# Import base optimization framework
try:
    from optimization_adapter import OptimizationAdapter, OptimizationResult
except ImportError:
    from .optimization_adapter import OptimizationAdapter, OptimizationResult


class HyperoptAdapter(OptimizationAdapter):
    """Adapter for Hyperopt optimization framework"""
    
    def __init__(self, objective_function: Callable, metric_adapter: Any):
        """
        Initialize Hyperopt adapter
        
        Args:
            objective_function: Function that takes parameters and returns score
            metric_adapter: Metric adapter to use for scoring
        """
        super().__init__(objective_function, metric_adapter)
        if not HYPEROPT_AVAILABLE:
            raise ImportError("Hyperopt is not installed. Install with: pip install hyperopt")
        
        self.trials = None
        self.space = None
        
    def optimize(self, param_space: Dict, n_trials: int = 100,
                algorithm: str = 'tpe', direction: str = 'maximize',
                verbose: bool = False, seed: Optional[int] = None,
                parallelism: int = 1, **kwargs) -> OptimizationResult:
        """
        Perform Hyperopt optimization
        
        Args:
            param_space: Dict defining parameter search space
                - For continuous: {'param': (min, max)} or {'param': {'type': 'float', 'low': min, 'high': max}}
                - For discrete: {'param': [val1, val2, ...]} or {'param': {'type': 'choice', 'options': [...]}}
                - For integers: {'param': {'type': 'int', 'low': min, 'high': max}}
                - For log scale: {'param': {'type': 'float', 'low': min, 'high': max, 'log': True}}
            n_trials: Number of trials to run
            algorithm: Algorithm to use ('tpe', 'random', 'anneal')
            direction: Optimization direction ('maximize' or 'minimize')
            verbose: Whether to print progress
            seed: Random seed for reproducibility
            parallelism: Number of parallel evaluations (requires MongoDB for > 1)
        """
        self.iteration_count = 0
        self.convergence_history = []
        self.direction = direction
        
        # Convert parameter space to Hyperopt format
        self.space = self._create_hyperopt_space(param_space)
        
        # Create trials object to track history
        self.trials = Trials()
        
        # Select algorithm
        algo = self._get_algorithm(algorithm)
        
        # Define objective wrapper for Hyperopt
        def hyperopt_objective(params):
            # Evaluate parameters
            score, metrics = self._evaluate(params)
            self.convergence_history.append(score)
            
            # Hyperopt minimizes, so negate if maximizing
            loss = -score if direction == 'maximize' else score
            
            # Return in Hyperopt format
            return {
                'loss': loss,
                'status': STATUS_OK,
                'metrics': metrics,
                'score': score
            }
        
        # Run optimization
        if seed is not None:
            np.random.seed(seed)
            
        best_params = fmin(
            fn=hyperopt_objective,
            space=self.space,
            algo=algo,
            max_evals=n_trials,
            trials=self.trials,
            verbose=verbose,
            rstate=np.random.RandomState(seed) if seed else None
        )
        
        # Get best result details
        best_trial = self.trials.best_trial
        best_score = -best_trial['result']['loss'] if direction == 'maximize' else best_trial['result']['loss']
        best_metrics = best_trial['result'].get('metrics', {})
        
        # Convert params back from Hyperopt format
        best_params = self._decode_params(best_params, param_space)
        
        return OptimizationResult(
            parameters=best_params,
            score=best_score,
            metrics=best_metrics,
            method=self.get_name(),
            iterations=len(self.trials.trials),
            convergence_history=self.convergence_history
        )
    
    def _create_hyperopt_space(self, param_space: Dict) -> Dict:
        """Convert parameter space to Hyperopt format"""
        hp_space = {}
        
        for param_name, param_def in param_space.items():
            if isinstance(param_def, dict):
                param_type = param_def.get('type', 'float')
                
                if param_type == 'float':
                    if param_def.get('log', False):
                        hp_space[param_name] = hp.loguniform(
                            param_name,
                            low=np.log(param_def['low']),
                            high=np.log(param_def['high'])
                        )
                    else:
                        hp_space[param_name] = hp.uniform(
                            param_name,
                            low=param_def['low'],
                            high=param_def['high']
                        )
                elif param_type == 'int':
                    hp_space[param_name] = scope.int(hp.quniform(
                        param_name,
                        low=param_def['low'],
                        high=param_def['high'],
                        q=1
                    ))
                elif param_type in ['choice', 'categorical']:
                    options = param_def.get('options', param_def.get('choices', []))
                    hp_space[param_name] = hp.choice(param_name, options)
                else:
                    raise ValueError(f"Unknown parameter type: {param_type}")
                    
            elif isinstance(param_def, tuple) and len(param_def) == 2:
                # Simple range format
                if isinstance(param_def[0], int) and isinstance(param_def[1], int):
                    hp_space[param_name] = scope.int(hp.quniform(
                        param_name,
                        low=param_def[0],
                        high=param_def[1],
                        q=1
                    ))
                else:
                    hp_space[param_name] = hp.uniform(
                        param_name,
                        low=float(param_def[0]),
                        high=float(param_def[1])
                    )
            elif isinstance(param_def, list):
                # Categorical choices
                hp_space[param_name] = hp.choice(param_name, param_def)
            else:
                raise ValueError(f"Invalid parameter definition for {param_name}")
        
        return hp_space
    
    def _decode_params(self, hp_params: Dict, original_space: Dict) -> Dict:
        """Convert Hyperopt parameters back to original format"""
        decoded = {}
        
        for param_name, value in hp_params.items():
            if param_name in original_space:
                param_def = original_space[param_name]
                
                # Handle categorical parameters that were encoded
                if isinstance(param_def, list):
                    # hp.choice returns index, need to get actual value
                    if isinstance(value, int) and value < len(param_def):
                        decoded[param_name] = param_def[value]
                    else:
                        decoded[param_name] = value
                elif isinstance(param_def, dict) and param_def.get('type') in ['choice', 'categorical']:
                    options = param_def.get('options', param_def.get('choices', []))
                    if isinstance(value, int) and value < len(options):
                        decoded[param_name] = options[value]
                    else:
                        decoded[param_name] = value
                else:
                    decoded[param_name] = value
            else:
                decoded[param_name] = value
        
        return decoded
    
    def _get_algorithm(self, algorithm: str):
        """Get Hyperopt algorithm object"""
        if algorithm == 'tpe':
            return tpe.suggest
        elif algorithm == 'random':
            return hyperopt.rand.suggest
        elif algorithm == 'anneal':
            return hyperopt.anneal.suggest
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}. Choose from: tpe, random, anneal")
    
    def get_name(self) -> str:
        return "hyperopt"
    
    def get_description(self) -> str:
        return "Tree-structured Parzen Estimator (TPE) Bayesian optimization"
    
    def get_trial_history(self) -> List[Dict]:
        """Get detailed history of all trials"""
        if not self.trials:
            return []
        
        history = []
        for trial in self.trials.trials:
            history.append({
                'params': trial['misc']['vals'],
                'loss': trial['result']['loss'],
                'status': trial['result']['status'],
                'metrics': trial['result'].get('metrics', {}),
                'tid': trial['tid']
            })
        
        return history
    
    def plot_optimization_history(self):
        """Plot optimization history"""
        if not self.trials:
            warnings.warn("No trials available to plot")
            return
        
        try:
            import matplotlib.pyplot as plt
            
            losses = [trial['result']['loss'] for trial in self.trials.trials]
            
            # Convert to scores if maximizing
            if self.direction == 'maximize':
                scores = [-l for l in losses]
                ylabel = "Score (maximizing)"
            else:
                scores = losses
                ylabel = "Loss (minimizing)"
            
            plt.figure(figsize=(10, 6))
            plt.plot(scores, alpha=0.5, label='All trials')
            
            # Plot running best
            running_best = []
            current_best = float('inf') if self.direction == 'minimize' else float('-inf')
            for score in scores:
                if self.direction == 'minimize':
                    current_best = min(current_best, score)
                else:
                    current_best = max(current_best, score)
                running_best.append(current_best)
            
            plt.plot(running_best, 'r-', linewidth=2, label='Best so far')
            plt.xlabel('Trial')
            plt.ylabel(ylabel)
            plt.title('Hyperopt Optimization History')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.show()
            
        except ImportError:
            warnings.warn("Matplotlib not installed. Cannot create visualization.")
            return None


class AsyncHyperoptAdapter(HyperoptAdapter):
    """Asynchronous/parallel version of Hyperopt adapter using MongoDB"""
    
    def optimize(self, param_space: Dict, n_trials: int = 100,
                mongo_url: str = 'localhost:27017/hyperopt',
                exp_key: str = None, **kwargs) -> OptimizationResult:
        """
        Perform parallel Hyperopt optimization using MongoDB
        
        Args:
            param_space: Parameter search space
            n_trials: Number of trials
            mongo_url: MongoDB connection URL
            exp_key: Experiment key for MongoDB
            **kwargs: Additional arguments passed to parent
        """
        try:
            from hyperopt.mongoexp import MongoTrials
        except ImportError:
            warnings.warn("MongoDB support not available. Falling back to serial execution.")
            return super().optimize(param_space, n_trials, **kwargs)
        
        if exp_key is None:
            import time
            exp_key = f"exp_{int(time.time())}"
        
        # Use MongoDB trials for parallel execution
        self.trials = MongoTrials(f'mongo://{mongo_url}/jobs', exp_key=exp_key)
        
        # Run optimization with MongoDB backend
        return super().optimize(param_space, n_trials, trials=self.trials, **kwargs)


# Register Hyperopt adapters with the factory
def register_hyperopt_adapters():
    """Register Hyperopt adapters with the optimization factory"""
    try:
        try:
            from optimization_adapter import OptimizationFactory
        except ImportError:
            from .optimization_adapter import OptimizationFactory
        
        if HYPEROPT_AVAILABLE:
            OptimizationFactory.register('hyperopt', HyperoptAdapter)
            OptimizationFactory.register('hyperopt_async', AsyncHyperoptAdapter)
            return True
        else:
            warnings.warn("Hyperopt not available. Install with: pip install hyperopt")
            return False
    except (ImportError, AttributeError) as e:
        warnings.warn(f"Could not register Hyperopt adapters with factory: {e}")
        return False