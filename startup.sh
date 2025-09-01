#!/bin/bash

# Wait for X server to be ready
sleep 5

# Set Wine environment
export WINEPREFIX=/home/developer/.wine
export WINEDEBUG=-all
export DISPLAY=:1

# Check if MT4 is already installed
MT4_PATH="/home/developer/.wine/drive_c/Program Files (x86)/MetaTrader 4/terminal.exe"
MT4_ALT_PATH="/app/mt4-terminal/terminal.exe"

# Function to download and install MT4
install_mt4() {
    echo "Downloading MT4..."
    cd /tmp
    
    # Try multiple sources
    if wget -O mt4setup.exe "https://download.mql5.com/cdn/web/ig.group/mt4/ig4setup.exe"; then
        echo "Downloaded from IG"
    elif wget -O mt4setup.exe "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt4/mt4setup.exe"; then
        echo "Downloaded from MetaQuotes"
    else
        echo "Failed to download MT4 installer"
        return 1
    fi
    
    echo "Installing MT4..."
    # Try silent installation
    wine mt4setup.exe /auto 2>/dev/null || wine mt4setup.exe
    
    # Wait for installation to complete
    sleep 30
    
    # Copy MT4 to alternative location if installed
    if [ -f "$MT4_PATH" ]; then
        echo "Copying MT4 to /app/mt4-terminal..."
        cp -r "/home/developer/.wine/drive_c/Program Files (x86)/MetaTrader 4/"* /app/mt4-terminal/
    fi
}

# Check and install MT4 if needed
if [ ! -f "$MT4_PATH" ] && [ ! -f "$MT4_ALT_PATH" ]; then
    install_mt4
fi

# Determine which MT4 path to use
if [ -f "$MT4_ALT_PATH" ]; then
    TERMINAL_PATH="$MT4_ALT_PATH"
    TERMINAL_DIR="/app/mt4-terminal"
elif [ -f "$MT4_PATH" ]; then
    TERMINAL_PATH="$MT4_PATH"
    TERMINAL_DIR="/home/developer/.wine/drive_c/Program Files (x86)/MetaTrader 4"
else
    echo "MT4 not found, attempting installation..."
    install_mt4
    if [ -f "$MT4_ALT_PATH" ]; then
        TERMINAL_PATH="$MT4_ALT_PATH"
        TERMINAL_DIR="/app/mt4-terminal"
    else
        echo "Failed to install MT4"
        exit 1
    fi
fi

# Create MQL4 directories if they don't exist
mkdir -p "$TERMINAL_DIR/MQL4/Experts"
mkdir -p "$TERMINAL_DIR/MQL4/Indicators"
mkdir -p "$TERMINAL_DIR/MQL4/Scripts"
mkdir -p "$TERMINAL_DIR/MQL4/Include"
mkdir -p "$TERMINAL_DIR/MQL4/Libraries"
mkdir -p "$TERMINAL_DIR/MQL4/Files"
mkdir -p "$TERMINAL_DIR/MQL4/Logs"

# Copy PythonDataBridge.mq4 if it exists
if [ -f "/app/converter/PythonDataBridge.mq4" ]; then
    echo "Copying PythonDataBridge.mq4 to Experts folder..."
    cp /app/converter/PythonDataBridge.mq4 "$TERMINAL_DIR/MQL4/Experts/"
fi

# Start Python server in background if script exists
if [ -f "/app/converter/server/mt4_server.py" ]; then
    echo "Starting Python server..."
    python3 /app/converter/server/mt4_server.py &
fi

# Start MT4 terminal
echo "Starting MT4 Terminal at $TERMINAL_PATH..."
cd "$TERMINAL_DIR"
wine "$TERMINAL_PATH" /portable

# Keep the script running
tail -f /dev/null