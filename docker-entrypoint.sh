#!/bin/bash
set -e

# Set default username if not provided
USERNAME=${USERNAME:-developer}

echo "Starting MT4 Docker container as user: $USERNAME..."

# Cleanup function
cleanup() {
    echo "Received shutdown signal, cleaning up..."
    
    # Kill processes owned by container user
    su - $USERNAME -c "pkill -f wine" || true
    su - $USERNAME -c "pkill -f wineserver" || true
    su - $USERNAME -c "wineserver -k" || true
    
    # Kill VNC processes owned by container user
    su - $USERNAME -c "pkill -f x11vnc" || true
    su - $USERNAME -c "pkill -f Xvfb" || true
    su - $USERNAME -c "pkill -f websockify" || true
    
    # Kill Python processes owned by container user
    su - $USERNAME -c "pkill -f python3" || true
    
    # Cleanup supervisor
    su - $USERNAME -c "supervisorctl stop all" || true
    
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
chown -R $USERNAME:$USERNAME /app/logs /app/data /var/run/supervisor 2>/dev/null || true
chmod 755 /var/run/supervisor

# Setup display
export DISPLAY=:1
echo "Display set to $DISPLAY"

# Generate supervisord config from template
echo "Generating supervisord config for user: $USERNAME"
sed "s/__USERNAME__/$USERNAME/g" /etc/supervisor/conf.d/supervisord.conf.template > /etc/supervisor/conf.d/supervisord.conf

# Initialize Wine environment
su - $USERNAME -c "wineboot --init" || true

# Check if MT4 terminal exists
if [ ! -f "/home/$USERNAME/.wine/drive_c/Program Files (x86)/MetaTrader 4/terminal.exe" ]; then
    echo "MT4 not found, downloading and installing..."
    su - $USERNAME -c "cd /tmp && \
        wget -q https://download.mql5.com/cdn/web/metaquotes.software.corp/mt4/mt4setup.exe && \
        wine mt4setup.exe /auto" || echo "MT4 installation may require manual setup"
fi

# Start the main process
exec "$@"