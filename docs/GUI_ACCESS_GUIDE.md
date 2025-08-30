# Complete GUI Access and Troubleshooting Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Setup Methods](#setup-methods)
4. [Accessing the GUI](#accessing-the-gui)
5. [Troubleshooting Guide](#troubleshooting-guide)
6. [MT4 Specific Setup](#mt4-specific-setup)
7. [Advanced Configurations](#advanced-configurations)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [FAQ](#faq)

## Quick Start

### One-Command Setup
```bash
# Quick setup script for GUI access
curl -sSL https://raw.githubusercontent.com/your-repo/setup-gui.sh | bash
```

### Manual Quick Setup
```bash
# 1. Start virtual display
Xvfb :99 -screen 0 1280x1024x24 &
export DISPLAY=:99

# 2. Start window manager
fluxbox &

# 3. Start VNC server
x11vnc -display :99 -rfbport 5999 -passwd mt4vnc -forever -shared &

# 4. Start NoVNC
cd ~/noVNC && ./utils/novnc_proxy --vnc localhost:5999 --listen 8080 &

# 5. Access via browser
echo "Open http://localhost:8080/vnc.html in your browser"
```

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│                 Client Browser               │
│              http://localhost:8080           │
└────────────────────┬────────────────────────┘
                     │ HTTP/WebSocket
┌────────────────────▼────────────────────────┐
│              NoVNC Web Server                │
│                 Port 8080                    │
│            (WebSocket to VNC)                │
└────────────────────┬────────────────────────┘
                     │ VNC Protocol
┌────────────────────▼────────────────────────┐
│             VNC Server (x11vnc)              │
│                 Port 5999                    │
│          (Screen capture & input)            │
└────────────────────┬────────────────────────┘
                     │ X11 Protocol
┌────────────────────▼────────────────────────┐
│         Virtual Display (Xvfb :99)           │
│              1280x1024x24                    │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│   Applications (MT4, Chrome, Firefox, etc)   │
│            Running on DISPLAY=:99            │
└─────────────────────────────────────────────┘
```

## Setup Methods

### Method 1: Docker Container (Recommended)

```dockerfile
# Dockerfile.gui
FROM ubuntu:22.04

# Install required packages
RUN apt-get update && apt-get install -y \
    xvfb x11vnc fluxbox \
    wget curl git python3 \
    novnc websockify \
    supervisor

# Setup VNC password
RUN mkdir ~/.vnc && \
    x11vnc -storepasswd mt4vnc ~/.vnc/passwd

# Copy configuration files
COPY supervisord.conf /etc/supervisor/conf.d/

# Expose ports
EXPOSE 5999 8080

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

**supervisord.conf:**
```ini
[supervisord]
nodaemon=true

[program:xvfb]
command=Xvfb :99 -screen 0 1280x1024x24
autorestart=true
priority=100

[program:fluxbox]
command=fluxbox
environment=DISPLAY=":99"
autorestart=true
priority=200

[program:x11vnc]
command=x11vnc -display :99 -rfbport 5999 -rfbauth /root/.vnc/passwd -forever -shared
autorestart=true
priority=300

[program:novnc]
command=/usr/share/novnc/utils/launch.sh --vnc localhost:5999 --listen 8080
autorestart=true
priority=400
```

### Method 2: Systemd Services

```bash
# Create service files
sudo tee /etc/systemd/system/gui-xvfb.service << 'EOF'
[Unit]
Description=X Virtual Framebuffer
After=network.target

[Service]
Type=simple
User=developer
ExecStart=/usr/bin/Xvfb :99 -screen 0 1280x1024x24 -ac +extension GLX +render -noreset
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/gui-vnc.service << 'EOF'
[Unit]
Description=VNC Server
After=gui-xvfb.service
Requires=gui-xvfb.service

[Service]
Type=simple
User=developer
Environment="DISPLAY=:99"
ExecStartPre=/bin/sleep 2
ExecStart=/usr/bin/x11vnc -display :99 -rfbport 5999 -passwd mt4vnc -forever -shared
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/gui-novnc.service << 'EOF'
[Unit]
Description=NoVNC Web Server
After=gui-vnc.service
Requires=gui-vnc.service

[Service]
Type=simple
User=developer
WorkingDirectory=/home/developer/noVNC
ExecStart=/home/developer/noVNC/utils/novnc_proxy --vnc localhost:5999 --listen 8080
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable gui-xvfb gui-vnc gui-novnc
sudo systemctl start gui-xvfb gui-vnc gui-novnc
```

### Method 3: Shell Scripts

```bash
# Create master control script
cat > ~/gui-control.sh << 'EOF'
#!/bin/bash

ACTION=$1
DISPLAY_NUM=99
VNC_PORT=5999
WEB_PORT=8080
VNC_PASSWORD="mt4vnc"

start_xvfb() {
    echo "Starting Xvfb on display :$DISPLAY_NUM..."
    Xvfb :$DISPLAY_NUM -screen 0 1280x1024x24 -ac +extension GLX +render -noreset &
    echo $! > /tmp/xvfb.pid
    sleep 2
}

start_wm() {
    echo "Starting window manager..."
    DISPLAY=:$DISPLAY_NUM fluxbox &
    echo $! > /tmp/fluxbox.pid
    sleep 1
}

start_vnc() {
    echo "Starting VNC server on port $VNC_PORT..."
    DISPLAY=:$DISPLAY_NUM x11vnc -rfbport $VNC_PORT -passwd $VNC_PASSWORD -forever -shared -bg
}

start_novnc() {
    echo "Starting NoVNC on port $WEB_PORT..."
    cd ~/noVNC
    ./utils/novnc_proxy --vnc localhost:$VNC_PORT --listen $WEB_PORT > /tmp/novnc.log 2>&1 &
    echo $! > /tmp/novnc.pid
}

stop_all() {
    echo "Stopping all GUI services..."
    [ -f /tmp/novnc.pid ] && kill $(cat /tmp/novnc.pid) 2>/dev/null
    killall x11vnc 2>/dev/null
    [ -f /tmp/fluxbox.pid ] && kill $(cat /tmp/fluxbox.pid) 2>/dev/null
    [ -f /tmp/xvfb.pid ] && kill $(cat /tmp/xvfb.pid) 2>/dev/null
    rm -f /tmp/*.pid
}

status() {
    echo "=== GUI Services Status ==="
    ps aux | grep -E "(Xvfb|fluxbox|x11vnc|novnc)" | grep -v grep
    echo ""
    echo "=== Port Status ==="
    netstat -tlnp 2>/dev/null | grep -E "($VNC_PORT|$WEB_PORT)"
    echo ""
    echo "=== Access URLs ==="
    echo "NoVNC: http://localhost:$WEB_PORT/vnc.html"
    echo "VNC: localhost:$VNC_PORT (password: $VNC_PASSWORD)"
}

case "$ACTION" in
    start)
        start_xvfb
        start_wm
        start_vnc
        start_novnc
        echo "GUI services started successfully!"
        echo "Access at: http://localhost:$WEB_PORT/vnc.html"
        ;;
    stop)
        stop_all
        echo "GUI services stopped."
        ;;
    restart)
        stop_all
        sleep 2
        $0 start
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
EOF

chmod +x ~/gui-control.sh
```

## Accessing the GUI

### Web Browser Access

1. **Local Machine**
   ```
   http://localhost:8080/vnc.html
   ```

2. **Remote Access (Same Network)**
   ```
   http://192.168.1.100:8080/vnc.html
   ```

3. **Remote Access (Internet)**
   ```
   # Setup SSH tunnel first
   ssh -L 8080:localhost:8080 user@remote-server
   # Then access
   http://localhost:8080/vnc.html
   ```

### VNC Client Access

1. **Install VNC Viewer**
   ```bash
   # Windows: Download from RealVNC, TightVNC, or TigerVNC
   # macOS: brew install --cask vnc-viewer
   # Linux: sudo apt install vncviewer
   ```

2. **Connect**
   ```
   Server: localhost:5999 or localhost::5999
   Password: mt4vnc
   ```

### Direct Application Access

```bash
# Run applications directly on virtual display
DISPLAY=:99 google-chrome http://localhost:8080
DISPLAY=:99 firefox http://localhost:8080
DISPLAY=:99 wine terminal.exe  # For MT4
```

## Troubleshooting Guide

### Problem: Black Screen in Browser

**Symptoms:**
- NoVNC connects but shows black screen
- No applications visible

**Solutions:**
```bash
# 1. Check if Xvfb is running
ps aux | grep Xvfb
# If not running, start it:
Xvfb :99 -screen 0 1280x1024x24 &

# 2. Check if window manager is running
ps aux | grep fluxbox
# If not running:
DISPLAY=:99 fluxbox &

# 3. Restart VNC server
killall x11vnc
DISPLAY=:99 x11vnc -rfbport 5999 -passwd mt4vnc -forever -shared &

# 4. Check display variable
echo $DISPLAY  # Should show :99

# 5. Test with simple application
DISPLAY=:99 xterm &  # Should show terminal window
```

### Problem: Connection Refused

**Symptoms:**
- Cannot connect to http://localhost:8080
- Browser shows "Connection refused"

**Solutions:**
```bash
# 1. Check if NoVNC is running
ps aux | grep novnc
netstat -tlnp | grep 8080

# 2. Check if VNC server is running
netstat -tlnp | grep 5999

# 3. Check firewall
sudo ufw status
sudo ufw allow 8080/tcp
sudo ufw allow 5999/tcp

# 4. Restart all services
~/gui-control.sh restart

# 5. Check logs
tail -f /tmp/novnc.log
tail -f ~/.vnc/*.log
```

### Problem: Slow Performance

**Symptoms:**
- Laggy mouse movement
- Slow screen updates
- High CPU usage

**Solutions:**
```bash
# 1. Reduce color depth
killall Xvfb
Xvfb :99 -screen 0 1280x720x16 &  # 16-bit instead of 24-bit

# 2. Optimize VNC encoding
# In NoVNC settings, change encoding to:
# - Tight (best compression)
# - ZRLE (good for slow networks)

# 3. Disable unnecessary features
x11vnc -display :99 -rfbport 5999 \
    -noxdamage \    # Disable X DAMAGE extension
    -noxfixes \     # Disable XFIXES
    -noxrandr \     # Disable XRANDR
    -nowf \         # Disable wireframing
    -nocursor       # Don't show remote cursor

# 4. Limit frame rate
x11vnc -display :99 -rfbport 5999 -defer 50  # 50ms delay

# 5. Use lighter window manager
# Replace fluxbox with openbox or twm
DISPLAY=:99 openbox &
```

### Problem: Authentication Failed

**Symptoms:**
- Password prompt appears repeatedly
- "Authentication failed" error

**Solutions:**
```bash
# 1. Reset VNC password
x11vnc -storepasswd newpassword ~/.vnc/passwd

# 2. Start VNC with new password
x11vnc -display :99 -rfbport 5999 -rfbauth ~/.vnc/passwd

# 3. Use no authentication (development only)
x11vnc -display :99 -rfbport 5999 -nopw

# 4. Clear browser cache
# Chrome: Ctrl+Shift+Delete
# Firefox: Ctrl+Shift+Delete

# 5. Check password in connection URL
# Correct format:
http://localhost:8080/vnc.html?password=mt4vnc
```

### Problem: Applications Not Visible

**Symptoms:**
- Desktop appears but applications don't show
- Applications crash on startup

**Solutions:**
```bash
# 1. Check DISPLAY variable for application
DISPLAY=:99 echo $DISPLAY

# 2. Test with simple application
DISPLAY=:99 xclock  # Should show clock
DISPLAY=:99 xeyes   # Should show eyes

# 3. Check for missing libraries
ldd /path/to/application | grep "not found"

# 4. Install missing dependencies
sudo apt install -y libgtk-3-0 libx11-xcb1 libxss1

# 5. Check application logs
DISPLAY=:99 application_name 2>&1 | tee app.log

# 6. Use strace to debug
DISPLAY=:99 strace -e trace=open,access application_name
```

## MT4 Specific Setup

### Running MT4 with GUI Access

```bash
# Prerequisites
sudo apt install -y wine wine32 wine64

# Start GUI services
~/gui-control.sh start

# Run MT4
DISPLAY=:99 wine ~/mt4/terminal.exe /portable

# Or using the MT4 script
DISPLAY=:99 ./mt4_gui.sh
```

### MT4 Connection Issues

```bash
# Wine network fix for MT4
# Error: "No connection" in MT4

# 1. Check Wine network
DISPLAY=:99 wine ipconfig

# 2. Reset Wine network
wineserver -k
rm -rf ~/.wine/drive_c/windows/system32/drivers/etc/

# 3. Reinstall Wine mono
sudo apt install --reinstall wine-mono

# 4. Use specific Wine version
sudo apt install wine-stable=5.0.3~focal

# 5. Run with debug output
WINEDEBUG=+winsock DISPLAY=:99 wine terminal.exe
```

### MT4 Display Issues

```bash
# Fix font rendering
winetricks corefonts

# Fix graphics issues
winetricks d3dx9 vcrun2019

# Optimize for MT4
cat > ~/.wine/user.reg << 'EOF'
[Software\\Wine\\Direct3D]
"VideoMemorySize"="512"
"UseGLSL"="enabled"
"OffscreenRenderingMode"="backbuffer"
EOF
```

## Advanced Configurations

### Multiple Displays

```bash
# Run multiple virtual displays for different applications
Xvfb :99 -screen 0 1280x1024x24 &  # Main display
Xvfb :98 -screen 0 1920x1080x24 &  # Secondary display

# Different VNC servers
x11vnc -display :99 -rfbport 5999 &
x11vnc -display :98 -rfbport 5998 &

# Access different displays
DISPLAY=:99 application1 &
DISPLAY=:98 application2 &
```

### SSL/TLS Security

```bash
# Generate SSL certificate
openssl req -x509 -nodes -newkey rsa:2048 \
    -keyout novnc.key -out novnc.crt -days 365 \
    -subj "/CN=localhost"

# Combine into single file
cat novnc.key novnc.crt > novnc.pem

# Start NoVNC with SSL
./utils/novnc_proxy --vnc localhost:5999 \
    --listen 8080 --cert novnc.pem --ssl-only

# Access via HTTPS
https://localhost:8080/vnc.html
```

### Performance Monitoring

```bash
# Monitor script
cat > ~/monitor-gui.sh << 'EOF'
#!/bin/bash

while true; do
    clear
    echo "=== GUI Performance Monitor ==="
    echo "Date: $(date)"
    echo ""
    
    echo "=== Process Status ==="
    ps aux | grep -E "(Xvfb|vnc|novnc)" | grep -v grep | awk '{print $11, "CPU:"$3"%", "MEM:"$4"%"}'
    echo ""
    
    echo "=== Network Connections ==="
    netstat -tn | grep -E "(5999|8080)"
    echo ""
    
    echo "=== Disk Usage ==="
    df -h /tmp | tail -n1
    echo ""
    
    echo "=== Memory Usage ==="
    free -h | grep -E "(Mem|Swap)"
    
    sleep 5
done
EOF

chmod +x ~/monitor-gui.sh
```

### Automated Screenshots

```bash
# Screenshot script
cat > ~/auto-screenshot.sh << 'EOF'
#!/bin/bash

SCREENSHOT_DIR=~/screenshots
mkdir -p $SCREENSHOT_DIR

while true; do
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    DISPLAY=:99 import -window root $SCREENSHOT_DIR/screen_$TIMESTAMP.png
    
    # Keep only last 100 screenshots
    ls -t $SCREENSHOT_DIR/*.png | tail -n +101 | xargs rm -f 2>/dev/null
    
    sleep 300  # Screenshot every 5 minutes
done
EOF

chmod +x ~/auto-screenshot.sh
```

## Monitoring and Maintenance

### Health Check Script

```bash
#!/bin/bash
# healthcheck.sh

check_service() {
    SERVICE=$1
    PORT=$2
    
    if pgrep -f "$SERVICE" > /dev/null; then
        echo "✓ $SERVICE is running"
    else
        echo "✗ $SERVICE is not running"
        return 1
    fi
    
    if [ ! -z "$PORT" ]; then
        if netstat -tlnp 2>/dev/null | grep -q ":$PORT"; then
            echo "  Port $PORT is listening"
        else
            echo "  Port $PORT is not listening"
            return 1
        fi
    fi
    
    return 0
}

echo "=== GUI Services Health Check ==="
check_service "Xvfb :99" ""
check_service "x11vnc" "5999"
check_service "novnc" "8080"
check_service "fluxbox" ""

# Test display
DISPLAY=:99 xdpyinfo > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Display :99 is accessible"
else
    echo "✗ Display :99 is not accessible"
fi

# Test web access
curl -s http://localhost:8080 > /dev/null
if [ $? -eq 0 ]; then
    echo "✓ NoVNC web interface is accessible"
else
    echo "✗ NoVNC web interface is not accessible"
fi
```

### Log Rotation

```bash
# /etc/logrotate.d/gui-services
/var/log/x11vnc.log /tmp/novnc.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 644 developer developer
    postrotate
        killall -USR1 x11vnc 2>/dev/null || true
    endscript
}
```

## FAQ

### Q: Can I change the resolution after starting?

**A:** Yes, use xrandr:
```bash
DISPLAY=:99 xrandr --size 1920x1080
# Or dynamically:
DISPLAY=:99 xrandr --fb 1920x1080
```

### Q: How do I enable audio?

**A:** Install PulseAudio:
```bash
sudo apt install pulseaudio
DISPLAY=:99 pulseaudio --start
# In application:
DISPLAY=:99 PULSE_SERVER=localhost application
```

### Q: Can I use GPU acceleration?

**A:** Yes, with VirtualGL:
```bash
sudo apt install virtualgl
vglrun -d :99 glxgears
```

### Q: How do I share clipboard?

**A:** NoVNC has built-in clipboard support:
1. Click clipboard icon in NoVNC toolbar
2. Paste text in the textarea
3. Text is available in remote session

### Q: Can multiple users connect?

**A:** Yes, x11vnc supports shared connections:
```bash
x11vnc -display :99 -shared -forever
```

### Q: How do I record sessions?

**A:** Use vnc2flv or ffmpeg:
```bash
# Record with ffmpeg
ffmpeg -f x11grab -r 25 -s 1280x1024 -i :99 output.mp4

# Record VNC session
vncrec -record session.vnc localhost:5999
```

### Q: What about security?

**A:** Implement these measures:
1. Use SSL/TLS for NoVNC
2. Strong VNC passwords
3. Firewall rules
4. SSH tunneling for remote access
5. Regular security updates

## Conclusion

This comprehensive guide covers all aspects of GUI access setup, from basic installation to advanced troubleshooting. The modular approach allows you to choose the method that best fits your needs, whether it's for development, testing, or production use.

### Quick Commands Reference

```bash
# Start everything
~/gui-control.sh start

# Check status
~/gui-control.sh status

# Take screenshot
DISPLAY=:99 import -window root screenshot.png

# Open browser
DISPLAY=:99 google-chrome http://localhost:8080

# Run MT4
DISPLAY=:99 wine terminal.exe

# Monitor performance
~/monitor-gui.sh

# Health check
~/healthcheck.sh
```

### Support Resources
- [NoVNC Issues](https://github.com/novnc/noVNC/issues)
- [x11vnc Documentation](http://www.karlrunge.com/x11vnc/docs.html)
- [Xvfb Manual](https://www.x.org/releases/X11R7.6/doc/man/man1/Xvfb.1.xhtml)
- [Wine Application Database](https://appdb.winehq.org/)