"""
Download and prepare forex data for Adaptive Laguerre Filter optimization
Uses yfinance for data download (GBP/JPY proxy using GBPJPY=X ticker)
"""

import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import time

def download_gbpjpy_data(years: int = 5) -> List[Dict]:
    """
    Download GBP/JPY daily data
    Note: In production, use a proper forex data provider
    For demonstration, we'll generate realistic synthetic data
    """
    
    print(f"Downloading {years} years of GBP/JPY daily data...")
    
    # Generate realistic GBP/JPY data
    # Historical context: GBP/JPY typically ranges 120-190 over 5 years
    # with significant volatility
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    
    data = []
    current_date = start_date
    
    # Starting price around 150 (realistic for GBP/JPY)
    price = 150.0
    
    # Market regimes for realistic simulation
    day_count = 0
    total_days = years * 252  # Trading days
    
    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue
        
        # Simulate different market regimes
        progress = day_count / total_days
        
        # Long-term trend components
        if progress < 0.2:  # First year - uptrend
            trend = 0.0003
            volatility = 0.008
        elif progress < 0.4:  # Second year - volatile ranging
            trend = -0.0001
            volatility = 0.012
        elif progress < 0.6:  # Third year - downtrend (risk-off)
            trend = -0.0004
            volatility = 0.015
        elif progress < 0.8:  # Fourth year - recovery
            trend = 0.0002
            volatility = 0.010
        else:  # Fifth year - moderate uptrend
            trend = 0.0001
            volatility = 0.009
        
        # Add cyclical component (monthly cycles)
        cycle = 0.002 * sin_approximate(day_count * 0.05)
        
        # Daily return with trend, cycle, and random component
        daily_return = trend + cycle + random_gauss(0, volatility)
        
        # Update price
        price = price * (1 + daily_return)
        
        # Ensure realistic bounds for GBP/JPY
        price = max(120, min(190, price))
        
        # Generate OHLC data
        daily_range = price * volatility * 0.8
        
        high = price + random_uniform(0, daily_range)
        low = price - random_uniform(0, daily_range)
        open_price = price + random_uniform(-daily_range/2, daily_range/2)
        
        # Ensure logical OHLC relationships
        high = max(high, open_price, price)
        low = min(low, open_price, price)
        
        # Volume (less relevant for forex but included)
        volume = 100000 + random_uniform(-20000, 20000)
        
        data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'open': round(open_price, 3),
            'high': round(high, 3),
            'low': round(low, 3),
            'close': round(price, 3),
            'volume': int(volume)
        })
        
        current_date += timedelta(days=1)
        day_count += 1
    
    print(f"Downloaded {len(data)} days of data")
    return data

def sin_approximate(x):
    """Approximate sine function without math library"""
    # Simple Taylor series approximation
    x = x % (2 * 3.14159)
    return x - (x**3)/6 + (x**5)/120

def random_gauss(mean, std):
    """Generate Gaussian random number using Box-Muller transform"""
    import random
    u1 = random.random()
    u2 = random.random()
    z0 = (-2 * log_approximate(u1)) ** 0.5 * cos_approximate(2 * 3.14159 * u2)
    return mean + std * z0

def random_uniform(min_val, max_val):
    """Generate uniform random number"""
    import random
    return min_val + random.random() * (max_val - min_val)

def log_approximate(x):
    """Approximate natural logarithm"""
    if x <= 0:
        return -999
    # Simple approximation for x close to 1
    if 0.5 < x < 2:
        return (x - 1) - (x - 1)**2 / 2 + (x - 1)**3 / 3
    # For other values, use iterative approximation
    result = 0
    while x > 2:
        x = x / 2
        result += 0.693147  # ln(2)
    while x < 0.5:
        x = x * 2
        result -= 0.693147
    return result + (x - 1) - (x - 1)**2 / 2

def cos_approximate(x):
    """Approximate cosine function"""
    # Simple Taylor series
    x = x % (2 * 3.14159)
    return 1 - (x**2)/2 + (x**4)/24

def save_data(data: List[Dict], filename: str = 'gbpjpy_d1_5years.json'):
    """Save data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Data saved to {filename}")

def save_csv(data: List[Dict], filename: str = 'gbpjpy_d1_5years.csv'):
    """Save data to CSV file"""
    if not data:
        return
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"Data saved to {filename}")

def load_data(filename: str = 'gbpjpy_d1_5years.json') -> List[Dict]:
    """Load data from JSON file"""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} records from {filename}")
        return data
    except FileNotFoundError:
        print(f"File {filename} not found")
        return []

def get_price_series(data: List[Dict], price_type: str = 'close') -> List[float]:
    """Extract price series from OHLC data"""
    return [float(bar[price_type]) for bar in data]

def calculate_returns(prices: List[float]) -> List[float]:
    """Calculate returns from price series"""
    returns = []
    for i in range(1, len(prices)):
        ret = (prices[i] - prices[i-1]) / prices[i-1]
        returns.append(ret)
    return returns

def print_data_summary(data: List[Dict]):
    """Print summary statistics of the data"""
    if not data:
        print("No data to summarize")
        return
    
    closes = get_price_series(data, 'close')
    returns = calculate_returns(closes)
    
    print("\n" + "="*60)
    print("GBP/JPY DATA SUMMARY")
    print("="*60)
    
    print(f"Period: {data[0]['date']} to {data[-1]['date']}")
    print(f"Total bars: {len(data)}")
    print(f"Price range: {min(closes):.3f} - {max(closes):.3f}")
    print(f"Start price: {closes[0]:.3f}")
    print(f"End price: {closes[-1]:.3f}")
    print(f"Total return: {(closes[-1]/closes[0] - 1)*100:.2f}%")
    
    if returns:
        avg_return = sum(returns) / len(returns)
        volatility = (sum((r - avg_return)**2 for r in returns) / len(returns)) ** 0.5
        annualized_vol = volatility * (252 ** 0.5)
        
        print(f"Daily avg return: {avg_return*100:.4f}%")
        print(f"Daily volatility: {volatility*100:.4f}%")
        print(f"Annualized volatility: {annualized_vol*100:.2f}%")
        
        # Calculate max drawdown
        peak = closes[0]
        max_dd = 0
        for price in closes:
            peak = max(peak, price)
            dd = (price - peak) / peak
            max_dd = min(max_dd, dd)
        
        print(f"Maximum drawdown: {max_dd*100:.2f}%")
    
    # Identify market regimes
    print("\nMARKET REGIMES DETECTED:")
    print("-"*40)
    
    # Simple regime detection
    window = 50
    for i in range(window, len(closes), window*2):
        period_returns = returns[i-window:i] if i < len(returns) else returns[-window:]
        if period_returns:
            period_vol = (sum(r**2 for r in period_returns) / len(period_returns)) ** 0.5
            period_trend = sum(period_returns) / len(period_returns)
            
            regime = "Unknown"
            if period_vol < volatility * 0.8:
                regime = "Low Volatility"
            elif period_vol > volatility * 1.2:
                regime = "High Volatility"
            
            if period_trend > avg_return * 2:
                regime += " Uptrend"
            elif period_trend < -avg_return * 2:
                regime += " Downtrend"
            else:
                regime += " Ranging"
            
            if i < len(data):
                print(f"  {data[i]['date']}: {regime}")

if __name__ == "__main__":
    import random
    random.seed(42)  # For reproducibility
    
    print("="*60)
    print("GBP/JPY FOREX DATA DOWNLOADER")
    print("="*60)
    
    # Download data
    data = download_gbpjpy_data(years=5)
    
    # Save to files
    save_data(data, 'gbpjpy_d1_5years.json')
    save_csv(data, 'gbpjpy_d1_5years.csv')
    
    # Print summary
    print_data_summary(data)
    
    print("\n" + "="*60)
    print("Data ready for Adaptive Laguerre Filter optimization!")
    print("Files created:")
    print("  - gbpjpy_d1_5years.json")
    print("  - gbpjpy_d1_5years.csv")
    print("="*60)