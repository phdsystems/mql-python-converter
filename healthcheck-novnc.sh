#!/bin/bash

# Health check script for MT4 NoVNC container
# Returns 0 if healthy, 1 if unhealthy

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check function
check_service() {
    local service=$1
    local process=$2
    
    if pgrep -f "$process" > /dev/null; then
        echo -e "${GREEN}✓${NC} $service is running"
        return 0
    else
        echo -e "${RED}✗${NC} $service is NOT running"
        return 1
    fi
}

# Check network port
check_port() {
    local port=$1
    local service=$2
    
    if netstat -tulpn 2>/dev/null | grep -q ":$port "; then
        echo -e "${GREEN}✓${NC} $service port $port is listening"
        return 0
    else
        echo -e "${RED}✗${NC} $service port $port is NOT listening"
        return 1
    fi
}

# Initialize status
HEALTH_STATUS=0

echo "MT4 NoVNC Container Health Check"
echo "================================"

# Check Xvfb (Virtual Display)
if ! check_service "Xvfb" "Xvfb :99"; then
    HEALTH_STATUS=1
fi

# Check Fluxbox (Window Manager)
if ! check_service "Fluxbox" "fluxbox"; then
    HEALTH_STATUS=1
fi

# Check x11vnc (VNC Server)
if ! check_service "x11vnc" "x11vnc"; then
    HEALTH_STATUS=1
fi

# Check NoVNC (Web Interface)
if ! check_service "NoVNC" "novnc_proxy"; then
    HEALTH_STATUS=1
fi

# Check Wine Server
if ! check_service "Wine Server" "wineserver"; then
    echo -e "${YELLOW}!${NC} Wine Server may be idle (this is normal)"
fi

# Check MT4 Terminal
if ! check_service "MT4 Terminal" "terminal.exe"; then
    echo -e "${YELLOW}!${NC} MT4 Terminal may be starting up"
    # Give it more time on first health check
    if [ ! -f /tmp/mt4_started ]; then
        sleep 5
        if check_service "MT4 Terminal" "terminal.exe"; then
            touch /tmp/mt4_started
        else
            HEALTH_STATUS=1
        fi
    else
        HEALTH_STATUS=1
    fi
fi

# Check ports
echo "--------------------------------"
echo "Checking network ports..."

if ! check_port 6080 "NoVNC Web Interface"; then
    HEALTH_STATUS=1
fi

if ! check_port 5999 "VNC Server"; then
    HEALTH_STATUS=1
fi

# Check supervisor
echo "--------------------------------"
echo "Checking supervisor status..."

if supervisorctl status > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Supervisor is running"
    
    # Get detailed status
    SUPERVISOR_STATUS=$(supervisorctl status 2>/dev/null)
    
    # Check each service status
    while IFS= read -r line; do
        if echo "$line" | grep -q "RUNNING"; then
            SERVICE_NAME=$(echo "$line" | awk '{print $1}')
            echo -e "  ${GREEN}✓${NC} $SERVICE_NAME"
        elif echo "$line" | grep -q "STOPPED"; then
            SERVICE_NAME=$(echo "$line" | awk '{print $1}')
            echo -e "  ${YELLOW}!${NC} $SERVICE_NAME (stopped)"
        elif echo "$line" | grep -q "FATAL"; then
            SERVICE_NAME=$(echo "$line" | awk '{print $1}')
            echo -e "  ${RED}✗${NC} $SERVICE_NAME (fatal)"
            HEALTH_STATUS=1
        fi
    done <<< "$SUPERVISOR_STATUS"
else
    echo -e "${RED}✗${NC} Supervisor is NOT running"
    HEALTH_STATUS=1
fi

# Check disk space
echo "--------------------------------"
echo "Checking disk space..."

DISK_USAGE=$(df -h /home/mt4user | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${GREEN}✓${NC} Disk usage: ${DISK_USAGE}%"
else
    echo -e "${RED}✗${NC} Disk usage critical: ${DISK_USAGE}%"
    HEALTH_STATUS=1
fi

# Check memory
echo "--------------------------------"
echo "Checking memory usage..."

MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
if [ "$MEMORY_USAGE" -lt 90 ]; then
    echo -e "${GREEN}✓${NC} Memory usage: ${MEMORY_USAGE}%"
else
    echo -e "${YELLOW}!${NC} High memory usage: ${MEMORY_USAGE}%"
fi

# Final status
echo "================================"
if [ $HEALTH_STATUS -eq 0 ]; then
    echo -e "${GREEN}Container is HEALTHY${NC}"
    echo "Access MT4 at: http://localhost:6080"
else
    echo -e "${RED}Container is UNHEALTHY${NC}"
    echo "Check logs: docker logs mt4-novnc"
fi

exit $HEALTH_STATUS