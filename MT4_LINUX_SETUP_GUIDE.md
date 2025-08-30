# MT4 Linux Installation Guide

## Overview
This guide documents the complete process of installing MetaTrader 4 (MT4) on Linux using Wine, including all prerequisites, configuration steps, and known limitations.

**Status**: ✅ MT4 runs and compiles MQL4 scripts | ❌ Cannot connect to broker servers due to Wine network limitations

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [System Architecture Setup](#system-architecture-setup)
3. [Wine Installation](#wine-installation)
4. [MT4 Download and Installation](#mt4-download-and-installation)
5. [Virtual Display Setup](#virtual-display-setup)
6. [MT4 Configuration](#mt4-configuration)
7. [Server Configuration](#server-configuration)
8. [Running MT4](#running-mt4)
9. [Verification](#verification)
10. [Known Issues and Limitations](#known-issues-and-limitations)
11. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Linux system (tested on Ubuntu/Debian-based)
- At least 4GB RAM
- 2GB free disk space
- Internet connection for downloading packages

### Required Packages
- Wine (Windows compatibility layer)
- Xvfb (Virtual framebuffer for headless operation)
- Python 3 (for automation scripts)
- curl/wget (for downloading files)

## System Architecture Setup

### Enable 32-bit Architecture
MT4 is a 32-bit application, so we need to enable 32-bit support on 64-bit systems:

```bash
# Enable 32-bit architecture
sudo dpkg --add-architecture i386

# Update package lists
sudo apt update
```

## Wine Installation

### Step 1: Add Wine Repository
```bash
# Add Wine GPG key
sudo mkdir -pm755 /etc/apt/keyrings
sudo wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key

# Add Wine repository (for Ubuntu 22.04)
sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/jammy/winehq-jammy.sources

# Update packages
sudo apt update
```

### Step 2: Install Wine
```bash
# Install Wine stable version with all recommended packages
sudo apt install --install-recommends winehq-stable

# Verify installation
wine --version  # Should show wine-9.0 or similar
```

### Step 3: Configure Wine Environment
```bash
# Initialize Wine prefix (first-time setup)
wineboot -u

# Configure Wine for Windows 7 compatibility (MT4 works best with this)
wine reg add "HKEY_CURRENT_USER\Software\Wine" /v Version /t REG_SZ /d win7 /f
```

## MT4 Download and Installation

### Step 1: Download MT4 Installer
```bash
# Create directory structure
mkdir -p ~/mql-python-converter/server/mt4-terminal
cd ~/mql-python-converter

# Download MT4 installer from IG (or your broker)
curl -L -o ig4setup.exe "https://download.mql5.com/cdn/web/ig.group.limited/mt4/ig4setup.exe"
```

### Step 2: Install MT4
```bash
# Run installer with Wine
wine ig4setup.exe /portable /skipupdate

# The /portable flag installs MT4 in portable mode
# The /skipupdate flag prevents automatic updates during installation
```

### Step 3: Copy MT4 Files
After installation, MT4 files are typically installed in Wine's drive_c. Copy them to your project:

```bash
# Copy MT4 installation to project directory
cp -r ~/.wine/drive_c/Program\ Files*/IG\ MT4/* ~/mql-python-converter/server/mt4-terminal/

# Alternative: If installed elsewhere, find and copy
find ~/.wine -name "terminal.exe" -type f
# Then copy the parent directory containing terminal.exe
```

## Virtual Display Setup

### Step 1: Install Xvfb
```bash
# Install virtual framebuffer for headless operation
sudo apt install xvfb
```

### Step 2: Create Headless Runner Script
Create `mt4_headless.sh`:

```bash
cat > ~/mql-python-converter/mt4_headless.sh << 'EOF'
#!/bin/bash

# MT4 Headless Mode Runner Script
MT4_PATH="/home/developer/mql-python-converter/server/mt4-terminal"
DISPLAY_NUM=99
LOG_FILE="/home/developer/mql-python-converter/mt4_headless.log"

start_mt4() {
    echo "Starting MT4 in headless mode..."
    
    # Start Xvfb virtual display
    echo "Starting Xvfb virtual display..."
    Xvfb :$DISPLAY_NUM -screen 0 1024x768x16 &
    XVFB_PID=$!
    sleep 2
    
    # Set display environment
    export DISPLAY=:$DISPLAY_NUM
    
    # Start MT4 in background
    cd "$MT4_PATH"
    wine terminal.exe /portable /skipupdate >> "$LOG_FILE" 2>&1 &
    MT4_PID=$!
    
    echo "MT4 started with PID $MT4_PID"
    echo "Log file: $LOG_FILE"
    
    # Save PIDs for later
    echo $XVFB_PID > /tmp/xvfb.pid
    echo $MT4_PID > /tmp/mt4.pid
    
    # Check if running
    sleep 3
    if ps -p $MT4_PID > /dev/null; then
        echo "✅ MT4 is running successfully"
        tail -20 "$MT4_PATH/logs/$(date +%Y%m%d).log" 2>/dev/null
    else
        echo "❌ MT4 failed to start"
        tail -20 "$LOG_FILE"
    fi
}

stop_mt4() {
    echo "Stopping MT4..."
    
    # Kill MT4
    if [ -f /tmp/mt4.pid ]; then
        MT4_PID=$(cat /tmp/mt4.pid)
        kill $MT4_PID 2>/dev/null
        echo "MT4 stopped (PID $MT4_PID)"
        rm /tmp/mt4.pid
    fi
    
    # Kill Xvfb
    if [ -f /tmp/xvfb.pid ]; then
        XVFB_PID=$(cat /tmp/xvfb.pid)
        kill $XVFB_PID 2>/dev/null
        rm /tmp/xvfb.pid
    fi
}

status_mt4() {
    if [ -f /tmp/mt4.pid ]; then
        MT4_PID=$(cat /tmp/mt4.pid)
        if ps -p $MT4_PID > /dev/null; then
            echo "✅ MT4 is running (PID $MT4_PID)"
            echo "Recent log entries:"
            tail -10 "$MT4_PATH/logs/$(date +%Y%m%d).log" 2>/dev/null
        else
            echo "❌ MT4 is not running (stale PID file)"
        fi
    else
        echo "❌ MT4 is not running"
    fi
}

case "$1" in
    start)
        start_mt4
        ;;
    stop)
        stop_mt4
        ;;
    restart)
        stop_mt4
        sleep 2
        start_mt4
        ;;
    status)
        status_mt4
        ;;
    logs)
        tail -f "$MT4_PATH/logs/$(date +%Y%m%d).log"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
EOF

chmod +x ~/mql-python-converter/mt4_headless.sh
```

## MT4 Configuration

### Step 1: Configure Terminal Settings
Edit `server/mt4-terminal/config/terminal.ini`:

```ini
[Settings]
ServerName=IG-DEMO
ServerAddress=193.218.121.94:443
Login=815917
AccountName=PHD SYSTEMS
AccountType=demoforex-usd
AccountDeposit=100000
AccountServer=IG-DEMO
AccountInvestor=fd3cthy
```

## Server Configuration

### Step 1: Create Server Configuration File
Create `server/mt4-terminal/config/IG-DEMO.srv`:

```
IG-DEMO
193.218.121.94:443
193.218.121.102:443
193.218.121.79:443
193.218.121.96:443
193.218.121.73:443
193.218.121.85:443
193.218.121.51:443
193.218.121.67:443
193.218.121.131:443
193.218.121.118:443
```

### Step 2: Wine Network Configuration (Attempt to Fix Connection)
```bash
# Configure Wine network settings
wine reg add "HKEY_CURRENT_USER\Software\Wine\WinSock" /v UseWinsock /t REG_SZ /d native /f
wine reg add "HKEY_LOCAL_MACHINE\System\CurrentControlSet\Services\WinSock2\Parameters" /v WinSock_Registry_Version /t REG_SZ /d "2.0" /f
wine reg add "HKEY_CURRENT_USER\Software\Wine\Direct3D" /v MaxVersionGL /t REG_DWORD /d 0x00030002 /f
```

## Running MT4

### Start MT4 in Headless Mode
```bash
cd ~/mql-python-converter
./mt4_headless.sh start
```

### Stop MT4
```bash
./mt4_headless.sh stop
```

### Check Status
```bash
./mt4_headless.sh status
```

### View Logs
```bash
./mt4_headless.sh logs
```

## Verification

### Create Verification Script
Create `verify_mt4.py`:

```python
#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

def check_mt4_installation():
    mt4_path = Path("/home/developer/mql-python-converter/server/mt4-terminal")
    
    print("MT4 Installation Verification")
    print("=" * 50)
    
    # Check directories
    checks = {
        "MT4 Directory": mt4_path.exists(),
        "MQL4 Directory": (mt4_path / "MQL4").exists(),
        "Experts Directory": (mt4_path / "MQL4/Experts").exists(),
        "Scripts Directory": (mt4_path / "MQL4/Scripts").exists(),
        "Config Directory": (mt4_path / "config").exists(),
    }
    
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}: {result}")
    
    # Check if MT4 is running
    try:
        result = subprocess.run(['pgrep', '-f', 'terminal.exe'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ MT4 is running (PID: {result.stdout.strip()})")
        else:
            print("❌ MT4 is not running")
    except Exception as e:
        print(f"Could not check process: {e}")

if __name__ == "__main__":
    check_mt4_installation()
```

Run verification:
```bash
python3 verify_mt4.py
```

## Known Issues and Limitations

### ❌ Network Connection Error 10042
**Issue**: MT4 fails with "Initialization failed [10042]" error  
**Cause**: Wine's incomplete implementation of Windows socket (Winsock) API  
**Impact**: 
- Cannot connect to broker servers
- Cannot receive live price quotes
- Cannot execute live trades
- Cannot authenticate with account credentials

**What Still Works**:
- ✅ MT4 runs and starts
- ✅ MQL4 script compilation
- ✅ Access to historical data (up to May 2021 in demo data)
- ✅ File system operations
- ✅ Strategy Tester with historical data

### Wine Compatibility Issues
- Display errors: "Failed to query current display settings" - Normal in headless mode
- ALSA audio errors: Can be ignored, MT4 doesn't need audio
- Some GUI features may not work properly

## Troubleshooting

### Issue: MT4 Won't Start
```bash
# Check Wine installation
wine --version

# Check if 32-bit architecture is enabled
dpkg --print-foreign-architectures  # Should show i386

# Reinstall Wine dependencies
sudo apt install --reinstall wine32
```

### Issue: Display Errors
```bash
# Ensure Xvfb is running
ps aux | grep Xvfb

# Test display
DISPLAY=:99 xdpyinfo

# Restart with display debug
DISPLAY=:99 wine terminal.exe
```

### Issue: Missing DLLs
```bash
# Install Windows core fonts
sudo apt install ttf-mscorefonts-installer

# Install additional Wine packages
winetricks corefonts vcrun2019 dotnet48
```

### Issue: Permission Errors
```bash
# Fix permissions
chmod -R 755 ~/mql-python-converter/server/mt4-terminal
```

### Check Logs
```bash
# MT4 logs
tail -f ~/mql-python-converter/server/mt4-terminal/logs/$(date +%Y%m%d).log

# Wine debug output
WINEDEBUG=+all wine terminal.exe 2>&1 | grep -i error
```

## Alternative Solutions

### For Full Connectivity
1. **Use Windows VM**: Install VirtualBox/VMware with Windows
2. **Use Windows VPS**: Rent a Windows server
3. **Docker with Windows**: Use Windows containers (requires Windows host)
4. **MT5 for Linux**: Consider using MT5 which has better Linux support

### For Development/Testing
1. **Use Strategy Tester**: Work with historical data only
2. **Import tick data**: Use offline mode with imported data
3. **Focus on backtesting**: Develop strategies without live connection

## Conclusion

While MT4 installs and runs on Linux via Wine, the network connectivity is limited by Wine's incomplete Winsock implementation. This setup is suitable for:
- MQL4 development and compilation
- Backtesting with historical data
- File-based operations
- Learning and testing

For production trading, a Windows environment is recommended.

## References
- [Wine HQ](https://www.winehq.org/)
- [MT4 System Requirements](https://www.metatrader4.com/en/trading-platform/help/userguide/install_mt4)
- [Wine AppDB - MetaTrader 4](https://appdb.winehq.org/objectManager.php?sClass=application&iId=5442)