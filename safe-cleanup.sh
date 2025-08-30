#!/bin/bash

# Safe cleanup script that handles permission issues gracefully

echo "Starting safe cleanup process..."

# Function to safely kill processes
safe_kill() {
    local pid=$1
    local name=$2
    
    if [ -n "$pid" ]; then
        echo "Attempting to kill $name (PID: $pid)..."
        
        # Try normal kill first
        if kill $pid 2>/dev/null; then
            echo "Successfully killed $name"
        else
            # Try with sudo if normal kill fails
            echo "Normal kill failed, trying with sudo..."
            if sudo kill $pid 2>/dev/null; then
                echo "Successfully killed $name with sudo"
            else
                echo "Warning: Could not kill $name (PID: $pid)"
            fi
        fi
        
        # Give process time to terminate
        sleep 1
        
        # Force kill if still running
        if kill -0 $pid 2>/dev/null; then
            echo "Process still running, force killing..."
            sudo kill -9 $pid 2>/dev/null || true
        fi
    fi
}

# Kill Wine processes
echo "Cleaning up Wine processes..."
for pid in $(pgrep -f wine); do
    safe_kill $pid "Wine process"
done

# Kill MT4 related processes
echo "Cleaning up MT4 processes..."
for pid in $(pgrep -f terminal.exe); do
    safe_kill $pid "MT4 Terminal"
done

# Kill Xvfb
echo "Cleaning up Xvfb..."
for pid in $(pgrep Xvfb); do
    safe_kill $pid "Xvfb"
done

# Clean up wine server
echo "Cleaning up wineserver..."
wineserver -k 2>/dev/null || true
sleep 1
wineserver -k9 2>/dev/null || true

# Clean up any orphaned processes
echo "Cleaning up orphaned processes..."
sudo pkill -f wine 2>/dev/null || true
sudo pkill -f terminal.exe 2>/dev/null || true
sudo pkill -f Xvfb 2>/dev/null || true

# Clean up temporary files
echo "Cleaning up temporary files..."
rm -f /tmp/.X99-lock 2>/dev/null || true
rm -rf /tmp/.wine-* 2>/dev/null || true

echo "Cleanup completed!"
echo ""
echo "Verification:"
ps aux | grep -E "(wine|terminal|Xvfb)" | grep -v grep || echo "No related processes found (clean state)"