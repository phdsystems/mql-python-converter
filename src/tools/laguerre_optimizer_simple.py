"""
Simplified Parameter Optimizer for Adaptive Laguerre Filter
Works without external dependencies
"""

import random
import json
from typing import Dict, List, Tuple
from datetime import datetime
import math

class SimpleOptimizer:
    """
    Parameter optimizer using built-in Python libraries only
    """
    
    def __init__(self, prices: List[float], metric: str = 'return'):
        self.prices = prices
        self.metric = metric
        self.results = []
        self.best_result = None
        
    def grid_search(self, param_grid: Dict) -> Dict:
        """
        Grid search through all parameter combinations
        """
        print("Starting Grid Search Optimization...")
        
        # Generate all combinations
        combinations = self._generate_combinations(param_grid)
        print(f"Testing {len(combinations)} parameter combinations...")
        
        best_score = -float('inf')
        best_params = None
        
        for i, params in enumerate(combinations):
            score = self._evaluate_params(params)
            
            if score > best_score:
                best_score = score
                best_params = params
            
            if (i + 1) % 10 == 0:
                print(f"Progress: {i+1}/{len(combinations)}")
        
        self.best_result = {'params': best_params, 'score': best_score}
        
        print(f"\nBest parameters found:")
        for key, value in best_params.items():
            print(f"  {key}: {value}")
        print(f"Score: {best_score:.4f}")
        
        return self.best_result
    
    def random_search(self, param_ranges: Dict, n_iter: int = 50) -> Dict:
        """
        Random search optimization
        """
        print(f"Starting Random Search ({n_iter} iterations)...")
        
        best_score = -float('inf')
        best_params = None
        
        for i in range(n_iter):
            # Generate random parameters
            params = {}
            for key, (min_val, max_val) in param_ranges.items():
                if isinstance(min_val, int):
                    params[key] = random.randint(min_val, max_val)
                else:
                    params[key] = random.uniform(min_val, max_val)
            
            score = self._evaluate_params(params)
            
            if score > best_score:
                best_score = score
                best_params = params
            
            if (i + 1) % 10 == 0:
                print(f"Progress: {i+1}/{n_iter}")
        
        self.best_result = {'params': best_params, 'score': best_score}
        
        print(f"\nBest parameters found:")
        for key, value in best_params.items():
            print(f"  {key}: {value}")
        print(f"Score: {best_score:.4f}")
        
        return self.best_result
    
    def _generate_combinations(self, param_grid: Dict) -> List[Dict]:
        """Generate all parameter combinations from grid"""
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        combinations = []
        
        # Recursive combination generation
        def generate(index, current):
            if index == len(keys):
                combinations.append(current.copy())
                return
            
            for value in values[index]:
                current[keys[index]] = value
                generate(index + 1, current)
        
        generate(0, {})
        return combinations
    
    def _evaluate_params(self, params: Dict) -> float:
        """
        Evaluate parameter combination
        Simplified evaluation using basic moving average crossover
        """
        length = params.get('length', 10)
        order = params.get('order', 4)
        
        if length >= len(self.prices) // 2:
            return -999
        
        # Calculate simple moving averages as proxy
        fast_ma = self._calculate_ma(self.prices, length)
        slow_ma = self._calculate_ma(self.prices, length * 2)
        
        # Generate signals
        signals = []
        for i in range(len(fast_ma)):
            if fast_ma[i] is not None and slow_ma[i] is not None:
                if fast_ma[i] > slow_ma[i]:
                    signals.append(1)
                else:
                    signals.append(-1)
            else:
                signals.append(0)
        
        # Calculate returns
        returns = []
        for i in range(1, len(self.prices)):
            if signals[i-1] != 0:
                ret = (self.prices[i] - self.prices[i-1]) / self.prices[i-1]
                returns.append(ret * signals[i-1])
        
        if not returns:
            return -999
        
        # Calculate metrics
        total_return = sum(returns) * 100
        
        if self.metric == 'return':
            return total_return
        elif self.metric == 'sharpe':
            if len(returns) > 1:
                avg_return = sum(returns) / len(returns)
                std_return = self._calculate_std(returns)
                if std_return > 0:
                    return avg_return / std_return * math.sqrt(252)
            return 0
        elif self.metric == 'win_rate':
            wins = sum(1 for r in returns if r > 0)
            return wins / len(returns) * 100 if returns else 0
        
        return total_return
    
    def _calculate_ma(self, prices: List[float], period: int) -> List[float]:
        """Calculate moving average"""
        ma = []
        for i in range(len(prices)):
            if i < period - 1:
                ma.append(None)
            else:
                avg = sum(prices[i-period+1:i+1]) / period
                ma.append(avg)
        return ma
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)


class ParameterRecommender:
    """
    Recommends optimal parameters based on market conditions
    """
    
    @staticmethod
    def analyze_market(prices: List[float]) -> Dict:
        """Analyze market characteristics"""
        # Calculate volatility
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        volatility = 0
        if returns:
            mean_return = sum(returns) / len(returns)
            volatility = math.sqrt(sum((r - mean_return) ** 2 for r in returns) / len(returns))
        
        # Detect trend
        trend_strength = 0
        if len(prices) > 20:
            ma20 = sum(prices[-20:]) / 20
            ma50 = sum(prices[-50:]) / 50 if len(prices) > 50 else ma20
            trend_strength = (ma20 - ma50) / ma50 if ma50 > 0 else 0
        
        # Classify market
        if volatility < 0.01:
            vol_class = 'low'
        elif volatility < 0.02:
            vol_class = 'medium'
        else:
            vol_class = 'high'
        
        if abs(trend_strength) < 0.02:
            trend_class = 'ranging'
        elif trend_strength > 0:
            trend_class = 'uptrend'
        else:
            trend_class = 'downtrend'
        
        return {
            'volatility': volatility,
            'volatility_class': vol_class,
            'trend_strength': trend_strength,
            'trend_class': trend_class
        }
    
    @staticmethod
    def recommend_parameters(market_analysis: Dict, trading_style: str = 'balanced') -> Dict:
        """Recommend parameters based on market analysis"""
        vol_class = market_analysis['volatility_class']
        trend_class = market_analysis['trend_class']
        
        # Base recommendations
        recommendations = {
            'scalping': {
                'length': 7,
                'order': 3,
                'adaptive_smooth': 3,
                'adaptive_mode': True
            },
            'day_trading': {
                'length': 15,
                'order': 4,
                'adaptive_smooth': 5,
                'adaptive_mode': True
            },
            'swing_trading': {
                'length': 30,
                'order': 4,
                'adaptive_smooth': 8,
                'adaptive_mode': True
            },
            'balanced': {
                'length': 20,
                'order': 4,
                'adaptive_smooth': 6,
                'adaptive_mode': True
            }
        }
        
        params = recommendations.get(trading_style, recommendations['balanced']).copy()
        
        # Adjust for market conditions
        if vol_class == 'high':
            params['length'] = int(params['length'] * 1.5)
            params['order'] = min(6, params['order'] + 1)
            params['adaptive_smooth'] = int(params['adaptive_smooth'] * 1.3)
        elif vol_class == 'low':
            params['length'] = int(params['length'] * 0.7)
            params['order'] = max(2, params['order'] - 1)
        
        if trend_class == 'ranging':
            params['length'] = int(params['length'] * 1.2)
            params['adaptive_mode'] = False
        
        return params


def demonstrate_optimization():
    """Demonstrate all optimization methods"""
    
    # Generate sample price data
    random.seed(42)
    prices = []
    price = 100
    for i in range(500):
        change = random.gauss(0, 1)
        trend = math.sin(i * 0.02) * 0.5
        price *= (1 + (change + trend) * 0.01)
        prices.append(price)
    
    print("="*60)
    print("ADAPTIVE LAGUERRE FILTER - PARAMETER OPTIMIZATION")
    print("="*60)
    
    # 1. Market Analysis
    print("\n1. MARKET ANALYSIS")
    print("-"*40)
    recommender = ParameterRecommender()
    market = recommender.analyze_market(prices)
    print(f"Volatility: {market['volatility']:.4f} ({market['volatility_class']})")
    print(f"Trend: {market['trend_strength']:.4f} ({market['trend_class']})")
    
    # 2. Parameter Recommendations
    print("\n2. RECOMMENDED PARAMETERS")
    print("-"*40)
    for style in ['scalping', 'day_trading', 'swing_trading']:
        params = recommender.recommend_parameters(market, style)
        print(f"\n{style.upper()}:")
        for key, value in params.items():
            print(f"  {key}: {value}")
    
    # 3. Grid Search Optimization
    print("\n3. GRID SEARCH OPTIMIZATION")
    print("-"*40)
    optimizer = SimpleOptimizer(prices, metric='return')
    param_grid = {
        'length': [10, 20, 30],
        'order': [3, 4, 5],
        'adaptive_smooth': [5, 7]
    }
    grid_result = optimizer.grid_search(param_grid)
    
    # 4. Random Search Optimization
    print("\n4. RANDOM SEARCH OPTIMIZATION")
    print("-"*40)
    optimizer2 = SimpleOptimizer(prices, metric='sharpe')
    param_ranges = {
        'length': (5, 50),
        'order': (2, 6),
        'adaptive_smooth': (3, 15)
    }
    random_result = optimizer2.random_search(param_ranges, n_iter=30)
    
    # 5. Comparison Table
    print("\n5. OPTIMIZATION COMPARISON")
    print("-"*40)
    print("Method          | Best Length | Best Order | Score")
    print("----------------|-------------|------------|--------")
    print(f"Grid Search     | {grid_result['params']['length']:11} | "
          f"{grid_result['params']['order']:10} | {grid_result['score']:6.2f}")
    print(f"Random Search   | {random_result['params']['length']:11} | "
          f"{random_result['params']['order']:10} | {random_result['score']:6.2f}")
    
    # 6. Save results
    results = {
        'market_analysis': market,
        'grid_search': grid_result,
        'random_search': random_result,
        'timestamp': datetime.now().isoformat()
    }
    
    with open('optimization_results_simple.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*60)
    print("Optimization complete! Results saved to optimization_results_simple.json")
    
    return results


if __name__ == "__main__":
    results = demonstrate_optimization()
    
    # Additional tips
    print("\nOPTIMIZATION TIPS:")
    print("-"*40)
    print("1. Start with recommended parameters for your trading style")
    print("2. Use grid search for thorough optimization (slower)")
    print("3. Use random search for quick exploration (faster)")
    print("4. Always validate on out-of-sample data")
    print("5. Re-optimize periodically as market conditions change")
    print("6. Consider multiple metrics (return, Sharpe, win rate)")
    print("7. Higher 'length' = smoother but more lag")
    print("8. Higher 'order' = more filtering but risk of overshoot")
    print("9. Adaptive mode works best in changing markets")
    print("10. Test parameters on at least 100 trades before using live")