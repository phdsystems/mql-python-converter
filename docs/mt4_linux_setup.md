# Running MT4 Terminal on Linux

## Prerequisites

1. **Wine Installation**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install wine wine32 wine64
   
   # Fedora
   sudo dnf install wine
   
   # Arch Linux
   sudo pacman -S wine
   ```

2. **For GUI Mode (Optional)**
   - Local Linux: X server (usually pre-installed)
   - Remote Linux: VNC server (`sudo apt install tightvncserver`)
   - WSL2: X server for Windows (VcXsrv or X410)

3. **For Virtual Display (Optional)**
   ```bash
   sudo apt install xvfb
   ```

## Running MT4

### Method 1: Using the Launch Script
```bash
./run_mt4_linux.sh
```
The script provides three options:
1. Headless mode (for automated trading)
2. GUI mode (requires display)
3. Virtual display mode (uses xvfb)

### Method 2: Direct Wine Commands

**Basic run:**
```bash
cd server/mt4-terminal
wine terminal.exe
```

**Portable mode (stores data locally):**
```bash
wine terminal.exe /portable
```

**Skip updates:**
```bash
wine terminal.exe /portable /skipupdate
```

**With custom config:**
```bash
wine terminal.exe /config:custom.ini
```

## WSL2 Specific Setup

1. **Install X Server on Windows**
   - Download and install VcXsrv or X410
   - Launch with "Disable access control" checked

2. **Set DISPLAY Variable**
   ```bash
   # Add to ~/.bashrc
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
   ```

3. **Allow Windows Firewall**
   - Allow VcXsrv through Windows Defender Firewall

## Headless/Automated Trading

For running MT4 without GUI (e.g., on VPS):

1. **Configure MT4 for auto-trading:**
   - Set up Expert Advisors
   - Enable auto-trading in terminal settings
   - Configure login credentials

2. **Run in background:**
   ```bash
   nohup wine terminal.exe /portable > mt4.log 2>&1 &
   ```

3. **Using screen/tmux:**
   ```bash
   # With screen
   screen -S mt4
   wine terminal.exe /portable
   # Detach: Ctrl+A, D
   
   # With tmux
   tmux new -s mt4
   wine terminal.exe /portable
   # Detach: Ctrl+B, D
   ```

## Troubleshooting

### Display Errors
```
err:winediag:nodrv_CreateWindow Make sure that your X server is running
```
**Solution:** Set DISPLAY variable or use xvfb:
```bash
export DISPLAY=:0
# or
xvfb-run wine terminal.exe
```

### Missing Dependencies
```bash
# Install 32-bit libraries
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install wine32
```

### Performance Issues
```bash
# Reduce Wine debug output
export WINEDEBUG=-all
wine terminal.exe
```

## Python Integration

Once MT4 is running, you can:

1. **Use the Python Bridge:**
   ```python
   from src.tools.mt4_integration import MT4Bridge
   
   bridge = MT4Bridge()
   bridge.connect()
   ```

2. **Monitor Expert Advisors:**
   - Place EA files in: `server/mt4-terminal/MQL4/Experts/`
   - Compile with MetaEditor
   - Attach to charts in MT4

3. **Data Export:**
   - Configure DDE server in MT4
   - Use Python to read exported data
   - Process with pandas/numpy

## Security Notes

- Never store credentials in scripts
- Use environment variables for sensitive data
- Restrict Wine permissions if running on production server
- Consider using Docker for isolation