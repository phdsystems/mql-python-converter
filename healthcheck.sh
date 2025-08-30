#!/bin/bash

# Health check script for MT4 Docker container

# Check if Xvfb is running
if ! pgrep -x "Xvfb" > /dev/null; then
    echo "Xvfb is not running"
    exit 1
fi

# Check if supervisor is running
if ! pgrep -x "supervisord" > /dev/null; then
    echo "Supervisor is not running"
    exit 1
fi

# Check if VNC is accessible
if ! nc -z localhost 5901 2>/dev/null; then
    echo "VNC port is not accessible"
    exit 1
fi

# Check if noVNC web interface is accessible
if ! nc -z localhost 6080 2>/dev/null; then
    echo "noVNC port is not accessible"
    exit 1
fi

# Check Wine status
if ! su - wineuser -c "wineserver -p0" 2>/dev/null; then
    echo "Wine server is not responding"
    exit 1
fi

echo "Health check passed"
exit 0