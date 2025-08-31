#!/bin/bash
# Secure startup script running as non-root user

set -e

echo "Starting services as user: $(whoami)"
echo "Home directory: $HOME"
echo "Wine prefix: $WINEPREFIX"

# Ensure directories exist with proper permissions
mkdir -p /app/logs
mkdir -p /app/data
mkdir -p $HOME/.wine

# Initialize Wine if needed (as non-root user)
if [ ! -f "$HOME/.wine/system.reg" ]; then
    echo "Initializing Wine prefix..."
    wineboot --init
    echo "Wine initialized successfully"
fi

# Install MT4 if not present (example)
MT4_DIR="$HOME/.wine/drive_c/Program Files (x86)/MetaTrader 4"
if [ ! -d "$MT4_DIR" ]; then
    echo "MT4 not found. Please install MT4 manually or add installation script here."
    # Add MT4 installation commands here if needed
fi

# Create a simple test to verify X11 is working
if [ -n "$DISPLAY" ]; then
    echo "Display is set to: $DISPLAY"
    # Test X11 connection
    xset q > /dev/null 2>&1 && echo "X11 connection successful" || echo "X11 connection failed"
fi

# Start any additional services needed
echo "Startup complete for user: $(whoami)"

# Keep the container running if this is the main process
if [ "$1" = "keep-alive" ]; then
    echo "Keeping container alive..."
    tail -f /dev/null
fi