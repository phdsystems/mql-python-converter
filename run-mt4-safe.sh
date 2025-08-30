#!/bin/bash

# Safe MT4 runner that handles permissions and cleanup properly

# Function to cleanup on exit
cleanup() {
    echo "Cleaning up..."
    ./safe-cleanup.sh 2>/dev/null || true
    exit
}

# Set up trap for cleanup on script exit
trap cleanup EXIT INT TERM

# Check if running as developer user
if [ "$USER" != "developer" ]; then
    echo "Switching to developer user..."
    exec sudo -u developer "$0" "$@"
fi

# Clean up any existing processes first
echo "Ensuring clean state..."
./safe-cleanup.sh 2>/dev/null || true

# Choose mode
MODE=${1:-headless}

case $MODE in
    headless)
        echo "Starting MT4 in headless mode..."
        ./mt4_headless.sh start
        ;;
    gui)
        echo "Starting MT4 in GUI mode..."
        ./mt4_gui.sh start
        ;;
    web)
        echo "Starting MT4 in web mode..."
        ./mt4_web.sh start
        ;;
    *)
        echo "Usage: $0 [headless|gui|web]"
        echo "  headless - Run without display"
        echo "  gui      - Run with GUI (requires X11)"
        echo "  web      - Run with web interface"
        exit 1
        ;;
esac