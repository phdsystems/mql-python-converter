#!/bin/bash
# Wrapper to handle Docker commands with proper cleanup

# Trap signals to ensure cleanup
cleanup() {
    echo "Cleaning up Docker processes..."
    sudo docker ps -q | xargs -r sudo docker stop 2>/dev/null || true
    pkill -u $USER -f "wine|terminal" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Run Docker command with sudo
sudo docker "$@"
