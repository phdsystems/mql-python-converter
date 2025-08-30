"""
Conversion Verification Framework
Verifies that converted Python code produces the same results as original MQL5/Pine Script
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json
import os


@dataclass
class VerificationResult:
    """Result of verification between original and converted code"""
    indicator_name: str
    source_platform: str  # 'MQL5' or 'PineScript'
    match_percentage: float
    max_deviation: float
    mean_deviation: float
    correlation: float
    signals_match: bool
    details: Dict[str, Any]
    
    def is_valid(self, tolerance: float = 0.0001) -> bool:
        """Check if conversion is valid within tolerance"""
        return (
            self.match_percentage > 99.99 and
            self.max_deviation < tolerance and
            self.correlation > 0.9999
        )


class ConversionVerifier:
    """Verifies conversion accuracy between platforms"""
    
    def __init__(self, tolerance: float = 0.0001):
        """
        Initialize verifier
        
        Args:
            tolerance: Maximum acceptable deviation (default 0.01%)
        """
        self.tolerance = tolerance
        self.results = []
        
    def verify_mql5_conversion(self,
                              mql5_values: Dict[str, np.ndarray],
                              python_values: Dict[str, np.ndarray],
                              indicator_name: str) -> VerificationResult:
        """
        Verify MQL5 to Python conversion
        
        Args:
            mql5_values: Original MQL5 indicator values
            python_values: Converted Python indicator values
            indicator_name: Name of the indicator
            
        Returns:
            VerificationResult object
        """
        print(f"\nVerifying MQL5 → Python: {indicator_name}")
        print("-" * 50)
        
        # Find common keys
        common_keys = set(mql5_values.keys()) & set(python_values.keys())
        if not common_keys:
            print("  ❌ No common output keys found!")
            return VerificationResult(
                indicator_name=indicator_name,
                source_platform='MQL5',
                match_percentage=0,
                max_deviation=float('inf'),
                mean_deviation=float('inf'),
                correlation=0,
                signals_match=False,
                details={'error': 'No common keys'}
            )
        
        results = {}
        overall_match = []
        max_dev = 0
        mean_dev = 0
        
        for key in common_keys:
            mql5_data = np.array(mql5_values[key])
            python_data = np.array(python_values[key])
            
            # Ensure same length
            min_len = min(len(mql5_data), len(python_data))
            mql5_data = mql5_data[:min_len]
            python_data = python_data[:min_len]
            
            # Calculate metrics
            deviation = np.abs(mql5_data - python_data)
            max_deviation = np.max(deviation)
            mean_deviation = np.mean(deviation)
            
            # Calculate correlation
            if len(mql5_data) > 1:
                correlation = np.corrcoef(mql5_data, python_data)[0, 1]
            else:
                correlation = 1.0 if max_deviation < self.tolerance else 0.0
            
            # Calculate match percentage
            matches = deviation < self.tolerance
            match_pct = (np.sum(matches) / len(matches)) * 100
            
            results[key] = {
                'match_percentage': match_pct,
                'max_deviation': max_deviation,
                'mean_deviation': mean_deviation,
                'correlation': correlation,
                'num_values': len(mql5_data)
            }
            
            overall_match.extend(matches)
            max_dev = max(max_dev, max_deviation)
            mean_dev += mean_deviation
            
            print(f"  {key}:")
            print(f"    Match: {match_pct:.2f}%")
            print(f"    Max deviation: {max_deviation:.6f}")
            print(f"    Correlation: {correlation:.6f}")
        
        # Overall metrics
        overall_match_pct = (np.sum(overall_match) / len(overall_match)) * 100
        mean_dev = mean_dev / len(common_keys)
        
        # Check signal accuracy (for trend/buy/sell signals)
        signals_match = self._verify_signals(mql5_values, python_values)
        
        result = VerificationResult(
            indicator_name=indicator_name,
            source_platform='MQL5',
            match_percentage=overall_match_pct,
            max_deviation=max_dev,
            mean_deviation=mean_dev,
            correlation=min(r['correlation'] for r in results.values()),
            signals_match=signals_match,
            details=results
        )
        
        # Print summary
        if result.is_valid(self.tolerance):
            print(f"\n✅ VALID: {overall_match_pct:.2f}% match, max deviation {max_dev:.6f}")
        else:
            print(f"\n❌ INVALID: Only {overall_match_pct:.2f}% match, max deviation {max_dev:.6f}")
        
        self.results.append(result)
        return result
    
    def verify_pinescript_conversion(self,
                                   pine_values: Dict[str, np.ndarray],
                                   python_values: Dict[str, np.ndarray],
                                   indicator_name: str) -> VerificationResult:
        """
        Verify Pine Script to Python conversion
        
        Args:
            pine_values: Original Pine Script indicator values
            python_values: Converted Python indicator values
            indicator_name: Name of the indicator
            
        Returns:
            VerificationResult object
        """
        print(f"\nVerifying Pine Script → Python: {indicator_name}")
        print("-" * 50)
        
        # Pine Script verification uses same logic as MQL5
        # but we adjust for Pine Script specific quirks
        
        # Handle Pine Script's different naming conventions
        pine_normalized = self._normalize_pine_keys(pine_values)
        
        # Use the MQL5 verification logic
        return self.verify_mql5_conversion(
            pine_normalized,
            python_values,
            indicator_name
        )
    
    def _normalize_pine_keys(self, pine_values: Dict) -> Dict:
        """Normalize Pine Script output keys to match Python conventions"""
        normalized = {}
        
        key_mapping = {
            'plot1': 'main',
            'plot2': 'signal',
            'hline1': 'upper',
            'hline2': 'lower',
            # Add more mappings as needed
        }
        
        for key, value in pine_values.items():
            new_key = key_mapping.get(key, key)
            normalized[new_key] = value
        
        return normalized
    
    def _verify_signals(self, 
                       original: Dict[str, np.ndarray],
                       converted: Dict[str, np.ndarray]) -> bool:
        """Verify that trading signals match"""
        # Check for signal keys
        signal_keys = ['buy', 'sell', 'trend', 'signal', 'crossover', 'crossunder']
        
        for key in signal_keys:
            if key in original and key in converted:
                orig_signals = original[key]
                conv_signals = converted[key]
                
                # For boolean signals
                if orig_signals.dtype == bool or conv_signals.dtype == bool:
                    if not np.array_equal(orig_signals, conv_signals):
                        return False
                
                # For numeric signals (1, -1, 0)
                else:
                    if not np.allclose(orig_signals, conv_signals, rtol=1e-5):
                        return False
        
        return True
    
    def generate_report(self, output_file: str = 'verification_report.json'):
        """Generate verification report"""
        report = {
            'summary': {
                'total_indicators': len(self.results),
                'valid_conversions': sum(1 for r in self.results if r.is_valid(self.tolerance)),
                'average_match': np.mean([r.match_percentage for r in self.results]),
                'tolerance_used': self.tolerance
            },
            'indicators': []
        }
        
        for result in self.results:
            report['indicators'].append({
                'name': result.indicator_name,
                'platform': result.source_platform,
                'match_percentage': result.match_percentage,
                'max_deviation': result.max_deviation,
                'mean_deviation': result.mean_deviation,
                'correlation': result.correlation,
                'signals_match': result.signals_match,
                'valid': result.is_valid(self.tolerance),
                'details': result.details
            })
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Report saved to {output_file}")
        return report


class TestDataGenerator:
    """Generate test data for verification"""
    
    @staticmethod
    def generate_price_data(n: int = 1000, seed: int = 42) -> Dict[str, np.ndarray]:
        """Generate realistic OHLCV price data"""
        np.random.seed(seed)
        
        # Generate realistic price movement
        returns = np.random.randn(n) * 0.01
        close = 100 * np.exp(np.cumsum(returns))
        
        # Generate OHLCV
        high = close * (1 + np.abs(np.random.randn(n) * 0.005))
        low = close * (1 - np.abs(np.random.randn(n) * 0.005))
        open_price = np.roll(close, 1)
        open_price[0] = close[0]
        volume = np.random.randint(1000, 10000, n)
        
        return {
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }
    
    @staticmethod
    def simulate_mql5_output(prices: Dict, indicator_type: str) -> Dict[str, np.ndarray]:
        """Simulate MQL5 indicator output for testing"""
        close = prices['close']
        
        if indicator_type == 'sma':
            # Simple moving average
            period = 20
            sma = np.convolve(close, np.ones(period)/period, mode='same')
            return {'main': sma}
        
        elif indicator_type == 'laguerre':
            # Simplified Laguerre filter
            gamma = 0.5
            laguerre = np.zeros_like(close)
            laguerre[0] = close[0]
            
            for i in range(1, len(close)):
                laguerre[i] = (1 - gamma) * close[i] + gamma * laguerre[i-1]
            
            # Add trend
            trend = np.zeros_like(close)
            for i in range(1, len(close)):
                if laguerre[i] > laguerre[i-1]:
                    trend[i] = 1
                elif laguerre[i] < laguerre[i-1]:
                    trend[i] = -1
                else:
                    trend[i] = trend[i-1]
            
            return {
                'laguerre': laguerre,
                'trend': trend,
                'gamma': np.full_like(close, gamma)
            }
        
        elif indicator_type == 'rsi':
            # RSI calculation
            period = 14
            delta = np.diff(close, prepend=close[0])
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            
            # RMA calculation
            avg_gain = np.zeros_like(gain)
            avg_loss = np.zeros_like(loss)
            avg_gain[period] = np.mean(gain[:period])
            avg_loss[period] = np.mean(loss[:period])
            
            for i in range(period + 1, len(gain)):
                avg_gain[i] = (avg_gain[i-1] * (period - 1) + gain[i]) / period
                avg_loss[i] = (avg_loss[i-1] * (period - 1) + loss[i]) / period
            
            rs = avg_gain / (avg_loss + 1e-10)
            rsi = 100 - (100 / (1 + rs))
            
            return {'rsi': rsi}
        
        return {}
    
    @staticmethod
    def simulate_pinescript_output(prices: Dict, indicator_type: str) -> Dict[str, np.ndarray]:
        """Simulate Pine Script indicator output for testing"""
        # Pine Script would produce similar outputs
        # We use the same calculations but might have slightly different keys
        mql5_output = TestDataGenerator.simulate_mql5_output(prices, indicator_type)
        
        # Rename keys to Pine Script style
        if indicator_type == 'sma':
            return {'plot1': mql5_output['main']}
        elif indicator_type == 'rsi':
            return {'rsi_value': mql5_output['rsi']}
        
        return mql5_output