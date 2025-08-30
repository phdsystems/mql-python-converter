#!/bin/bash

# MT4 Terminal Runner for Linux using Wine
# This script helps run MetaTrader 4 on Linux systems

MT4_DIR="./server/mt4-terminal"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "===================================="
echo "MT4 Terminal Runner for Linux"
echo "===================================="

# Check if Wine is installed
if ! command -v wine &> /dev/null; then
    echo "❌ Wine is not installed. Please install it first:"
    echo "   Ubuntu/Debian: sudo apt install wine wine32 wine64"
    echo "   Fedora: sudo dnf install wine"
    echo "   Arch: sudo pacman -S wine"
    exit 1
fi

echo "✓ Wine version: $(wine --version)"

# Options for running MT4
echo ""
echo "Choose how to run MT4:"
echo "1. Headless mode (no GUI, for automated trading)"
echo "2. With GUI (requires X server or VNC)"
echo "3. Virtual display mode (requires xvfb)"

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo "Running MT4 in headless mode..."
        echo "Note: This requires MT4 to be configured for automated trading"
        cd "$SCRIPT_DIR/$MT4_DIR"
        WINEDEBUG=-all wine terminal.exe /portable /skipupdate
        ;;
    2)
        echo "Running MT4 with GUI..."
        echo "Make sure you have:"
        echo "  - X server running (for local Linux)"
        echo "  - VNC server (for remote Linux)"
        echo "  - WSL with X server (for WSL2)"
        
        # For WSL2, try to set DISPLAY automatically
        if grep -qi microsoft /proc/version; then
            echo "Detected WSL2 environment"
            export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
            echo "Setting DISPLAY=$DISPLAY"
        fi
        
        cd "$SCRIPT_DIR/$MT4_DIR"
        wine terminal.exe /portable
        ;;
    3)
        echo "Running MT4 with virtual display..."
        if ! command -v xvfb-run &> /dev/null; then
            echo "❌ xvfb is not installed. Install it with:"
            echo "   sudo apt install xvfb"
            exit 1
        fi
        cd "$SCRIPT_DIR/$MT4_DIR"
        xvfb-run -a wine terminal.exe /portable
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "===================================="
echo "MT4 Terminal session ended"
echo "===================================="