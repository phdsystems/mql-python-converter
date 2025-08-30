"""
Unit tests for metrics adapter pattern implementation
"""

import unittest
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.metrics_adapter import (
    TradeResult, MetricFactory, SharpeRatioAdapter, TotalReturnAdapter,
    WinRateAdapter, ProfitFactorAdapter, MaxDrawdownAdapter,
    CalmarRatioAdapter, SortinoRatioAdapter, CompositeMetric
)


class TestTradeResult(unittest.TestCase):
    """Test TradeResult class"""
    
    def test_trade_result_return_calculation(self):
        """Test return percentage calculation"""
        trade = TradeResult(
            entry_price=100,
            exit_price=110,
            entry_time=0,
            exit_time=1
        )
        self.assertAlmostEqual(trade.return_pct, 10.0, places=2)
        
    def test_trade_result_profit_calculation(self):
        """Test profit calculation"""
        trade = TradeResult(
            entry_price=100,
            exit_price=110,
            entry_time=0,
            exit_time=1,
            position_size=2.0
        )
        self.assertAlmostEqual(trade.profit, 20.0, places=2)
    
    def test_negative_return(self):
        """Test negative return calculation"""
        trade = TradeResult(
            entry_price=100,
            exit_price=90,
            entry_time=0,
            exit_time=1
        )
        self.assertAlmostEqual(trade.return_pct, -10.0, places=2)


class TestMetricAdapters(unittest.TestCase):
    """Test individual metric adapters"""
    
    def setUp(self):
        """Create sample trades for testing"""
        self.winning_trades = [
            TradeResult(100, 110, 0, 1),  # +10%
            TradeResult(110, 121, 1, 2),  # +10%
            TradeResult(121, 127.05, 2, 3),  # +5%
        ]
        
        self.mixed_trades = [
            TradeResult(100, 110, 0, 1),  # +10%
            TradeResult(110, 99, 1, 2),   # -10%
            TradeResult(99, 108.9, 2, 3),  # +10%
            TradeResult(108.9, 104.544, 3, 4),  # -4%
        ]
        
        self.losing_trades = [
            TradeResult(100, 95, 0, 1),   # -5%
            TradeResult(95, 90.25, 1, 2),  # -5%
            TradeResult(90.25, 85.737, 2, 3),  # -5%
        ]
    
    def test_sharpe_ratio_adapter(self):
        """Test Sharpe Ratio calculation"""
        adapter = SharpeRatioAdapter(periods_per_year=252)
        
        # Test with winning trades
        sharpe = adapter.calculate(self.winning_trades)
        self.assertGreater(sharpe, 0)  # Should be positive
        
        # Test with mixed trades
        sharpe_mixed = adapter.calculate(self.mixed_trades)
        self.assertLess(abs(sharpe_mixed), abs(sharpe))  # Lower Sharpe for mixed
        
        # Test with no trades
        sharpe_empty = adapter.calculate([])
        self.assertEqual(sharpe_empty, -999.0)
    
    def test_total_return_adapter(self):
        """Test Total Return calculation"""
        adapter = TotalReturnAdapter()
        
        # Test winning trades: 10% + 10% + 5% = 25%
        total = adapter.calculate(self.winning_trades)
        self.assertAlmostEqual(total, 25.0, places=1)
        
        # Test mixed trades: 10% - 10% + 10% - 4% = 6%
        total_mixed = adapter.calculate(self.mixed_trades)
        self.assertAlmostEqual(total_mixed, 6.0, places=1)
        
        # Test losing trades: -5% - 5% - 5% = -15%
        total_losing = adapter.calculate(self.losing_trades)
        self.assertAlmostEqual(total_losing, -15.0, places=1)
    
    def test_win_rate_adapter(self):
        """Test Win Rate calculation"""
        adapter = WinRateAdapter()
        
        # All winning trades: 100%
        win_rate = adapter.calculate(self.winning_trades)
        self.assertAlmostEqual(win_rate, 100.0, places=1)
        
        # Mixed trades: 2 wins out of 4 = 50%
        win_rate_mixed = adapter.calculate(self.mixed_trades)
        self.assertAlmostEqual(win_rate_mixed, 50.0, places=1)
        
        # All losing trades: 0%
        win_rate_losing = adapter.calculate(self.losing_trades)
        self.assertAlmostEqual(win_rate_losing, 0.0, places=1)
    
    def test_profit_factor_adapter(self):
        """Test Profit Factor calculation"""
        adapter = ProfitFactorAdapter()
        
        # All winning trades: infinite (no losses)
        pf = adapter.calculate(self.winning_trades)
        self.assertEqual(pf, 999.0)  # Capped at 999
        
        # Mixed trades
        pf_mixed = adapter.calculate(self.mixed_trades)
        self.assertGreater(pf_mixed, 0)
        self.assertLess(pf_mixed, 999)
        
        # All losing trades: 0 (no profits)
        pf_losing = adapter.calculate(self.losing_trades)
        self.assertEqual(pf_losing, 0.0)
    
    def test_max_drawdown_adapter(self):
        """Test Maximum Drawdown calculation"""
        adapter = MaxDrawdownAdapter()
        
        # No drawdown with all winning trades
        dd = adapter.calculate(self.winning_trades)
        self.assertEqual(dd, 0.0)
        
        # Some drawdown with mixed trades
        dd_mixed = adapter.calculate(self.mixed_trades)
        self.assertGreater(dd_mixed, 0)
        
        # Continuous drawdown with losing trades
        dd_losing = adapter.calculate(self.losing_trades)
        self.assertGreater(dd_losing, 10)  # Should be around 14.3%
    
    def test_calmar_ratio_adapter(self):
        """Test Calmar Ratio calculation"""
        adapter = CalmarRatioAdapter(periods_per_year=252)
        
        # High Calmar with winning trades (no drawdown)
        calmar = adapter.calculate(self.winning_trades)
        self.assertEqual(calmar, 999.0)  # Capped due to zero drawdown
        
        # Lower Calmar with mixed trades
        calmar_mixed = adapter.calculate(self.mixed_trades)
        self.assertGreater(calmar_mixed, 0)
        self.assertLess(calmar_mixed, 999)
    
    def test_sortino_ratio_adapter(self):
        """Test Sortino Ratio calculation"""
        adapter = SortinoRatioAdapter(target_return=0.0, periods_per_year=252)
        
        # High Sortino with winning trades (no downside)
        sortino = adapter.calculate(self.winning_trades)
        self.assertEqual(sortino, 999.0)  # No downside deviation
        
        # Lower Sortino with mixed trades
        sortino_mixed = adapter.calculate(self.mixed_trades)
        self.assertNotEqual(sortino_mixed, 999.0)
        
        # Negative Sortino with losing trades
        sortino_losing = adapter.calculate(self.losing_trades)
        self.assertLess(sortino_losing, 0)


class TestMetricFactory(unittest.TestCase):
    """Test MetricFactory functionality"""
    
    def test_create_metric(self):
        """Test creating metrics by name"""
        metric = MetricFactory.create('sharpe_ratio')
        self.assertIsInstance(metric, SharpeRatioAdapter)
        
        metric = MetricFactory.create('total_return')
        self.assertIsInstance(metric, TotalReturnAdapter)
    
    def test_list_available_metrics(self):
        """Test listing available metrics"""
        metrics = MetricFactory.list_available()
        self.assertIn('sharpe_ratio', metrics)
        self.assertIn('total_return', metrics)
        self.assertIn('win_rate', metrics)
        self.assertIn('profit_factor', metrics)
        self.assertIn('max_drawdown', metrics)
    
    def test_invalid_metric(self):
        """Test creating invalid metric raises error"""
        with self.assertRaises(ValueError):
            MetricFactory.create('invalid_metric')
    
    def test_metric_properties(self):
        """Test metric properties"""
        sharpe = MetricFactory.create('sharpe_ratio')
        self.assertEqual(sharpe.get_name(), 'sharpe_ratio')
        self.assertTrue(sharpe.is_higher_better())
        
        drawdown = MetricFactory.create('max_drawdown')
        self.assertEqual(drawdown.get_name(), 'max_drawdown')
        self.assertFalse(drawdown.is_higher_better())


class TestCompositeMetric(unittest.TestCase):
    """Test CompositeMetric functionality"""
    
    def setUp(self):
        """Create sample trades"""
        self.trades = [
            TradeResult(100, 110, 0, 1),
            TradeResult(110, 105, 1, 2),
            TradeResult(105, 115, 2, 3),
        ]
    
    def test_composite_metric_equal_weights(self):
        """Test composite metric with equal weights"""
        composite = CompositeMetric({
            'sharpe_ratio': 1.0,
            'win_rate': 1.0
        }, normalize=True)
        
        score = composite.calculate(self.trades)
        self.assertIsInstance(score, float)
        
        # Each metric should contribute 50%
        self.assertEqual(len(composite.metrics), 2)
    
    def test_composite_metric_custom_weights(self):
        """Test composite metric with custom weights"""
        composite = CompositeMetric({
            'sharpe_ratio': 3.0,
            'total_return': 1.0,
            'max_drawdown': 1.0
        }, normalize=True)
        
        score = composite.calculate(self.trades)
        self.assertIsInstance(score, float)
        
        # Sharpe should have 60% weight (3/5)
        sharpe_weight = None
        for adapter, weight in composite.metrics.items():
            if adapter.get_name() == 'sharpe_ratio':
                sharpe_weight = weight
                break
        self.assertAlmostEqual(sharpe_weight, 0.6, places=1)
    
    def test_composite_metric_description(self):
        """Test composite metric description"""
        composite = CompositeMetric({
            'sharpe_ratio': 1.0,
            'win_rate': 1.0
        })
        
        description = composite.get_description()
        self.assertIn('sharpe_ratio', description)
        self.assertIn('win_rate', description)


class TestMetricConsistency(unittest.TestCase):
    """Test consistency and edge cases across metrics"""
    
    def test_single_trade(self):
        """Test metrics with single trade"""
        trades = [TradeResult(100, 110, 0, 1)]
        
        for metric_name in MetricFactory.list_available():
            metric = MetricFactory.create(metric_name)
            score = metric.calculate(trades)
            self.assertIsInstance(score, float)
            self.assertNotEqual(score, float('inf'))
            self.assertNotEqual(score, float('-inf'))
    
    def test_zero_return_trades(self):
        """Test metrics with zero-return trades"""
        trades = [
            TradeResult(100, 100, 0, 1),
            TradeResult(100, 100, 1, 2),
        ]
        
        for metric_name in MetricFactory.list_available():
            metric = MetricFactory.create(metric_name)
            score = metric.calculate(trades)
            self.assertIsInstance(score, float)
    
    def test_large_number_trades(self):
        """Test metrics with many trades"""
        np.random.seed(42)
        trades = []
        
        for i in range(1000):
            entry = 100
            exit = entry * (1 + np.random.randn() * 0.02)
            trades.append(TradeResult(entry, exit, i, i+1))
        
        for metric_name in MetricFactory.list_available():
            metric = MetricFactory.create(metric_name)
            score = metric.calculate(trades)
            self.assertIsInstance(score, float)
            self.assertFalse(np.isnan(score))


def run_tests():
    """Run all tests with summary"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()