#!/bin/bash

# Exit on error
set -e

echo "Starting MT4 NoVNC Container..."
echo "================================"

# Function to cleanup on exit
cleanup() {
    echo "Cleaning up..."
    # Kill Wine processes gracefully
    wineserver -k || true
    # Kill any remaining processes
    pkill -f terminal.exe || true
    pkill -f wineserver || true
    pkill -f x11vnc || true
    pkill -f Xvfb || true
    exit 0
}

# Trap signals for cleanup
trap cleanup SIGINT SIGTERM EXIT

# Ensure directories exist with correct permissions
echo "Setting up directories..."
mkdir -p /home/mt4user/.wine
mkdir -p /home/mt4user/.vnc
mkdir -p /var/log/supervisor
mkdir -p /home/mt4user/mt4/MQL4/Experts
mkdir -p /home/mt4user/mt4/MQL4/Scripts
mkdir -p /home/mt4user/mt4/MQL4/Indicators
mkdir -p /home/mt4user/shared

# Initialize Wine if needed
if [ ! -f /home/mt4user/.wine/drive_c/windows/system32/kernel32.dll ]; then
    echo "Initializing Wine prefix..."
    export WINEPREFIX=/home/mt4user/.wine
    export WINEDEBUG=-all
    winecfg > /dev/null 2>&1 || true
    
    # Install Windows dependencies
    echo "Installing Windows dependencies..."
    winetricks -q dotnet40 vcrun2019 corefonts || true
fi

# Configure MT4 if config exists
if [ -f /home/mt4user/mt4/config/servers.ini ]; then
    echo "Configuring MT4 server settings..."
    cp -f /home/mt4user/mt4/config/servers.ini /home/mt4user/mt4/config/
fi

# Set VNC password if provided
if [ ! -z "$VNC_PASSWORD" ]; then
    echo "Setting VNC password..."
    x11vnc -storepasswd $VNC_PASSWORD /home/mt4user/.vnc/passwd
fi

# Create NoVNC HTML file with auto-connect
cat > /opt/novnc/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>MT4 Terminal - NoVNC</title>
    <meta charset="utf-8">
    <style>
        body { margin: 0; padding: 0; background: #222; }
        #screen { position: fixed; top: 0; left: 0; width: 100%; height: 100%; }
    </style>
</head>
<body>
    <div id="screen">
        <iframe src="vnc.html?autoconnect=true&password=mt4vnc&resize=scale" 
                style="width: 100%; height: 100%; border: none;">
        </iframe>
    </div>
</body>
</html>
EOF

# Display startup information
echo "================================"
echo "MT4 NoVNC Container Started"
echo "================================"
echo "Web Interface: http://localhost:6080"
echo "VNC Port: 5999"
echo "VNC Password: ${VNC_PASSWORD:-mt4vnc}"
echo "================================"

# Check if supervisor config exists
if [ ! -f /etc/supervisor/conf.d/supervisord.conf ]; then
    echo "Error: Supervisor configuration not found!"
    exit 1
fi

# Start supervisor
echo "Starting supervisor..."
exec "$@"