#!/usr/bin/env python3
"""
Generate synthetic forex data for testing
Since MT4 history files are corrupted, this creates realistic test data
"""

import struct
import random
from datetime import datetime, timedelta
from pathlib import Path
import math


def generate_forex_prices(symbol="EURUSD", start_price=1.1000, days=365, timeframe=240):
    """
    Generate realistic forex price data
    
    Args:
        symbol: Currency pair
        start_price: Starting price
        days: Number of days to generate
        timeframe: Timeframe in minutes (240 = 4 hours)
    
    Returns:
        List of OHLCV bars
    """
    bars = []
    current_price = start_price
    
    # Calculate number of bars
    bars_per_day = 1440 // timeframe  # 1440 minutes in a day
    total_bars = days * bars_per_day
    
    # Start date
    start_date = datetime(2020, 1, 1)
    
    for i in range(total_bars):
        # Calculate timestamp
        timestamp = start_date + timedelta(minutes=i * timeframe)
        
        # Generate price movement
        # Daily volatility for forex is typically 0.5-1.5%
        daily_volatility = 0.01
        bar_volatility = daily_volatility / math.sqrt(bars_per_day)
        
        # Random walk with slight trend
        trend = 0.00001 * math.sin(i / 100)  # Slight sinusoidal trend
        change = random.gauss(trend, bar_volatility)
        
        # Calculate OHLC
        open_price = current_price
        close_price = current_price * (1 + change)
        
        # High and Low with realistic wicks
        wick_size = abs(change) * random.uniform(0.3, 1.5)
        high_price = max(open_price, close_price) + current_price * wick_size
        low_price = min(open_price, close_price) - current_price * wick_size
        
        # Volume (random, typical forex volume)
        volume = random.randint(100, 10000)
        
        # Create bar
        bar = {
            'time': timestamp,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        }
        
        bars.append(bar)
        current_price = close_price
    
    return bars


def write_mt4_history(bars, filepath, symbol="EURUSD", digits=5, period=240):
    """
    Write bars to MT4 .hst format
    
    Args:
        bars: List of price bars
        filepath: Output file path
        symbol: Currency pair symbol
        digits: Number of decimal digits
        period: Timeframe in minutes
    """
    with open(filepath, 'wb') as f:
        # Write header (148 bytes)
        # Version
        f.write(struct.pack('<I', 401))
        
        # Copyright (64 bytes)
        copyright_text = "Generated Test Data".encode('ascii')
        f.write(copyright_text.ljust(64, b'\x00'))
        
        # Symbol (12 bytes)
        f.write(symbol.encode('ascii').ljust(12, b'\x00'))
        
        # Period
        f.write(struct.pack('<I', period))
        
        # Digits
        f.write(struct.pack('<I', digits))
        
        # Timesign
        f.write(struct.pack('<I', 0))
        
        # Last sync
        f.write(struct.pack('<I', 0))
        
        # Unused (52 bytes)
        f.write(b'\x00' * 52)
        
        # Write bars (60 bytes each)
        for bar in bars:
            # Time (4 bytes)
            timestamp = int(bar['time'].timestamp())
            f.write(struct.pack('<I', timestamp))
            
            # Padding (4 bytes)
            f.write(struct.pack('<I', 0))
            
            # Open (8 bytes)
            f.write(struct.pack('<d', bar['open']))
            
            # High (8 bytes)
            f.write(struct.pack('<d', bar['high']))
            
            # Low (8 bytes)
            f.write(struct.pack('<d', bar['low']))
            
            # Close (8 bytes)
            f.write(struct.pack('<d', bar['close']))
            
            # Volume (8 bytes)
            f.write(struct.pack('<Q', bar['volume']))
            
            # Spread (4 bytes)
            f.write(struct.pack('<I', 2))  # 2 pips spread
            
            # Real volume (8 bytes)
            f.write(struct.pack('<Q', bar['volume']))
    
    print(f"Written {len(bars)} bars to {filepath}")


def write_csv(bars, filepath):
    """
    Write bars to CSV format for easy inspection
    
    Args:
        bars: List of price bars
        filepath: Output CSV file path
    """
    with open(filepath, 'w') as f:
        # Write header
        f.write("Date,Time,Open,High,Low,Close,Volume\n")
        
        # Write bars
        for bar in bars:
            date_str = bar['time'].strftime('%Y.%m.%d')
            time_str = bar['time'].strftime('%H:%M')
            f.write(f"{date_str},{time_str},{bar['open']:.5f},{bar['high']:.5f},"
                   f"{bar['low']:.5f},{bar['close']:.5f},{bar['volume']}\n")
    
    print(f"Written {len(bars)} bars to {filepath}")


def main():
    """Generate test data files"""
    print("Generating Synthetic Forex Data")
    print("=" * 50)
    
    output_dir = Path("/home/developer/mql-python-converter/backtesting/test_data")
    output_dir.mkdir(exist_ok=True)
    
    # Generate data for different pairs
    test_configs = [
        {"symbol": "EURUSD", "start_price": 1.1000, "digits": 5},
        {"symbol": "GBPUSD", "start_price": 1.3000, "digits": 5},
        {"symbol": "USDJPY", "start_price": 110.00, "digits": 3},
        {"symbol": "GBPJPY", "start_price": 143.00, "digits": 3},
    ]
    
    for config in test_configs:
        print(f"\nGenerating {config['symbol']} data...")
        
        # Generate bars
        bars = generate_forex_prices(
            symbol=config['symbol'],
            start_price=config['start_price'],
            days=365,
            timeframe=240
        )
        
        # Write MT4 format
        hst_file = output_dir / f"{config['symbol']}240.hst"
        write_mt4_history(
            bars, 
            hst_file,
            symbol=config['symbol'],
            digits=config['digits'],
            period=240
        )
        
        # Write CSV format
        csv_file = output_dir / f"{config['symbol']}240.csv"
        write_csv(bars, csv_file)
        
        # Show sample data
        print(f"  First bar: {bars[0]['time']} O={bars[0]['open']:.5f} C={bars[0]['close']:.5f}")
        print(f"  Last bar:  {bars[-1]['time']} O={bars[-1]['open']:.5f} C={bars[-1]['close']:.5f}")
        print(f"  Price range: {min(b['low'] for b in bars):.5f} - {max(b['high'] for b in bars):.5f}")
    
    print("\n" + "=" * 50)
    print("✅ Test data generation complete!")
    print(f"Files saved in: {output_dir}")
    
    # Test reading the generated file
    print("\n" + "=" * 50)
    print("Verifying generated data...")
    
    test_file = output_dir / "EURUSD240.hst"
    with open(test_file, 'rb') as f:
        # Skip header
        f.read(148)
        
        # Read first bar
        bar_data = f.read(60)
        time_val = struct.unpack('<I', bar_data[0:4])[0]
        f.seek(-56, 1)
        open_val = struct.unpack('<d', f.read(8))[0]
        high_val = struct.unpack('<d', f.read(8))[0]
        low_val = struct.unpack('<d', f.read(8))[0]
        close_val = struct.unpack('<d', f.read(8))[0]
        
        print(f"First bar from file:")
        print(f"  Time: {datetime.fromtimestamp(time_val)}")
        print(f"  OHLC: {open_val:.5f} / {high_val:.5f} / {low_val:.5f} / {close_val:.5f}")
        
        if 0.5 < open_val < 2.0:
            print("✅ Data validation: PASSED")
        else:
            print("❌ Data validation: FAILED")


if __name__ == "__main__":
    main()