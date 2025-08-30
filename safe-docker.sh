#!/bin/bash
# Wrapper to handle Docker commands with proper cleanup

# Trap signals to ensure cleanup
cleanup() {
    echo "Cleaning up Docker processes..."
    docker ps -q | xargs -r docker stop 2>/dev/null || true
    pkill -u $USER -f "wine|terminal" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Run Docker command
if [ "$1" = "build" ] || [ "$1" = "run" ]; then
    sudo docker "$@"
else
    docker "$@" 2>/dev/null || sudo docker "$@"
fi
