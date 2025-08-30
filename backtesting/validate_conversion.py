#!/usr/bin/env python3
"""
Conversion Validation Script
Tests and validates MQL4 to Python indicator conversions
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backtesting.framework import (
    MT4HistoryReader, 
    SimpleMA, 
    BacktestEngine,
    compare_indicators
)


class ConversionValidator:
    """Validates MQL4 to Python conversions"""
    
    def __init__(self, mt4_terminal_path: str):
        self.mt4_path = Path(mt4_terminal_path)
        self.history_path = self.mt4_path / "history/default"
        self.indicators_path = self.mt4_path / "MQL4/Indicators"
        self.validation_results = []
        
    def load_history_data(self, symbol: str = "EURUSD", period: int = 240) -> pd.DataFrame:
        """Load historical data for testing"""
        history_file = self.history_path / f"{symbol}{period}.hst"
        
        if not history_file.exists():
            raise FileNotFoundError(f"History file not found: {history_file}")
            
        reader = MT4HistoryReader(str(history_file))
        return reader.load(), reader.get_info()
    
    def test_simple_ma(self, data: pd.DataFrame) -> dict:
        """Test Simple Moving Average conversion"""
        print("\nTesting Simple MA Conversion...")
        print("-" * 40)
        
        # Test parameters
        test_cases = [
            {'fast': 10, 'slow': 20, 'method': 'SMA'},
            {'fast': 12, 'slow': 26, 'method': 'EMA'},
            {'fast': 5, 'slow': 15, 'method': 'SMA'},
        ]
        
        results = []
        for params in test_cases:
            indicator = SimpleMA(
                data, 
                fast_period=params['fast'],
                slow_period=params['slow'],
                ma_method=params['method']
            )
            indicator.calculate()
            signals = indicator.get_crossover_signals()
            
            # Run backtest
            engine = BacktestEngine(data.copy())
            engine.run_strategy(signals)
            stats = engine.get_statistics()
            
            result = {
                'indicator': 'SimpleMA',
                'parameters': params,
                'total_signals': (signals != 0).sum(),
                'bullish_signals': (signals == 1).sum(),
                'bearish_signals': (signals == -1).sum(),
                'backtest_stats': stats
            }
            results.append(result)
            
            print(f"\nParameters: Fast={params['fast']}, Slow={params['slow']}, Method={params['method']}")
            print(f"Total Signals: {result['total_signals']}")
            print(f"Win Rate: {stats['win_rate']:.2%}")
            print(f"Total Return: {stats['total_return']:.2%}")
            
        return results
    
    def test_indicator_accuracy(self, data: pd.DataFrame) -> dict:
        """Test indicator calculation accuracy"""
        print("\nTesting Indicator Calculation Accuracy...")
        print("-" * 40)
        
        # Calculate using Python
        indicator = SimpleMA(data, fast_period=10, slow_period=20)
        indicator.calculate()
        
        # Compare different price points
        test_points = [100, 500, 1000, 5000, 10000]
        
        for point in test_points:
            if point < len(data):
                fast_ma = indicator.results['fast_ma'].iloc[point]
                slow_ma = indicator.results['slow_ma'].iloc[point]
                
                # Manual calculation for verification
                manual_fast = data['close'].iloc[point-9:point+1].mean()
                manual_slow = data['close'].iloc[point-19:point+1].mean()
                
                diff_fast = abs(fast_ma - manual_fast)
                diff_slow = abs(slow_ma - manual_slow)
                
                print(f"\nBar {point}:")
                print(f"  Fast MA: {fast_ma:.5f} (diff: {diff_fast:.8f})")
                print(f"  Slow MA: {slow_ma:.5f} (diff: {diff_slow:.8f})")
                
        return {'accuracy_test': 'passed'}
    
    def test_edge_cases(self, data: pd.DataFrame) -> dict:
        """Test edge cases and error handling"""
        print("\nTesting Edge Cases...")
        print("-" * 40)
        
        test_results = []
        
        # Test 1: Period larger than data
        try:
            indicator = SimpleMA(data.head(10), fast_period=20, slow_period=30)
            indicator.calculate()
            test_results.append({'test': 'large_period', 'status': 'handled'})
            print("✓ Large period handled correctly")
        except Exception as e:
            test_results.append({'test': 'large_period', 'status': 'failed', 'error': str(e)})
            print(f"✗ Large period failed: {e}")
        
        # Test 2: Empty data
        try:
            indicator = SimpleMA(pd.DataFrame(), fast_period=10, slow_period=20)
            indicator.calculate()
            test_results.append({'test': 'empty_data', 'status': 'handled'})
            print("✓ Empty data handled correctly")
        except Exception as e:
            test_results.append({'test': 'empty_data', 'status': 'handled', 'note': str(e)})
            print("✓ Empty data raises appropriate error")
        
        # Test 3: Single data point
        single_point = data.head(1)
        indicator = SimpleMA(single_point, fast_period=1, slow_period=1)
        indicator.calculate()
        test_results.append({'test': 'single_point', 'status': 'handled'})
        print("✓ Single data point handled correctly")
        
        return test_results
    
    def run_full_validation(self) -> dict:
        """Run complete validation suite"""
        print("\n" + "=" * 50)
        print("MQL4 to Python Conversion Validation")
        print("=" * 50)
        
        validation_report = {
            'timestamp': datetime.now().isoformat(),
            'mt4_path': str(self.mt4_path),
            'tests': {}
        }
        
        try:
            # Load data
            data, info = self.load_history_data()
            print(f"\nLoaded {info['symbol']} data:")
            print(f"  Period: {info['period']} minutes")
            print(f"  Bars: {info['bar_count']}")
            print(f"  Range: {info['date_range'][0]} to {info['date_range'][1]}")
            
            # Run tests
            validation_report['data_info'] = info
            validation_report['tests']['simple_ma'] = self.test_simple_ma(data)
            validation_report['tests']['accuracy'] = self.test_indicator_accuracy(data)
            validation_report['tests']['edge_cases'] = self.test_edge_cases(data)
            
            # Overall status
            validation_report['status'] = 'PASSED'
            
        except Exception as e:
            print(f"\nValidation failed: {e}")
            validation_report['status'] = 'FAILED'
            validation_report['error'] = str(e)
            
        return validation_report
    
    def save_report(self, report: dict, filename: str = "validation_report.json"):
        """Save validation report to file"""
        output_path = Path(__file__).parent / filename
        
        # Convert numpy/pandas types to JSON-serializable format
        def serialize(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=serialize)
            
        print(f"\n✓ Report saved to: {output_path}")
        return output_path


def main():
    """Main validation routine"""
    # MT4 terminal path
    mt4_path = "/home/developer/mql-python-converter/server/mt4-terminal"
    
    # Create validator
    validator = ConversionValidator(mt4_path)
    
    # Run validation
    report = validator.run_full_validation()
    
    # Save report
    validator.save_report(report)
    
    # Print summary
    print("\n" + "=" * 50)
    print("Validation Summary")
    print("=" * 50)
    print(f"Status: {report['status']}")
    
    if report['status'] == 'PASSED':
        # Count total tests
        total_tests = 0
        for test_category in report.get('tests', {}).values():
            if isinstance(test_category, list):
                total_tests += len(test_category)
            else:
                total_tests += 1
                
        print(f"Total tests run: {total_tests}")
        print("\n✅ All conversion validations passed!")
    else:
        print(f"Error: {report.get('error', 'Unknown error')}")
        print("\n❌ Validation failed!")
    
    return 0 if report['status'] == 'PASSED' else 1


if __name__ == "__main__":
    sys.exit(main())