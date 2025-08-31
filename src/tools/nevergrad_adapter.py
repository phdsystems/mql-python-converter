"""
Nevergrad integration adapter for the optimization framework
Provides gradient-free optimization from Facebook Research
"""

from typing import Dict, List, Tuple, Optional, Callable, Any, Union
import numpy as np
from dataclasses import dataclass
import warnings

try:
    import nevergrad as ng
    from nevergrad import parametrization as p
    from nevergrad.optimization import optimizerlib
    NEVERGRAD_AVAILABLE = True
except ImportError:
    NEVERGRAD_AVAILABLE = False
    warnings.warn("Nevergrad not installed. Install with: pip install nevergrad")

# Import base optimization framework
try:
    from optimization_adapter import OptimizationAdapter, OptimizationResult
except ImportError:
    from .optimization_adapter import OptimizationAdapter, OptimizationResult


class NevergradAdapter(OptimizationAdapter):
    """Adapter for Nevergrad optimization framework"""
    
    def __init__(self, objective_function: Callable, metric_adapter: Any):
        """
        Initialize Nevergrad adapter
        
        Args:
            objective_function: Function that takes parameters and returns score
            metric_adapter: Metric adapter to use for scoring
        """
        super().__init__(objective_function, metric_adapter)
        if not NEVERGRAD_AVAILABLE:
            raise ImportError("Nevergrad is not installed. Install with: pip install nevergrad")
        
        self.optimizer = None
        self.parametrization = None
        self.recommendation = None
        
    def optimize(self, param_space: Dict, budget: int = 100,
                algorithm: str = 'NGOpt', direction: str = 'maximize',
                num_workers: int = 1, verbose: bool = False,
                seed: Optional[int] = None, **kwargs) -> OptimizationResult:
        """
        Perform Nevergrad optimization
        
        Args:
            param_space: Dict defining parameter search space
                - For continuous: {'param': (min, max)} or {'param': {'type': 'float', 'low': min, 'high': max}}
                - For discrete: {'param': [val1, val2, ...]} or {'param': {'type': 'choice', 'options': [...]}}
                - For integers: {'param': {'type': 'int', 'low': min, 'high': max}}
                - For log scale: {'param': {'type': 'float', 'low': min, 'high': max, 'log': True}}
            budget: Total number of evaluations
            algorithm: Optimization algorithm (see list below)
            direction: Optimization direction ('maximize' or 'minimize')
            num_workers: Number of parallel workers
            verbose: Whether to print progress
            seed: Random seed
            
        Available algorithms:
            - 'NGOpt': Nevergrad's meta-optimizer (recommended)
            - 'CMA': Covariance Matrix Adaptation Evolution Strategy
            - 'PSO': Particle Swarm Optimization
            - 'DE': Differential Evolution
            - 'OnePlusOne': (1+1) Evolution Strategy
            - 'TwoPointsDE': Two Points Differential Evolution
            - 'RandomSearch': Random search baseline
            - 'TBPSA': Test-Based Population Size Adaptation
            - 'SPSA': Simultaneous Perturbation Stochastic Approximation
            - 'NelderMead': Nelder-Mead simplex algorithm
            - 'Powell': Powell's method
            - 'ScrHammersleySearch': Scrambled Hammersley search
            - 'MetaModel': Metamodel-based optimization
        """
        self.iteration_count = 0
        self.convergence_history = []
        self.direction = direction
        
        # Set random seed if provided
        if seed is not None:
            np.random.seed(seed)
        
        # Create Nevergrad parametrization
        self.parametrization = self._create_nevergrad_parametrization(param_space)
        
        # Create optimizer
        self.optimizer = self._create_optimizer(
            algorithm, self.parametrization, budget, num_workers
        )
        
        # Optimization loop
        best_score = float('-inf') if direction == 'maximize' else float('inf')
        best_params = None
        best_metrics = None
        
        for _ in range(budget):
            # Ask for a candidate
            x = self.optimizer.ask()
            
            # Convert Nevergrad candidate to dict
            params = self._candidate_to_dict(x)
            
            # Evaluate
            score, metrics = self._evaluate(params)
            self.convergence_history.append(score)
            
            # Nevergrad minimizes, so negate if maximizing
            loss = -score if direction == 'maximize' else score
            
            # Tell the optimizer about the result
            self.optimizer.tell(x, loss)
            
            # Track best
            if direction == 'maximize':
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_metrics = metrics
                    if verbose:
                        print(f"Iteration {self.iteration_count}: New best score = {best_score:.4f}")
            else:
                if score < best_score:
                    best_score = score
                    best_params = params
                    best_metrics = metrics
                    if verbose:
                        print(f"Iteration {self.iteration_count}: New best score = {best_score:.4f}")
        
        # Get final recommendation
        self.recommendation = self.optimizer.provide_recommendation()
        recommended_params = self._candidate_to_dict(self.recommendation)
        
        # Evaluate recommendation if different from best found
        if recommended_params != best_params:
            rec_score, rec_metrics = self._evaluate(recommended_params)
            if (direction == 'maximize' and rec_score > best_score) or \
               (direction == 'minimize' and rec_score < best_score):
                best_params = recommended_params
                best_score = rec_score
                best_metrics = rec_metrics
        
        return OptimizationResult(
            parameters=best_params,
            score=best_score,
            metrics=best_metrics,
            method=self.get_name(),
            iterations=self.iteration_count,
            convergence_history=self.convergence_history
        )
    
    def _create_nevergrad_parametrization(self, param_space: Dict):
        """Convert parameter space to Nevergrad parametrization"""
        ng_params = {}
        
        for param_name, param_def in param_space.items():
            if isinstance(param_def, dict):
                param_type = param_def.get('type', 'float')
                
                if param_type == 'float':
                    lower = param_def['low']
                    upper = param_def['high']
                    
                    if param_def.get('log', False):
                        # Log scale
                        ng_params[param_name] = p.Log(
                            lower=lower,
                            upper=upper
                        )
                    else:
                        # Linear scale
                        ng_params[param_name] = p.Scalar(
                            lower=lower,
                            upper=upper
                        )
                        
                elif param_type == 'int':
                    ng_params[param_name] = p.IntegerScalar(
                        lower=param_def['low'],
                        upper=param_def['high']
                    )
                    
                elif param_type in ['choice', 'categorical']:
                    choices = param_def.get('choices', param_def.get('options', []))
                    ng_params[param_name] = p.Choice(choices)
                    
                else:
                    raise ValueError(f"Unknown parameter type: {param_type}")
                    
            elif isinstance(param_def, tuple) and len(param_def) == 2:
                # Simple range format
                if isinstance(param_def[0], int) and isinstance(param_def[1], int):
                    ng_params[param_name] = p.IntegerScalar(
                        lower=param_def[0],
                        upper=param_def[1]
                    )
                else:
                    ng_params[param_name] = p.Scalar(
                        lower=float(param_def[0]),
                        upper=float(param_def[1])
                    )
                    
            elif isinstance(param_def, list):
                # Categorical choices
                ng_params[param_name] = p.Choice(param_def)
                
            else:
                raise ValueError(f"Invalid parameter definition for {param_name}")
        
        return p.Dict(**ng_params)
    
    def _create_optimizer(self, algorithm: str, parametrization, 
                         budget: int, num_workers: int):
        """Create Nevergrad optimizer"""
        # Map common names to Nevergrad optimizer names
        optimizer_map = {
            'NGOpt': 'NGOpt',
            'CMA': 'CMA',
            'PSO': 'PSO',
            'DE': 'DE',
            'OnePlusOne': 'OnePlusOne',
            'TwoPointsDE': 'TwoPointsDE',
            'RandomSearch': 'RandomSearch',
            'TBPSA': 'TBPSA',
            'SPSA': 'SPSA',
            'NelderMead': 'NelderMead',
            'Powell': 'Powell',
            'ScrHammersleySearch': 'ScrHammersleySearch',
            'MetaModel': 'MetaModel',
            'DiagonalCMA': 'DiagonalCMA',
            'FCMA': 'FCMA',
            'BO': 'BO',  # Bayesian Optimization
            'LHSSearch': 'LHSSearch',  # Latin Hypercube Sampling
            'SobolSearch': 'SobolSearch',  # Sobol sequence search
        }
        
        if algorithm not in optimizer_map:
            warnings.warn(f"Unknown algorithm {algorithm}, using NGOpt")
            algorithm = 'NGOpt'
        
        optimizer_name = optimizer_map[algorithm]
        
        # Create optimizer with budget and workers
        return ng.optimizers.registry[optimizer_name](
            parametrization=parametrization,
            budget=budget,
            num_workers=num_workers
        )
    
    def _candidate_to_dict(self, candidate) -> Dict:
        """Convert Nevergrad candidate to dictionary"""
        if hasattr(candidate, 'value'):
            value = candidate.value
            if isinstance(value, dict):
                return value
            else:
                # Single parameter case
                return {'param': value}
        else:
            # Already a dict or other structure
            return dict(candidate)
    
    def get_name(self) -> str:
        return "nevergrad"
    
    def get_description(self) -> str:
        return "Gradient-free optimization from Facebook Research"
    
    def get_optimizer_info(self) -> Dict:
        """Get information about the optimizer"""
        if not self.optimizer:
            return {}
        
        info = {
            'name': self.optimizer.name,
            'budget': self.optimizer.budget,
            'num_workers': self.optimizer.num_workers,
            'num_ask': self.optimizer.num_ask,
            'num_tell': self.optimizer.num_tell,
        }
        
        if self.recommendation:
            info['recommendation'] = self._candidate_to_dict(self.recommendation)
        
        return info


class MultiObjectiveNevergradAdapter(NevergradAdapter):
    """Multi-objective optimization with Nevergrad"""
    
    def optimize(self, param_space: Dict, objectives: List[str],
                budget: int = 100, algorithm: str = 'NSGA2',
                verbose: bool = False, seed: Optional[int] = None,
                **kwargs) -> List[OptimizationResult]:
        """
        Perform multi-objective optimization
        
        Args:
            param_space: Parameter search space
            objectives: List of objective names to optimize
            budget: Total number of evaluations
            algorithm: Multi-objective algorithm ('NSGA2', 'CMA', 'DE')
            verbose: Whether to print progress
            seed: Random seed
            
        Returns:
            List of Pareto-optimal solutions
        """
        self.iteration_count = 0
        self.objectives = objectives
        
        if seed is not None:
            np.random.seed(seed)
        
        # Create parametrization
        self.parametrization = self._create_nevergrad_parametrization(param_space)
        
        # Use multi-objective optimizer
        if algorithm == 'NSGA2':
            # NSGA-II is not directly available in Nevergrad
            # Use CMA with multi-objective support
            self.optimizer = ng.optimizers.CMA(
                parametrization=self.parametrization,
                budget=budget
            )
        else:
            self.optimizer = self._create_optimizer(
                algorithm, self.parametrization, budget, 1
            )
        
        # Track Pareto front
        pareto_front = []
        
        for _ in range(budget):
            x = self.optimizer.ask()
            params = self._candidate_to_dict(x)
            
            # Evaluate all objectives
            score, metrics = self._evaluate(params)
            
            # Create multi-objective loss
            losses = []
            for obj in objectives:
                if obj in metrics:
                    # Nevergrad minimizes, so negate for maximization
                    losses.append(-metrics[obj])
                else:
                    losses.append(0)
            
            # Tell optimizer (use scalarization for now)
            self.optimizer.tell(x, sum(losses))
            
            # Track solution
            pareto_front.append({
                'params': params,
                'score': score,
                'metrics': metrics
            })
        
        # Filter to get Pareto-optimal solutions
        pareto_optimal = self._filter_pareto_optimal(pareto_front, objectives)
        
        # Convert to OptimizationResult objects
        results = []
        for solution in pareto_optimal:
            results.append(OptimizationResult(
                parameters=solution['params'],
                score=solution['score'],
                metrics=solution['metrics'],
                method=f"{self.get_name()}_multi",
                iterations=1,
                convergence_history=None
            ))
        
        return results
    
    def _filter_pareto_optimal(self, solutions: List[Dict], 
                               objectives: List[str]) -> List[Dict]:
        """Filter solutions to keep only Pareto-optimal ones"""
        pareto_front = []
        
        for candidate in solutions:
            is_dominated = False
            
            for other in solutions:
                if candidate == other:
                    continue
                
                # Check if other dominates candidate
                dominates = True
                for obj in objectives:
                    if candidate['metrics'].get(obj, 0) >= other['metrics'].get(obj, 0):
                        dominates = False
                        break
                
                if dominates:
                    is_dominated = True
                    break
            
            if not is_dominated:
                pareto_front.append(candidate)
        
        return pareto_front


# Register Nevergrad adapters with the factory
def register_nevergrad_adapters():
    """Register Nevergrad adapters with the optimization factory"""
    try:
        try:
            from optimization_adapter import OptimizationFactory
        except ImportError:
            from .optimization_adapter import OptimizationFactory
        
        if NEVERGRAD_AVAILABLE:
            OptimizationFactory.register('nevergrad', NevergradAdapter)
            OptimizationFactory.register('ng', NevergradAdapter)  # Alias
            OptimizationFactory.register('nevergrad_multi', MultiObjectiveNevergradAdapter)
            return True
        else:
            warnings.warn("Nevergrad not available. Install with: pip install nevergrad")
            return False
    except (ImportError, AttributeError) as e:
        warnings.warn(f"Could not register Nevergrad adapters with factory: {e}")
        return False