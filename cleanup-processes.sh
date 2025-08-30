#!/bin/bash

echo "Cleaning up Wine and MT4 processes..."

# Kill Wine processes
pkill -f "C:\\\\windows\\\\system32" 2>/dev/null || true
pkill -f explorer.exe 2>/dev/null || true
pkill -f services.exe 2>/dev/null || true
pkill -f rpcss.exe 2>/dev/null || true
pkill -f plugplay.exe 2>/dev/null || true
pkill -f svchost.exe 2>/dev/null || true

# Kill websockify/VNC if running
pkill -f websockify 2>/dev/null || true
pkill -f novnc_proxy 2>/dev/null || true

# Clean up any Wine server instances
wineserver -k 2>/dev/null || true

# Wait a moment for processes to terminate
sleep 2

# Force kill if still running
pkill -9 -f "C:\\\\windows\\\\system32" 2>/dev/null || true

echo "Cleanup complete. Checking remaining processes..."
ps aux | grep -E "wine|terminal|explorer" | grep -v grep || echo "No Wine/MT4 processes found."