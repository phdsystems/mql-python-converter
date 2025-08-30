"""
Optuna integration adapter for the optimization framework
Provides advanced hyperparameter optimization capabilities
"""

import optuna
from typing import Dict, List, Tuple, Optional, Callable, Any, Union
import numpy as np
from dataclasses import dataclass
import warnings

# Import base optimization framework
try:
    from optimization_adapter import OptimizationAdapter, OptimizationResult
except ImportError:
    from .optimization_adapter import OptimizationAdapter, OptimizationResult


class OptunaAdapter(OptimizationAdapter):
    """Adapter for Optuna hyperparameter optimization framework"""
    
    def __init__(self, objective_function: Callable, metric_adapter: Any):
        """
        Initialize Optuna adapter
        
        Args:
            objective_function: Function that takes parameters and returns score
            metric_adapter: Metric adapter to use for scoring
        """
        super().__init__(objective_function, metric_adapter)
        self.study = None
        self.param_definitions = {}
        
    def optimize(self, param_space: Dict, n_trials: int = 100,
                sampler: str = 'tpe', direction: str = 'maximize',
                timeout: Optional[float] = None, n_jobs: int = 1,
                verbose: bool = False, seed: Optional[int] = None,
                pruner: Optional[str] = None, **kwargs) -> OptimizationResult:
        """
        Perform Optuna optimization
        
        Args:
            param_space: Dict defining parameter search space
                - For continuous: {'param': (min, max)} or {'param': {'type': 'float', 'low': min, 'high': max}}
                - For discrete: {'param': [val1, val2, ...]} or {'param': {'type': 'categorical', 'choices': [...]}}
                - For integers: {'param': {'type': 'int', 'low': min, 'high': max}}
                - For log scale: {'param': {'type': 'float', 'low': min, 'high': max, 'log': True}}
            n_trials: Number of trials to run
            sampler: Sampling algorithm ('tpe', 'random', 'grid', 'cmaes')
            direction: Optimization direction ('maximize' or 'minimize')
            timeout: Stop optimization after this many seconds
            n_jobs: Number of parallel jobs (-1 for all cores)
            verbose: Whether to print progress
            seed: Random seed for reproducibility
            pruner: Pruning algorithm ('median', 'percentile', 'hyperband', None)
        """
        self.iteration_count = 0
        self.convergence_history = []
        
        # Store parameter space for trial suggestion
        self.param_definitions = self._parse_param_space(param_space)
        
        # Create sampler
        sampler_obj = self._create_sampler(sampler, seed)
        
        # Create pruner if specified
        pruner_obj = self._create_pruner(pruner) if pruner else None
        
        # Create study
        self.study = optuna.create_study(
            direction=direction,
            sampler=sampler_obj,
            pruner=pruner_obj,
            study_name=f"optimization_{self.metric_adapter.get_name()}"
        )
        
        # Set logging verbosity
        if not verbose:
            optuna.logging.set_verbosity(optuna.logging.WARNING)
        
        # Define objective wrapper
        def optuna_objective(trial):
            # Suggest parameters based on definitions
            params = self._suggest_params(trial)
            
            # Evaluate
            score, metrics = self._evaluate(params)
            self.convergence_history.append(score)
            
            # Report intermediate values for pruning
            if pruner:
                trial.report(score, self.iteration_count)
                if trial.should_prune():
                    raise optuna.TrialPruned()
            
            return score
        
        # Run optimization
        try:
            self.study.optimize(
                optuna_objective,
                n_trials=n_trials,
                timeout=timeout,
                n_jobs=n_jobs if n_jobs != -1 else None,
                show_progress_bar=verbose
            )
        except KeyboardInterrupt:
            if verbose:
                print("Optimization interrupted by user")
        
        # Get best result
        best_trial = self.study.best_trial
        best_score, best_metrics = self._evaluate(best_trial.params)
        
        return OptimizationResult(
            parameters=best_trial.params,
            score=best_score,
            metrics=best_metrics,
            method=self.get_name(),
            iterations=len(self.study.trials),
            convergence_history=self.convergence_history
        )
    
    def _parse_param_space(self, param_space: Dict) -> Dict:
        """Parse parameter space into Optuna format"""
        definitions = {}
        
        for param_name, param_def in param_space.items():
            if isinstance(param_def, dict):
                # Already in detailed format
                definitions[param_name] = param_def
            elif isinstance(param_def, tuple) and len(param_def) == 2:
                # Simple range format (min, max)
                if isinstance(param_def[0], int) and isinstance(param_def[1], int):
                    definitions[param_name] = {
                        'type': 'int',
                        'low': param_def[0],
                        'high': param_def[1]
                    }
                else:
                    definitions[param_name] = {
                        'type': 'float',
                        'low': float(param_def[0]),
                        'high': float(param_def[1])
                    }
            elif isinstance(param_def, list):
                # Categorical choices
                definitions[param_name] = {
                    'type': 'categorical',
                    'choices': param_def
                }
            else:
                raise ValueError(f"Invalid parameter definition for {param_name}")
        
        return definitions
    
    def _suggest_params(self, trial: optuna.Trial) -> Dict:
        """Suggest parameters for a trial"""
        params = {}
        
        for param_name, param_def in self.param_definitions.items():
            param_type = param_def['type']
            
            if param_type == 'float':
                params[param_name] = trial.suggest_float(
                    param_name,
                    param_def['low'],
                    param_def['high'],
                    log=param_def.get('log', False)
                )
            elif param_type == 'int':
                params[param_name] = trial.suggest_int(
                    param_name,
                    param_def['low'],
                    param_def['high'],
                    log=param_def.get('log', False)
                )
            elif param_type == 'categorical':
                params[param_name] = trial.suggest_categorical(
                    param_name,
                    param_def['choices']
                )
            else:
                raise ValueError(f"Unknown parameter type: {param_type}")
        
        return params
    
    def _create_sampler(self, sampler: str, seed: Optional[int]):
        """Create Optuna sampler"""
        if sampler == 'tpe':
            return optuna.samplers.TPESampler(seed=seed)
        elif sampler == 'random':
            return optuna.samplers.RandomSampler(seed=seed)
        elif sampler == 'grid':
            # Grid search requires explicit search space
            search_space = {}
            for param_name, param_def in self.param_definitions.items():
                if param_def['type'] == 'categorical':
                    search_space[param_name] = param_def['choices']
                else:
                    # For continuous params, create a grid
                    if param_def['type'] == 'int':
                        n_points = min(10, param_def['high'] - param_def['low'] + 1)
                        search_space[param_name] = list(range(
                            param_def['low'],
                            param_def['high'] + 1,
                            max(1, (param_def['high'] - param_def['low']) // n_points)
                        ))
                    else:
                        n_points = 10
                        search_space[param_name] = np.linspace(
                            param_def['low'],
                            param_def['high'],
                            n_points
                        ).tolist()
            return optuna.samplers.GridSampler(search_space)
        elif sampler == 'cmaes':
            return optuna.samplers.CmaEsSampler(seed=seed)
        else:
            raise ValueError(f"Unknown sampler: {sampler}")
    
    def _create_pruner(self, pruner: str):
        """Create Optuna pruner"""
        if pruner == 'median':
            return optuna.pruners.MedianPruner()
        elif pruner == 'percentile':
            return optuna.pruners.PercentilePruner(percentile=25.0)
        elif pruner == 'hyperband':
            return optuna.pruners.HyperbandPruner()
        else:
            raise ValueError(f"Unknown pruner: {pruner}")
    
    def get_name(self) -> str:
        return "optuna"
    
    def get_description(self) -> str:
        return "Advanced hyperparameter optimization using Optuna framework"
    
    def get_study_statistics(self) -> Dict:
        """Get optimization study statistics"""
        if not self.study:
            return {}
        
        return {
            'n_trials': len(self.study.trials),
            'best_value': self.study.best_value,
            'best_params': self.study.best_params,
            'n_complete': len([t for t in self.study.trials if t.state == optuna.trial.TrialState.COMPLETE]),
            'n_pruned': len([t for t in self.study.trials if t.state == optuna.trial.TrialState.PRUNED]),
            'n_failed': len([t for t in self.study.trials if t.state == optuna.trial.TrialState.FAIL])
        }
    
    def plot_optimization_history(self):
        """Plot optimization history (requires plotly)"""
        if not self.study:
            warnings.warn("No study available to plot")
            return
        
        try:
            import optuna.visualization as vis
            return vis.plot_optimization_history(self.study)
        except ImportError:
            warnings.warn("Plotly not installed. Cannot create visualization.")
            return None
    
    def plot_param_importances(self):
        """Plot parameter importances (requires plotly)"""
        if not self.study:
            warnings.warn("No study available to plot")
            return
        
        try:
            import optuna.visualization as vis
            return vis.plot_param_importances(self.study)
        except ImportError:
            warnings.warn("Plotly not installed. Cannot create visualization.")
            return None


class MultiObjectiveOptunaAdapter(OptunaAdapter):
    """Adapter for multi-objective optimization with Optuna"""
    
    def optimize(self, param_space: Dict, objectives: List[str],
                n_trials: int = 100, sampler: str = 'nsga2',
                verbose: bool = False, seed: Optional[int] = None,
                **kwargs) -> List[OptimizationResult]:
        """
        Perform multi-objective optimization
        
        Args:
            param_space: Parameter search space
            objectives: List of objective names to optimize
            n_trials: Number of trials
            sampler: Multi-objective sampler ('nsga2', 'random')
            verbose: Whether to print progress
            seed: Random seed
        
        Returns:
            List of Pareto-optimal solutions
        """
        self.iteration_count = 0
        self.objectives = objectives
        self.param_definitions = self._parse_param_space(param_space)
        
        # Create multi-objective sampler
        if sampler == 'nsga2':
            sampler_obj = optuna.samplers.NSGAIISampler(seed=seed)
        else:
            sampler_obj = optuna.samplers.RandomSampler(seed=seed)
        
        # Create multi-objective study
        self.study = optuna.create_study(
            directions=['maximize'] * len(objectives),
            sampler=sampler_obj
        )
        
        if not verbose:
            optuna.logging.set_verbosity(optuna.logging.WARNING)
        
        def multi_objective(trial):
            params = self._suggest_params(trial)
            score, metrics = self._evaluate(params)
            
            # Extract multiple objectives
            objective_values = []
            for obj_name in objectives:
                if obj_name in metrics:
                    objective_values.append(metrics[obj_name])
                else:
                    objective_values.append(score)
            
            return objective_values
        
        # Run optimization
        self.study.optimize(multi_objective, n_trials=n_trials)
        
        # Get Pareto front
        pareto_front = []
        for trial in self.study.best_trials:
            score, metrics = self._evaluate(trial.params)
            pareto_front.append(OptimizationResult(
                parameters=trial.params,
                score=score,
                metrics=metrics,
                method=f"{self.get_name()}_multi",
                iterations=1,
                convergence_history=None
            ))
        
        return pareto_front


# Register Optuna adapters with the factory
def register_optuna_adapters():
    """Register Optuna adapters with the optimization factory"""
    try:
        try:
            from optimization_adapter import OptimizationFactory
        except ImportError:
            from .optimization_adapter import OptimizationFactory
        
        OptimizationFactory.register('optuna', OptunaAdapter)
        OptimizationFactory.register('optuna_multi', MultiObjectiveOptunaAdapter)
        return True
    except (ImportError, AttributeError) as e:
        warnings.warn(f"Could not register Optuna adapters with factory: {e}")
        return False