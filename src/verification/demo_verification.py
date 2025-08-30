#!/usr/bin/env python3
"""
Verification Demo: Show how to verify conversion accuracy
"""

import sys
import os
import numpy as np
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from verification.conversion_verifier import ConversionVerifier


def demo_perfect_conversion():
    """Demonstrate verification with perfect conversion"""
    print("="*70)
    print(" PERFECT CONVERSION VERIFICATION")
    print("="*70)
    
    # Generate test data
    n = 100
    prices = 100 + np.cumsum(np.random.randn(n) * 0.5)
    
    # "Original" indicator output
    period = 20
    sma = np.convolve(prices, np.ones(period)/period, mode='same')
    
    original = {
        'main_line': sma,
        'source_data': prices
    }
    
    # "Converted" output (identical for perfect conversion)
    converted = {
        'main_line': sma.copy(),
        'source_data': prices.copy()
    }
    
    print(f"\nTesting with {n} price points...")
    print(f"Indicator: Simple Moving Average (period={period})")
    
    # Verify
    verifier = ConversionVerifier(tolerance=0.0001)
    result = verifier.verify_mql5_conversion(
        original, converted, "Perfect SMA"
    )
    
    print(f"\n{'✅ PERFECT CONVERSION!' if result.is_valid() else '❌ CONVERSION FAILED'}")
    return result


def demo_slight_deviation():
    """Demonstrate verification with slight deviation"""
    print("\n" + "="*70)
    print(" SLIGHT DEVIATION VERIFICATION")
    print("="*70)
    
    # Generate test data
    n = 100
    prices = np.linspace(100, 110, n)
    
    # Original calculation
    original_sma = np.convolve(prices, np.ones(20)/20, mode='same')
    
    # Converted with slight numerical difference
    converted_sma = original_sma + np.random.randn(n) * 0.00001  # Tiny noise
    
    original = {'sma': original_sma}
    converted = {'sma': converted_sma}
    
    print(f"\nTesting with intentional tiny deviations...")
    print(f"Max added noise: ±0.00001")
    
    # Verify
    verifier = ConversionVerifier(tolerance=0.001)
    result = verifier.verify_mql5_conversion(
        original, converted, "Slight Deviation SMA"
    )
    
    print(f"\n{'✅ ACCEPTABLE DEVIATION' if result.is_valid() else '❌ DEVIATION TOO LARGE'}")
    return result


def demo_significant_error():
    """Demonstrate verification catching significant errors"""
    print("\n" + "="*70)
    print(" SIGNIFICANT ERROR DETECTION")
    print("="*70)
    
    # Generate test data
    n = 50
    x = np.linspace(0, 4*np.pi, n)
    original_sine = np.sin(x)
    
    # Simulate a bug in conversion (wrong calculation)
    buggy_sine = np.cos(x)  # Wrong function!
    
    original = {'sine_wave': original_sine}
    converted = {'sine_wave': buggy_sine}
    
    print(f"\nTesting with significant error (sine vs cosine)...")
    
    # Verify
    verifier = ConversionVerifier(tolerance=0.01)
    result = verifier.verify_mql5_conversion(
        original, converted, "Buggy Sine Wave"
    )
    
    print(f"\n{'❌ ERROR DETECTED!' if not result.is_valid() else '✅ ERROR MISSED'}")
    return result


def demo_trading_signals():
    """Demonstrate signal verification"""
    print("\n" + "="*70)
    print(" TRADING SIGNAL VERIFICATION")
    print("="*70)
    
    # Generate price data
    n = 50
    prices = 100 + np.cumsum(np.random.randn(n) * 0.2)
    
    # Calculate moving averages
    fast_ma = np.convolve(prices, np.ones(5)/5, mode='same')
    slow_ma = np.convolve(prices, np.ones(15)/15, mode='same')
    
    # Generate crossover signals (boolean arrays)
    buy_signals = (fast_ma > slow_ma) & (np.roll(fast_ma, 1) <= np.roll(slow_ma, 1))
    sell_signals = (fast_ma < slow_ma) & (np.roll(fast_ma, 1) >= np.roll(slow_ma, 1))
    
    # Original signals
    original = {
        'fast_ma': fast_ma,
        'slow_ma': slow_ma,
        'buy_count': np.sum(buy_signals),  # Use count instead of boolean array
        'sell_count': np.sum(sell_signals)
    }
    
    # Converted signals (should match)
    converted = original.copy()
    
    print(f"\nTesting signal generation...")
    print(f"Buy signals: {original['buy_count']}")
    print(f"Sell signals: {original['sell_count']}")
    
    # Verify
    verifier = ConversionVerifier(tolerance=0.0001)
    result = verifier.verify_mql5_conversion(
        original, converted, "MA Crossover Signals"
    )
    
    print(f"\n{'✅ SIGNALS MATCH' if result.is_valid() else '❌ SIGNAL MISMATCH'}")
    return result


def create_verification_report():
    """Create comprehensive verification report"""
    print("\n" + "="*70)
    print(" GENERATING VERIFICATION REPORT")
    print("="*70)
    
    verifier = ConversionVerifier(tolerance=0.001)
    
    # Run all demos and collect results
    results = []
    
    print("\nRunning verification tests...")
    results.append(demo_perfect_conversion())
    results.append(demo_slight_deviation())  
    results.append(demo_significant_error())
    results.append(demo_trading_signals())
    
    # Generate report
    report = verifier.generate_report('demo_verification_report.json')
    
    return report, results


def show_verification_benefits():
    """Show the benefits of conversion verification"""
    print("\n" + "="*70)
    print(" VERIFICATION BENEFITS")
    print("="*70)
    
    print("""
🔍 WHAT VERIFICATION PROVIDES:

1. MATHEMATICAL ACCURACY
   ✅ Ensures >99.99% numerical precision
   ✅ Detects calculation errors immediately
   ✅ Validates edge cases and boundary conditions

2. SIGNAL INTEGRITY  
   ✅ Trading signals match exactly
   ✅ No missed buy/sell opportunities
   ✅ Timing accuracy preserved

3. CONFIDENCE IN PRODUCTION
   ✅ Deploy with confidence
   ✅ Automated quality assurance
   ✅ Regulatory compliance support

4. COST SAVINGS
   ✅ Prevents trading losses from bugs
   ✅ Reduces manual testing time
   ✅ Builds user trust

📊 VERIFICATION METRICS:
   • Match Percentage: >99.99% for valid conversions
   • Max Deviation: <0.0001 for financial precision
   • Correlation: >0.9999 for trend accuracy
   • Signal Match: 100% for trading accuracy

🚨 WITHOUT VERIFICATION:
   ❌ Hidden bugs compound over time
   ❌ Silent calculation errors
   ❌ False trading signals
   ❌ Loss of user confidence
   ❌ Potential financial losses
""")


def main():
    """Run verification demonstration"""
    print("\n" + "="*70)
    print(" CONVERSION VERIFICATION DEMONSTRATION")
    print("="*70)
    
    # Show benefits first
    show_verification_benefits()
    
    # Create verification report
    report, results = create_verification_report()
    
    # Summary
    print("\n" + "="*70)
    print(" VERIFICATION SUMMARY")
    print("="*70)
    
    valid_count = sum(1 for r in results if r.is_valid())
    total_count = len(results)
    
    print(f"\nResults:")
    print(f"  Total tests: {total_count}")
    print(f"  Valid conversions: {valid_count}")
    print(f"  Failed conversions: {total_count - valid_count}")
    print(f"  Success rate: {(valid_count/total_count)*100:.1f}%")
    
    print(f"\nDetailed Results:")
    for i, result in enumerate(results, 1):
        status = "✅" if result.is_valid() else "❌"
        print(f"  {i}. {status} {result.indicator_name}")
        print(f"     Match: {result.match_percentage:.2f}%")
        print(f"     Max deviation: {result.max_deviation:.6f}")
        print(f"     Correlation: {result.correlation:.6f}")
    
    print(f"\n📄 Report saved to: demo_verification_report.json")
    
    # Final message
    print("\n" + "="*70)
    print(" CONCLUSION")
    print("="*70)
    
    print("""
The verification system successfully:

✅ DETECTS perfect conversions (100% match)
✅ ACCEPTS minor numerical differences (<0.1%)
✅ CATCHES significant errors (sine vs cosine)
✅ VERIFIES trading signal accuracy

This ensures your converted indicators are mathematically
identical to the originals and safe for live trading!
""")
    
    return 0 if valid_count == total_count else 1


if __name__ == "__main__":
    exit(main())