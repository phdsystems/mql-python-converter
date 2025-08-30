#!/bin/bash
set -e

echo "Starting MT4 Docker container..."

# Cleanup function
cleanup() {
    echo "Received shutdown signal, cleaning up..."
    
    # Kill Wine processes
    pkill -f wine || true
    pkill -f wineserver || true
    wineserver -k || true
    
    # Kill VNC processes
    pkill -f x11vnc || true
    pkill -f Xvfb || true
    pkill -f websockify || true
    
    # Kill Python processes
    pkill -f python3 || true
    
    # Cleanup supervisor
    supervisorctl stop all || true
    
    echo "Cleanup complete"
    exit 0
}

# Trap signals
trap cleanup SIGTERM SIGINT SIGQUIT

# Create necessary directories
mkdir -p /app/logs
mkdir -p /app/data
mkdir -p /var/run/supervisor

# Fix permissions
chown -R wineuser:wineuser /app/logs /app/data 2>/dev/null || true
chmod 755 /var/run/supervisor

# Setup display
export DISPLAY=:1
echo "Display set to $DISPLAY"

# Initialize Wine environment
su - wineuser -c "wineboot --init" || true

# Check if MT4 terminal exists
if [ ! -f "/home/wineuser/.wine/drive_c/Program Files (x86)/MetaTrader 4/terminal.exe" ]; then
    echo "MT4 not found, downloading and installing..."
    su - wineuser -c "cd /tmp && \
        wget -q https://download.mql5.com/cdn/web/metaquotes.software.corp/mt4/mt4setup.exe && \
        wine mt4setup.exe /auto" || echo "MT4 installation may require manual setup"
fi

# Start the main process
exec "$@"