# MT4 Setup Guide for WSL/Linux

This guide explains how to run MetaTrader 4 (MT4) in WSL/Linux and integrate it with the MQL-Python converter.

## Prerequisites

- WSL2 with Ubuntu (already installed)
- Wine for running Windows applications (already installed: wine-6.0.3)
- X Server for GUI applications (e.g., VcXsrv or WSLg)

## Option 1: Running MT4 with Wine in WSL

### Step 1: Initialize Wine Prefix
```bash
# Initialize Wine configuration
winecfg
```

### Step 2: Download MT4
```bash
# Create directory for MT4
mkdir -p ~/mt4
cd ~/mt4

# Download MT4 installer from your broker
# Example: wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt4/mt4setup.exe
```

### Step 3: Install MT4
```bash
# Install MT4 using Wine
wine mt4setup.exe
```

### Step 4: Run MT4
```bash
# Run MT4
wine ~/.wine/drive_c/Program\ Files\ \(x86\)/MetaTrader\ 4/terminal.exe
```

## Option 2: MT4 Python Integration (Recommended)

Instead of running MT4 directly, integrate with MT4 running on Windows host:

### Using MetaTrader5 Python Package
```python
# Install the package
pip install MetaTrader5

# Example connection
import MetaTrader5 as mt5

# Initialize connection
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()
```

### Using ZeroMQ Bridge
Create a bridge between MT4 and Python for real-time data:

1. **MT4 Side (MQL4 Expert Advisor)**:
```mql4
// SaveToFile.mq4 - Saves data to shared location
void OnTick() {
    int handle = FileOpen("shared_data.csv", FILE_WRITE|FILE_CSV);
    if(handle != INVALID_HANDLE) {
        FileWrite(handle, Symbol(), TimeCurrent(), Bid, Ask);
        FileClose(handle);
    }
}
```

2. **Python Side**:
```python
import pandas as pd
import time
from pathlib import Path

def read_mt4_data():
    # MT4 data directory in Wine
    mt4_data = Path.home() / ".wine/drive_c/users" / Path.home().name / "AppData/Roaming/MetaQuotes/Terminal/[ID]/MQL4/Files"
    
    data_file = mt4_data / "shared_data.csv"
    if data_file.exists():
        return pd.read_csv(data_file, names=['Symbol', 'Time', 'Bid', 'Ask'])
    return None
```

## Option 3: Direct Windows Host Integration

If MT4 is running on Windows host (not WSL):

### Share Data via Network
```python
# server.py - Run on Windows with MT4
import socket
import json

def start_mt4_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 9999))
    server.listen(1)
    
    while True:
        client, addr = server.accept()
        # Send MT4 data
        data = {"symbol": "EURUSD", "bid": 1.1234, "ask": 1.1235}
        client.send(json.dumps(data).encode())
        client.close()
```

### WSL Client
```python
# client.py - Run in WSL
import socket
import json

def get_mt4_data():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Use Windows host IP
    client.connect(('172.17.0.1', 9999))  # Adjust IP as needed
    data = json.loads(client.recv(1024).decode())
    client.close()
    return data
```

## Integration with MQL-Python Converter

### Workflow
1. Export EA/Indicators from MT4
2. Convert using the converter
3. Backtest with Python
4. Deploy back to MT4 or run standalone

### Example Integration Script
```python
#!/usr/bin/env python3
"""
MT4 Integration for MQL-Python Converter
"""

import os
import shutil
from pathlib import Path
from src.converters.mql5_converter import MQL5Converter

class MT4Integration:
    def __init__(self):
        self.wine_prefix = Path.home() / ".wine"
        self.mt4_path = self.find_mt4_installation()
        self.converter = MQL5Converter()
    
    def find_mt4_installation(self):
        """Find MT4 installation in Wine"""
        possible_paths = [
            self.wine_prefix / "drive_c/Program Files (x86)/MetaTrader 4",
            self.wine_prefix / "drive_c/Program Files/MetaTrader 4",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        return None
    
    def export_mql_files(self, output_dir="exported_mql"):
        """Export MQL4 files from MT4"""
        if not self.mt4_path:
            print("MT4 not found in Wine")
            return
        
        mql4_dir = self.mt4_path / "MQL4"
        
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
        # Copy Expert Advisors
        ea_dir = mql4_dir / "Experts"
        if ea_dir.exists():
            for ea_file in ea_dir.glob("*.mq4"):
                shutil.copy(ea_file, output_dir)
                print(f"Exported: {ea_file.name}")
        
        # Copy Indicators
        ind_dir = mql4_dir / "Indicators"
        if ind_dir.exists():
            for ind_file in ind_dir.glob("*.mq4"):
                shutil.copy(ind_file, output_dir)
                print(f"Exported: {ind_file.name}")
    
    def convert_exported_files(self, input_dir="exported_mql", output_dir="converted_python"):
        """Convert exported MQL4 files to Python"""
        Path(output_dir).mkdir(exist_ok=True)
        
        for mql_file in Path(input_dir).glob("*.mq4"):
            print(f"Converting {mql_file.name}...")
            
            with open(mql_file, 'r') as f:
                mql_code = f.read()
            
            # Convert to Python
            python_code = self.converter.convert(mql_code)
            
            # Save Python version
            output_file = Path(output_dir) / f"{mql_file.stem}.py"
            with open(output_file, 'w') as f:
                f.write(python_code)
            
            print(f"Saved: {output_file}")
    
    def run_mt4_terminal(self):
        """Launch MT4 terminal with Wine"""
        if not self.mt4_path:
            print("MT4 not found. Please install first.")
            return
        
        terminal_exe = self.mt4_path / "terminal.exe"
        if terminal_exe.exists():
            os.system(f"wine '{terminal_exe}'")
        else:
            print(f"Terminal.exe not found at {terminal_exe}")

if __name__ == "__main__":
    integration = MT4Integration()
    
    # Check MT4 installation
    if integration.mt4_path:
        print(f"MT4 found at: {integration.mt4_path}")
    else:
        print("MT4 not installed in Wine")
        print("Run: wine mt4setup.exe to install")
    
    # Example workflow
    # integration.export_mql_files()
    # integration.convert_exported_files()
    # integration.run_mt4_terminal()
```

## Troubleshooting

### X Server Issues
If you get display errors:
```bash
# For WSLg (Windows 11)
export DISPLAY=:0

# For VcXsrv (Windows 10)
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
```

### Wine Configuration
```bash
# Set Windows version for MT4 compatibility
winecfg
# Set to Windows 7 or Windows XP
```

### File Access
MT4 files in Wine are located at:
```
~/.wine/drive_c/Program Files (x86)/MetaTrader 4/
~/.wine/drive_c/users/[username]/AppData/Roaming/MetaQuotes/Terminal/[ID]/
```

## Alternative: Use MT5 Instead

MetaTrader 5 has better Python integration:
```bash
pip install MetaTrader5
```

This provides direct API access without Wine.

## Next Steps

1. Install MT4 if needed
2. Set up data bridge between MT4 and Python
3. Convert existing EAs/Indicators
4. Run backtests with Python
5. Deploy optimized strategies back to MT4