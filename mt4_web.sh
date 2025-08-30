#!/bin/bash

# MT4 Web Access Script
# Access MT4 through a web browser - no VNC client needed!

MT4_PATH="/home/developer/mql-python-converter/server/mt4-terminal"
NOVNC_PATH="/home/developer/noVNC"
WEB_PORT=8080
VNC_PORT=5999
PASSWORD="mt4vnc"

start_web() {
    echo "Starting MT4 Web Access..."
    
    # Check if MT4 GUI is running
    if ! pgrep -f "x11vnc.*5999" > /dev/null; then
        echo "MT4 GUI is not running. Starting it first..."
        ./mt4_gui.sh start
        sleep 5
    fi
    
    # Kill any existing noVNC
    pkill -f "websockify.*$WEB_PORT"
    sleep 1
    
    # Start noVNC web server
    echo "Starting web server on port $WEB_PORT..."
    cd "$NOVNC_PATH"
    ./utils/novnc_proxy --vnc localhost:$VNC_PORT --listen $WEB_PORT &
    NOVNC_PID=$!
    
    # Save PID
    echo $NOVNC_PID > /tmp/novnc.pid
    
    sleep 3
    
    echo ""
    echo "========================================="
    echo "✅ MT4 Web Access is Ready!"
    echo "========================================="
    echo ""
    echo "🌐 Open in your web browser:"
    echo "   http://41.150.50.119:$WEB_PORT/vnc.html"
    echo ""
    echo "📱 Or from local network:"
    echo "   http://localhost:$WEB_PORT/vnc.html"
    echo ""
    echo "🔐 When prompted for password, enter: $PASSWORD"
    echo ""
    echo "📊 In MT4 you can:"
    echo "   • Import CSV data (Tools > History Center > Import)"
    echo "   • View charts and indicators"
    echo "   • Test Expert Advisors"
    echo "   • Export data for analysis"
    echo ""
    echo "⚠️  Note: Port $WEB_PORT must be open in firewall"
    echo "========================================="
}

stop_web() {
    echo "Stopping MT4 Web Access..."
    
    # Kill noVNC
    if [ -f /tmp/novnc.pid ]; then
        kill $(cat /tmp/novnc.pid) 2>/dev/null
        rm /tmp/novnc.pid
    fi
    
    pkill -f "websockify.*$WEB_PORT"
    
    echo "Web access stopped"
}

status_web() {
    echo "Checking MT4 Web Access status..."
    
    # Check noVNC
    if pgrep -f "websockify.*$WEB_PORT" > /dev/null; then
        echo "✅ Web server is running on port $WEB_PORT"
        echo "   URL: http://41.150.50.119:$WEB_PORT/vnc.html"
    else
        echo "❌ Web server is not running"
    fi
    
    # Check VNC
    if pgrep -f "x11vnc.*$VNC_PORT" > /dev/null; then
        echo "✅ VNC server is running"
    else
        echo "❌ VNC server is not running"
    fi
    
    # Check MT4
    if pgrep -f terminal.exe > /dev/null; then
        echo "✅ MT4 is running"
    else
        echo "❌ MT4 is not running"
    fi
}

download_csv() {
    echo "Downloading sample CSV data..."
    
    DATA_DIR="$MT4_PATH/MQL4/Files"
    mkdir -p "$DATA_DIR"
    
    # Download sample data from histdata.com (they provide free forex data)
    echo "Downloading EURUSD sample data..."
    
    # Create a sample CSV with proper format
    cat > "$DATA_DIR/EURUSD_H4_sample.csv" << 'EOF'
Date,Time,Open,High,Low,Close,Volume
2023.01.02,00:00,1.0658,1.0703,1.0652,1.0698,1524
2023.01.02,04:00,1.0698,1.0712,1.0685,1.0689,1832
2023.01.02,08:00,1.0689,1.0695,1.0672,1.0678,2103
2023.01.02,12:00,1.0678,1.0688,1.0665,1.0683,1987
2023.01.02,16:00,1.0683,1.0702,1.0680,1.0695,2234
2023.01.02,20:00,1.0695,1.0705,1.0688,1.0692,1756
EOF
    
    echo "✅ Sample CSV created: $DATA_DIR/EURUSD_H4_sample.csv"
    echo ""
    echo "To import in MT4:"
    echo "1. Open MT4 in browser"
    echo "2. Press F2 (History Center)"
    echo "3. Select EURUSD > 240 (H4)"
    echo "4. Click Import"
    echo "5. Browse to file: EURUSD_H4_sample.csv"
    echo "6. Click OK"
    
    echo ""
    echo "For more historical data, download from:"
    echo "• https://www.histdata.com/download-free-forex-data/"
    echo "• https://www.dukascopy.com/swiss/english/marketwatch/historical/"
}

case "$1" in
    start)
        start_web
        ;;
    stop)
        stop_web
        ;;
    restart)
        stop_web
        sleep 2
        start_web
        ;;
    status)
        status_web
        ;;
    download)
        download_csv
        ;;
    *)
        echo "MT4 Web Access - Access MT4 through your web browser"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|download}"
        echo ""
        echo "Commands:"
        echo "  start    - Start web access on port $WEB_PORT"
        echo "  stop     - Stop web access"
        echo "  restart  - Restart web access"
        echo "  status   - Check if services are running"
        echo "  download - Download sample CSV data"
        echo ""
        echo "After starting, open: http://41.150.50.119:$WEB_PORT/vnc.html"
        exit 1
        ;;
esac