#!/bin/bash

# MT4 GUI Access Script with VNC
# Allows GUI access to MT4 for downloading fresh data

MT4_PATH="/home/developer/mql-python-converter/server/mt4-terminal"
DISPLAY_NUM=99
VNC_PORT=5999
VNC_PASSWORD="mt4vnc"
LOG_FILE="/home/developer/mql-python-converter/mt4_gui.log"

start_gui() {
    echo "Starting MT4 with GUI access via VNC..."
    
    # Kill any existing instances
    pkill -f Xvfb
    pkill -f x11vnc
    pkill -f fluxbox
    pkill -f terminal.exe
    sleep 2
    
    # Start Xvfb with larger resolution for better GUI experience
    echo "Starting virtual display..."
    Xvfb :$DISPLAY_NUM -screen 0 1280x1024x24 &
    XVFB_PID=$!
    sleep 2
    
    # Set display
    export DISPLAY=:$DISPLAY_NUM
    
    # Start fluxbox window manager
    echo "Starting window manager..."
    fluxbox &
    FLUXBOX_PID=$!
    sleep 2
    
    # Start VNC server
    echo "Starting VNC server on port $VNC_PORT..."
    x11vnc -display :$DISPLAY_NUM -forever -shared -rfbport $VNC_PORT -passwd $VNC_PASSWORD -bg -o $LOG_FILE
    
    # Start MT4
    echo "Starting MT4..."
    cd "$MT4_PATH"
    wine terminal.exe /portable &
    MT4_PID=$!
    
    # Save PIDs
    echo $XVFB_PID > /tmp/xvfb_gui.pid
    echo $FLUXBOX_PID > /tmp/fluxbox.pid
    echo $MT4_PID > /tmp/mt4_gui.pid
    
    echo ""
    echo "========================================="
    echo "✅ MT4 GUI is running!"
    echo "========================================="
    echo ""
    echo "📱 VNC Connection Details:"
    echo "   Host: localhost"
    echo "   Port: $VNC_PORT"
    echo "   Password: $VNC_PASSWORD"
    echo ""
    echo "🔗 Connect using VNC viewer:"
    echo "   vncviewer localhost:$VNC_PORT"
    echo "   or"
    echo "   Remote: <your-ip>:$VNC_PORT"
    echo ""
    echo "📊 To download fresh data in MT4:"
    echo "   1. Connect via VNC"
    echo "   2. Go to Tools > History Center"
    echo "   3. Select symbol (e.g., EURUSD)"
    echo "   4. Double-click timeframe (e.g., H4)"
    echo "   5. Click 'Download' button"
    echo ""
    echo "⚠️  Note: Due to Wine limitations, online connection may not work"
    echo "    You can still import .csv data files"
    echo "========================================="
}

stop_gui() {
    echo "Stopping MT4 GUI..."
    
    # Kill processes
    if [ -f /tmp/mt4_gui.pid ]; then
        kill $(cat /tmp/mt4_gui.pid) 2>/dev/null
        rm /tmp/mt4_gui.pid
    fi
    
    if [ -f /tmp/fluxbox.pid ]; then
        kill $(cat /tmp/fluxbox.pid) 2>/dev/null
        rm /tmp/fluxbox.pid
    fi
    
    if [ -f /tmp/xvfb_gui.pid ]; then
        kill $(cat /tmp/xvfb_gui.pid) 2>/dev/null
        rm /tmp/xvfb_gui.pid
    fi
    
    # Kill VNC
    pkill -f x11vnc
    
    echo "MT4 GUI stopped"
}

status_gui() {
    echo "Checking MT4 GUI status..."
    
    # Check Xvfb
    if pgrep -f "Xvfb :$DISPLAY_NUM" > /dev/null; then
        echo "✅ Virtual display is running"
    else
        echo "❌ Virtual display is not running"
    fi
    
    # Check VNC
    if pgrep -f "x11vnc.*$VNC_PORT" > /dev/null; then
        echo "✅ VNC server is running on port $VNC_PORT"
    else
        echo "❌ VNC server is not running"
    fi
    
    # Check MT4
    if pgrep -f terminal.exe > /dev/null; then
        echo "✅ MT4 is running"
    else
        echo "❌ MT4 is not running"
    fi
    
    # Check if port is listening
    if netstat -tuln 2>/dev/null | grep -q ":$VNC_PORT"; then
        echo "✅ VNC port $VNC_PORT is listening"
    else
        echo "⚠️  VNC port $VNC_PORT is not accessible"
    fi
}

import_csv() {
    # Function to help import CSV data
    echo "CSV Import Helper"
    echo "================="
    echo ""
    echo "To import CSV data into MT4:"
    echo "1. Place your CSV file in: $MT4_PATH/MQL4/Files/"
    echo "2. Format should be: Date,Time,Open,High,Low,Close,Volume"
    echo "3. In MT4: Tools > History Center > Import"
    echo ""
    echo "Sample CSV format:"
    echo "2020.01.01,00:00,1.1000,1.1010,1.0990,1.1005,1000"
    echo ""
    
    # Check for CSV files
    echo "Available CSV files:"
    ls -la "$MT4_PATH/MQL4/Files/"*.csv 2>/dev/null || echo "No CSV files found"
}

download_data() {
    # Download sample forex data
    echo "Downloading sample forex data..."
    
    DATA_DIR="$MT4_PATH/MQL4/Files"
    mkdir -p "$DATA_DIR"
    
    # You can add wget commands here to download historical data
    # For example, from free data sources
    
    echo "Sample data download URLs:"
    echo "1. https://www.histdata.com - Free forex historical data"
    echo "2. https://www.dukascopy.com/trading-tools/widgets/quotes/historical_data_feed"
    echo ""
    echo "Download data manually and place in: $DATA_DIR"
}

case "$1" in
    start)
        start_gui
        ;;
    stop)
        stop_gui
        ;;
    restart)
        stop_gui
        sleep 2
        start_gui
        ;;
    status)
        status_gui
        ;;
    import)
        import_csv
        ;;
    download)
        download_data
        ;;
    *)
        echo "MT4 GUI Manager - Access MT4 with graphical interface"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|import|download}"
        echo ""
        echo "Commands:"
        echo "  start    - Start MT4 with VNC access"
        echo "  stop     - Stop MT4 and VNC server"
        echo "  restart  - Restart MT4 GUI"
        echo "  status   - Check if services are running"
        echo "  import   - Show CSV import instructions"
        echo "  download - Show data download sources"
        echo ""
        echo "After starting, connect with VNC viewer to localhost:$VNC_PORT"
        echo "Password: $VNC_PASSWORD"
        exit 1
        ;;
esac