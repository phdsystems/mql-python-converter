"""
Adapter pattern implementation for different scoring metrics
Provides a unified interface for various performance metrics
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
import numpy as np
from dataclasses import dataclass


@dataclass
class TradeResult:
    """Represents a single trade result"""
    entry_price: float
    exit_price: float
    entry_time: int
    exit_time: int
    position_size: float = 1.0
    
    @property
    def return_pct(self) -> float:
        """Calculate percentage return"""
        return ((self.exit_price - self.entry_price) / self.entry_price) * 100
    
    @property
    def profit(self) -> float:
        """Calculate absolute profit"""
        return (self.exit_price - self.entry_price) * self.position_size


class MetricAdapter(ABC):
    """Abstract base class for metric adapters"""
    
    @abstractmethod
    def calculate(self, trades: List[TradeResult], prices: Optional[np.ndarray] = None) -> float:
        """Calculate the metric value"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get metric name"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get metric description"""
        pass
    
    @abstractmethod
    def is_higher_better(self) -> bool:
        """Return True if higher values are better"""
        pass


class SharpeRatioAdapter(MetricAdapter):
    """Adapter for Sharpe Ratio calculation"""
    
    def __init__(self, risk_free_rate: float = 0.0, periods_per_year: int = 252):
        self.risk_free_rate = risk_free_rate
        self.periods_per_year = periods_per_year
    
    def calculate(self, trades: List[TradeResult], prices: Optional[np.ndarray] = None) -> float:
        """Calculate Sharpe Ratio"""
        if not trades:
            return -999.0
        
        returns = [trade.return_pct / 100 for trade in trades]
        
        if len(returns) < 2:
            return 0.0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)
        
        if std_return == 0:
            return 0.0
        
        # Annualized Sharpe Ratio
        sharpe = (avg_return - self.risk_free_rate) / std_return
        sharpe_annualized = sharpe * np.sqrt(self.periods_per_year)
        
        return sharpe_annualized
    
    def get_name(self) -> str:
        return "sharpe_ratio"
    
    def get_description(self) -> str:
        return "Risk-adjusted return (annualized)"
    
    def is_higher_better(self) -> bool:
        return True


class TotalReturnAdapter(MetricAdapter):
    """Adapter for Total Return calculation"""
    
    def calculate(self, trades: List[TradeResult], prices: Optional[np.ndarray] = None) -> float:
        """Calculate total cumulative return"""
        if not trades:
            return 0.0
        
        total_return = sum(trade.return_pct for trade in trades)
        return total_return
    
    def get_name(self) -> str:
        return "total_return"
    
    def get_description(self) -> str:
        return "Total cumulative return (%)"
    
    def is_higher_better(self) -> bool:
        return True


class WinRateAdapter(MetricAdapter):
    """Adapter for Win Rate calculation"""
    
    def calculate(self, trades: List[TradeResult], prices: Optional[np.ndarray] = None) -> float:
        """Calculate win rate percentage"""
        if not trades:
            return 0.0
        
        winning_trades = sum(1 for trade in trades if trade.return_pct > 0)
        win_rate = (winning_trades / len(trades)) * 100
        
        return win_rate
    
    def get_name(self) -> str:
        return "win_rate"
    
    def get_description(self) -> str:
        return "Percentage of winning trades"
    
    def is_higher_better(self) -> bool:
        return True


class ProfitFactorAdapter(MetricAdapter):
    """Adapter for Profit Factor calculation"""
    
    def calculate(self, trades: List[TradeResult], prices: Optional[np.ndarray] = None) -> float:
        """Calculate profit factor (gross profit / gross loss)"""
        if not trades:
            return 0.0
        
        gross_profit = sum(trade.profit for trade in trades if trade.profit > 0)
        gross_loss = abs(sum(trade.profit for trade in trades if trade.profit < 0))
        
        if gross_loss == 0:
            return 999.0 if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def get_name(self) -> str:
        return "profit_factor"
    
    def get_description(self) -> str:
        return "Gross profit / Gross loss"
    
    def is_higher_better(self) -> bool:
        return True


class MaxDrawdownAdapter(MetricAdapter):
    """Adapter for Maximum Drawdown calculation"""
    
    def calculate(self, trades: List[TradeResult], prices: Optional[np.ndarray] = None) -> float:
        """Calculate maximum drawdown percentage"""
        if not trades:
            return 0.0
        
        # Calculate cumulative returns
        cumulative = 1.0
        equity_curve = [1.0]
        
        for trade in trades:
            cumulative *= (1 + trade.return_pct / 100)
            equity_curve.append(cumulative)
        
        # Calculate maximum drawdown
        peak = equity_curve[0]
        max_dd = 0.0
        
        for value in equity_curve:
            peak = max(peak, value)
            drawdown = ((value - peak) / peak) * 100
            max_dd = min(max_dd, drawdown)
        
        return abs(max_dd)  # Return positive value
    
    def get_name(self) -> str:
        return "max_drawdown"
    
    def get_description(self) -> str:
        return "Maximum peak-to-trough decline (%)"
    
    def is_higher_better(self) -> bool:
        return False  # Lower drawdown is better


class CalmarRatioAdapter(MetricAdapter):
    """Adapter for Calmar Ratio calculation"""
    
    def __init__(self, periods_per_year: int = 252):
        self.periods_per_year = periods_per_year
    
    def calculate(self, trades: List[TradeResult], prices: Optional[np.ndarray] = None) -> float:
        """Calculate Calmar Ratio (annual return / max drawdown)"""
        if not trades:
            return 0.0
        
        # Calculate annualized return
        total_return = sum(trade.return_pct for trade in trades) / 100
        num_periods = len(trades)
        
        if num_periods == 0:
            return 0.0
        
        annualized_return = total_return * (self.periods_per_year / num_periods)
        
        # Calculate max drawdown
        max_dd_adapter = MaxDrawdownAdapter()
        max_dd = max_dd_adapter.calculate(trades, prices) / 100
        
        if max_dd == 0:
            return 999.0 if annualized_return > 0 else 0.0
        
        return annualized_return / max_dd
    
    def get_name(self) -> str:
        return "calmar_ratio"
    
    def get_description(self) -> str:
        return "Annual return / Max drawdown"
    
    def is_higher_better(self) -> bool:
        return True


class SortinoRatioAdapter(MetricAdapter):
    """Adapter for Sortino Ratio calculation"""
    
    def __init__(self, target_return: float = 0.0, periods_per_year: int = 252):
        self.target_return = target_return
        self.periods_per_year = periods_per_year
    
    def calculate(self, trades: List[TradeResult], prices: Optional[np.ndarray] = None) -> float:
        """Calculate Sortino Ratio (uses downside deviation)"""
        if not trades or len(trades) < 2:
            return 0.0
        
        returns = [trade.return_pct / 100 for trade in trades]
        avg_return = np.mean(returns)
        
        # Calculate downside deviation
        downside_returns = [r for r in returns if r < self.target_return]
        
        if not downside_returns:
            return 999.0  # No downside risk
        
        downside_dev = np.std(downside_returns, ddof=1)
        
        if downside_dev == 0:
            return 0.0
        
        # Annualized Sortino Ratio
        sortino = (avg_return - self.target_return) / downside_dev
        sortino_annualized = sortino * np.sqrt(self.periods_per_year)
        
        return sortino_annualized
    
    def get_name(self) -> str:
        return "sortino_ratio"
    
    def get_description(self) -> str:
        return "Risk-adjusted return (downside deviation)"
    
    def is_higher_better(self) -> bool:
        return True


class MetricFactory:
    """Factory class for creating metric adapters"""
    
    _metrics = {
        'sharpe_ratio': SharpeRatioAdapter,
        'total_return': TotalReturnAdapter,
        'win_rate': WinRateAdapter,
        'profit_factor': ProfitFactorAdapter,
        'max_drawdown': MaxDrawdownAdapter,
        'calmar_ratio': CalmarRatioAdapter,
        'sortino_ratio': SortinoRatioAdapter
    }
    
    @classmethod
    def create(cls, metric_name: str, **kwargs) -> MetricAdapter:
        """Create a metric adapter by name"""
        if metric_name not in cls._metrics:
            raise ValueError(f"Unknown metric: {metric_name}. Available: {list(cls._metrics.keys())}")
        
        metric_class = cls._metrics[metric_name]
        
        # Pass kwargs only to metrics that accept them
        if metric_name in ['sharpe_ratio', 'calmar_ratio', 'sortino_ratio']:
            return metric_class(**kwargs)
        else:
            return metric_class()
    
    @classmethod
    def list_available(cls) -> List[str]:
        """List all available metrics"""
        return list(cls._metrics.keys())
    
    @classmethod
    def register(cls, name: str, metric_class: type):
        """Register a new metric adapter"""
        if not issubclass(metric_class, MetricAdapter):
            raise TypeError("Metric class must inherit from MetricAdapter")
        cls._metrics[name] = metric_class


class CompositeMetric(MetricAdapter):
    """Composite metric that combines multiple metrics with weights"""
    
    def __init__(self, metrics: Dict[str, float], normalize: bool = True):
        """
        Initialize composite metric
        
        Args:
            metrics: Dict of metric_name -> weight
            normalize: Whether to normalize weights to sum to 1
        """
        self.metrics = {}
        total_weight = sum(metrics.values()) if normalize else 1.0
        
        for name, weight in metrics.items():
            adapter = MetricFactory.create(name)
            normalized_weight = weight / total_weight if normalize else weight
            self.metrics[adapter] = normalized_weight
    
    def calculate(self, trades: List[TradeResult], prices: Optional[np.ndarray] = None) -> float:
        """Calculate weighted composite score"""
        if not trades:
            return 0.0
        
        composite_score = 0.0
        
        for adapter, weight in self.metrics.items():
            score = adapter.calculate(trades, prices)
            
            # Normalize score based on whether higher is better
            if not adapter.is_higher_better():
                # For metrics where lower is better, invert
                score = -score if score != 0 else 0
            
            composite_score += score * weight
        
        return composite_score
    
    def get_name(self) -> str:
        return "composite_metric"
    
    def get_description(self) -> str:
        components = [f"{adapter.get_name()}({weight:.2f})" 
                     for adapter, weight in self.metrics.items()]
        return f"Weighted composite: {', '.join(components)}"
    
    def is_higher_better(self) -> bool:
        return True