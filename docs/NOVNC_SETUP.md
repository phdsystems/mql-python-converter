# NoVNC Setup and Configuration Guide

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Troubleshooting](#troubleshooting)
7. [Security Considerations](#security-considerations)
8. [Advanced Configuration](#advanced-configuration)

## Overview

NoVNC is a browser-based VNC client that allows you to access remote desktop environments through a web browser without requiring any plugins or client software installation. This guide covers setting up NoVNC to access GUI applications running in Docker containers or remote servers.

### Key Features
- **Browser-based**: No client software required
- **HTML5 Canvas**: Modern browser support
- **WebSockets**: Real-time communication
- **Mobile Support**: Works on tablets and phones
- **Clipboard Support**: Copy/paste between local and remote
- **Encryption**: Supports SSL/TLS connections

## Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+ recommended)
- **RAM**: Minimum 2GB, 4GB recommended
- **Disk Space**: 500MB for NoVNC and dependencies
- **Network**: Port 8080 (web) and 5999 (VNC) available

### Software Dependencies
```bash
# Required packages
- Python 3.6+
- Git
- Xvfb (X Virtual Framebuffer)
- x11vnc or TigerVNC server
- Window manager (fluxbox, openbox, or similar)
- WebSockets proxy (included with NoVNC)
```

### Port Requirements
| Port | Service | Description |
|------|---------|-------------|
| 5999 | VNC Server | VNC protocol communication |
| 8080 | Web Server | NoVNC web interface |
| 99 | X11 Display | Virtual display number |

## Installation

### Step 1: Install System Dependencies

```bash
# Update package lists
sudo apt update

# Install X11 and VNC dependencies
sudo apt install -y \
    xvfb \
    x11vnc \
    fluxbox \
    git \
    python3 \
    python3-numpy \
    net-tools \
    nginx

# Install additional utilities
sudo apt install -y \
    wget \
    curl \
    vim \
    htop
```

### Step 2: Clone NoVNC Repository

```bash
# Clone NoVNC from GitHub
cd /home/developer
git clone https://github.com/novnc/noVNC.git

# Clone WebSockets proxy
cd noVNC
git clone https://github.com/novnc/websockify utils/websockify
```

### Step 3: Set Up Virtual Display

```bash
# Create Xvfb startup script
cat > ~/start_xvfb.sh << 'EOF'
#!/bin/bash
export DISPLAY=:99
Xvfb :99 -screen 0 1280x1024x24 -ac +extension GLX +render -noreset &
sleep 2
fluxbox &
EOF

chmod +x ~/start_xvfb.sh
```

### Step 4: Configure VNC Server

```bash
# Create VNC startup script
cat > ~/start_vnc.sh << 'EOF'
#!/bin/bash
export DISPLAY=:99

# Kill any existing VNC servers
killall x11vnc 2>/dev/null

# Start VNC server with password
x11vnc -display :99 \
       -forever \
       -shared \
       -rfbport 5999 \
       -passwd mt4vnc \
       -bg \
       -o /var/log/x11vnc.log
EOF

chmod +x ~/start_vnc.sh
```

### Step 5: Create NoVNC Launcher

```bash
# Create NoVNC startup script
cat > ~/start_novnc.sh << 'EOF'
#!/bin/bash
cd /home/developer/noVNC

# Start NoVNC with WebSockets proxy
./utils/novnc_proxy \
    --vnc localhost:5999 \
    --listen 8080 \
    --web ./ \
    > /var/log/novnc.log 2>&1 &

echo "NoVNC started on http://localhost:8080/vnc.html"
EOF

chmod +x ~/start_novnc.sh
```

## Configuration

### Basic Configuration

1. **Display Resolution**
   ```bash
   # Edit Xvfb command in start_xvfb.sh
   # Format: WIDTHxHEIGHTxDEPTH
   Xvfb :99 -screen 0 1920x1080x24  # Full HD
   Xvfb :99 -screen 0 1280x720x24   # HD
   Xvfb :99 -screen 0 800x600x16    # Low resource
   ```

2. **VNC Password**
   ```bash
   # Generate VNC password file
   x11vnc -storepasswd your_password ~/.vnc/passwd
   
   # Use password file in VNC server
   x11vnc -display :99 -rfbauth ~/.vnc/passwd
   ```

3. **NoVNC Settings**
   ```bash
   # Edit NoVNC default settings
   cd /home/developer/noVNC
   cp vnc.html index.html
   
   # Modify settings in app/ui.js
   # - Default host
   # - Default port
   # - Encryption settings
   ```

### SSL/TLS Configuration

```bash
# Generate self-signed certificate
openssl req -new -x509 -days 365 -nodes \
    -out /home/developer/novnc.pem \
    -keyout /home/developer/novnc.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Start NoVNC with SSL
./utils/novnc_proxy \
    --vnc localhost:5999 \
    --listen 8080 \
    --cert /home/developer/novnc.pem \
    --ssl-only
```

### Authentication Configuration

```bash
# Create token file for multi-user access
cat > /home/developer/tokens.conf << 'EOF'
# token: host:port
user1: localhost:5999
user2: localhost:5998
admin: localhost:5997
EOF

# Start with token authentication
./utils/novnc_proxy \
    --vnc localhost:5999 \
    --listen 8080 \
    --token-plugin TokenFile \
    --token-source /home/developer/tokens.conf
```

## Usage

### Starting Services

```bash
# 1. Start virtual display
~/start_xvfb.sh

# 2. Start VNC server
~/start_vnc.sh

# 3. Start NoVNC web server
~/start_novnc.sh

# 4. Verify services
ps aux | grep -E "(Xvfb|vnc|websockify)"
netstat -tulnp | grep -E "(5999|8080)"
```

### Accessing NoVNC

1. **Local Access**
   ```
   http://localhost:8080/vnc.html
   ```

2. **Remote Access**
   ```
   http://YOUR_SERVER_IP:8080/vnc.html
   ```

3. **Connection Parameters**
   - Host: Leave empty for same host
   - Port: 8080 (automatically handled)
   - Password: Your VNC password
   - Encrypt: Check for SSL connections

### Keyboard and Mouse Controls

| Action | Description |
|--------|-------------|
| **Left Click** | Normal click |
| **Right Click** | Right-click menu |
| **Middle Click** | Ctrl + Left Click |
| **Scroll** | Mouse wheel or touch scroll |
| **Keyboard** | Direct input, special keys via menu |
| **Clipboard** | Use clipboard sidebar |

### Special Key Combinations

Access via Extra Keys menu:
- **Ctrl+Alt+Del**: System menu
- **Alt+Tab**: Switch applications
- **Ctrl+C/V**: Copy/Paste
- **F1-F12**: Function keys
- **Esc**: Escape key

## Troubleshooting

### Common Issues and Solutions

#### 1. Black Screen
```bash
# Check if Xvfb is running
ps aux | grep Xvfb

# Restart display
killall Xvfb
~/start_xvfb.sh

# Check display variable
echo $DISPLAY  # Should be :99
```

#### 2. Connection Refused
```bash
# Check VNC server
netstat -tulnp | grep 5999

# Check firewall
sudo ufw status
sudo ufw allow 8080/tcp
sudo ufw allow 5999/tcp

# Restart VNC
killall x11vnc
~/start_vnc.sh
```

#### 3. Performance Issues
```bash
# Reduce color depth
Xvfb :99 -screen 0 1280x720x16  # 16-bit color

# Disable unnecessary features
x11vnc -display :99 -rfbport 5999 \
       -noxdamage \
       -noxfixes \
       -noxrandr

# Adjust encoding
# In NoVNC settings, use "Tight" or "ZRLE" encoding
```

#### 4. Authentication Failed
```bash
# Regenerate password
x11vnc -storepasswd newpassword ~/.vnc/passwd

# Check password in VNC startup
grep passwd ~/start_vnc.sh

# Clear browser cache and cookies
```

### Debug Mode

```bash
# Enable verbose logging
x11vnc -display :99 -rfbport 5999 -debug

# NoVNC debug mode
./utils/novnc_proxy --vnc localhost:5999 --verbose

# Check logs
tail -f /var/log/x11vnc.log
tail -f /var/log/novnc.log
```

## Security Considerations

### Best Practices

1. **Use Strong Passwords**
   ```bash
   # Generate random password
   openssl rand -base64 12
   ```

2. **Implement SSL/TLS**
   ```bash
   # Always use HTTPS in production
   --cert /path/to/cert.pem --ssl-only
   ```

3. **Restrict Access**
   ```bash
   # Bind to localhost only
   x11vnc -display :99 -localhost -rfbport 5999
   
   # Use SSH tunnel for remote access
   ssh -L 8080:localhost:8080 user@server
   ```

4. **Network Isolation**
   ```bash
   # Use firewall rules
   sudo ufw default deny incoming
   sudo ufw allow from 192.168.1.0/24 to any port 8080
   ```

5. **Regular Updates**
   ```bash
   # Keep NoVNC updated
   cd /home/developer/noVNC
   git pull origin master
   cd utils/websockify
   git pull origin master
   ```

## Advanced Configuration

### Multiple Displays

```bash
# Start multiple virtual displays
Xvfb :99 -screen 0 1280x720x24 &
Xvfb :98 -screen 0 1920x1080x24 &

# Multiple VNC servers
x11vnc -display :99 -rfbport 5999 &
x11vnc -display :98 -rfbport 5998 &

# Configure NoVNC for multiple targets
./utils/novnc_proxy --target-config /path/to/targets.conf
```

### Docker Integration

```dockerfile
# Dockerfile example
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    xvfb x11vnc fluxbox git python3

RUN git clone https://github.com/novnc/noVNC.git /opt/noVNC && \
    git clone https://github.com/novnc/websockify /opt/noVNC/utils/websockify

EXPOSE 8080 5999

CMD ["/start.sh"]
```

### Systemd Service

```ini
# /etc/systemd/system/novnc.service
[Unit]
Description=NoVNC Server
After=network.target

[Service]
Type=simple
User=developer
WorkingDirectory=/home/developer/noVNC
ExecStart=/home/developer/noVNC/utils/novnc_proxy --vnc localhost:5999 --listen 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

### Performance Tuning

```bash
# Optimize VNC settings
x11vnc -display :99 \
       -rfbport 5999 \
       -shared \
       -forever \
       -alwaysshared \
       -permitfiletransfer \
       -ultrafilexfer \
       -threads \
       -ncache 10 \
       -ncache_cr
```

## Conclusion

NoVNC provides a powerful, browser-based solution for remote desktop access. With proper configuration and security measures, it's suitable for both development and production environments. Regular monitoring and updates ensure optimal performance and security.

### Quick Reference Commands

```bash
# Start all services
~/start_xvfb.sh && ~/start_vnc.sh && ~/start_novnc.sh

# Stop all services
killall Xvfb x11vnc websockify

# Check status
ps aux | grep -E "(Xvfb|vnc|websockify)"

# View logs
tail -f /var/log/x11vnc.log
tail -f /var/log/novnc.log
```

### Additional Resources
- [NoVNC GitHub](https://github.com/novnc/noVNC)
- [NoVNC Documentation](https://github.com/novnc/noVNC/wiki)
- [WebSockets Proxy](https://github.com/novnc/websockify)
- [x11vnc Manual](http://www.karlrunge.com/x11vnc/)