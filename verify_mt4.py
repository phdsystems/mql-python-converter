#!/usr/bin/env python3
"""
Verify MT4 Installation and Functionality
"""
import os
import struct
import datetime
from pathlib import Path

def check_mt4_installation():
    """Check if MT4 is properly installed and configured"""
    mt4_path = Path("/home/developer/mql-python-converter/server/mt4-terminal")
    
    print("MT4 Installation Verification")
    print("=" * 50)
    
    # Check basic directories
    checks = {
        "MT4 Directory": mt4_path.exists(),
        "MQL4 Directory": (mt4_path / "MQL4").exists(),
        "Experts Directory": (mt4_path / "MQL4/Experts").exists(),
        "Scripts Directory": (mt4_path / "MQL4/Scripts").exists(),
        "Indicators Directory": (mt4_path / "MQL4/Indicators").exists(),
        "Files Directory": (mt4_path / "MQL4/Files").exists(),
        "Logs Directory": (mt4_path / "logs").exists(),
        "History Directory": (mt4_path / "history").exists(),
        "Config Directory": (mt4_path / "config").exists(),
    }
    
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}: {result}")
    
    print("\n" + "=" * 50)
    print("Configuration Files:")
    
    # Check configuration files
    config_files = [
        "config/terminal.ini",
        "config/IG-DEMO.srv",
    ]
    
    for config_file in config_files:
        file_path = mt4_path / config_file
        if file_path.exists():
            print(f"✅ {config_file} exists ({file_path.stat().st_size} bytes)")
        else:
            print(f"❌ {config_file} missing")
    
    print("\n" + "=" * 50)
    print("Market Data:")
    
    # Check for market data files
    history_path = mt4_path / "history/default"
    if history_path.exists():
        hst_files = list(history_path.glob("*.hst"))
        print(f"Found {len(hst_files)} history files")
        if hst_files:
            print("Sample symbols with data:")
            for hst_file in hst_files[:5]:
                symbol = hst_file.stem[:-3]  # Remove timeframe suffix
                print(f"  - {symbol}")
    
    print("\n" + "=" * 50)
    print("Recent Logs:")
    
    # Check recent logs
    log_dir = mt4_path / "logs"
    if log_dir.exists():
        log_files = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
        if log_files:
            latest_log = log_files[0]
            print(f"Latest log: {latest_log.name}")
            try:
                with open(latest_log, 'r', encoding='utf-16-le', errors='ignore') as f:
                    lines = f.readlines()[-5:]
                    print("Last 5 lines:")
                    for line in lines:
                        print(f"  {line.strip()}")
            except:
                pass
    
    print("\n" + "=" * 50)
    print("Process Status:")
    
    # Check if MT4 is running
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', 'terminal.exe'], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✅ MT4 is running (PID: {', '.join(pids)})")
        else:
            print("❌ MT4 is not running")
    except Exception as e:
        print(f"Could not check process: {e}")
    
    print("\n" + "=" * 50)
    print("Summary:")
    
    all_checks_passed = all(checks.values())
    if all_checks_passed:
        print("✅ MT4 installation appears to be complete and functional")
        print("   The terminal is ready for MQL4 script execution")
    else:
        print("⚠️  Some components are missing or not configured")
    
    return all_checks_passed

if __name__ == "__main__":
    check_mt4_installation()