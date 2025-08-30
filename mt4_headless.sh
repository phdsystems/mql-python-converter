#!/bin/bash

# MT4 Headless Runner Script
# Runs MT4 terminal in background with virtual display

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MT4_DIR="$SCRIPT_DIR/server/mt4-terminal"
PID_FILE="/tmp/mt4_headless.pid"
LOG_FILE="$SCRIPT_DIR/mt4_headless.log"

start_mt4() {
    echo "Starting MT4 in headless mode..."
    
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            echo "MT4 is already running with PID $OLD_PID"
            return 1
        fi
    fi
    
    # Start Xvfb if not running
    if ! pgrep -x "Xvfb" > /dev/null; then
        echo "Starting Xvfb virtual display..."
        Xvfb :99 -screen 0 1024x768x16 > /dev/null 2>&1 &
        sleep 2
    fi
    
    # Start MT4
    cd "$MT4_DIR"
    DISPLAY=:99 WINEDEBUG=-all wine terminal.exe /portable /skipupdate > "$LOG_FILE" 2>&1 &
    MT4_PID=$!
    echo $MT4_PID > "$PID_FILE"
    
    echo "MT4 started with PID $MT4_PID"
    echo "Log file: $LOG_FILE"
    echo "Checking if MT4 is running..."
    
    sleep 5
    
    if ps -p "$MT4_PID" > /dev/null 2>&1; then
        echo "✅ MT4 is running successfully"
        tail -n 20 "$MT4_DIR/logs/"*.log 2>/dev/null
    else
        echo "❌ MT4 failed to start. Check log file for details."
        tail -n 20 "$LOG_FILE"
    fi
}

stop_mt4() {
    echo "Stopping MT4..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            echo "MT4 stopped (PID $PID)"
        else
            echo "MT4 is not running"
        fi
        rm -f "$PID_FILE"
    else
        echo "No PID file found. MT4 may not be running."
    fi
    
    # Stop Xvfb if no other processes are using it
    pkill -f "Xvfb :99" 2>/dev/null
}

status_mt4() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ MT4 is running (PID $PID)"
            echo "Recent log entries:"
            tail -n 10 "$MT4_DIR/logs/"*.log 2>/dev/null
        else
            echo "❌ MT4 is not running (stale PID file)"
        fi
    else
        echo "❌ MT4 is not running"
    fi
}

logs_mt4() {
    echo "=== MT4 Process Log ==="
    tail -n 50 "$LOG_FILE" 2>/dev/null || echo "No process log found"
    echo ""
    echo "=== MT4 Terminal Log ==="
    tail -n 50 "$MT4_DIR/logs/"*.log 2>/dev/null || echo "No terminal log found"
}

case "$1" in
    start)
        start_mt4
        ;;
    stop)
        stop_mt4
        ;;
    restart)
        stop_mt4
        sleep 2
        start_mt4
        ;;
    status)
        status_mt4
        ;;
    logs)
        logs_mt4
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start MT4 in headless mode with virtual display"
        echo "  stop    - Stop MT4 and cleanup"
        echo "  restart - Restart MT4"
        echo "  status  - Check if MT4 is running"
        echo "  logs    - Show MT4 logs"
        exit 1
        ;;
esac