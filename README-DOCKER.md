# Docker MT4 Setup Guide

## Overview
This setup provides a containerized MetaTrader 4 environment with VNC access, Python integration, and proper process management.

## Quick Start

### 1. Prerequisites
- Docker installed and running
- Docker Compose installed
- User added to docker group (or use sudo)

### 2. Start the Container

#### Option A: Using Docker Compose (Recommended)
```bash
# Start services
sudo docker-compose -f docker-compose.safe.yml up -d

# View logs
sudo docker-compose -f docker-compose.safe.yml logs -f

# Stop services
sudo docker-compose -f docker-compose.safe.yml down
```

#### Option B: Using the Safe Run Script
```bash
# Make scripts executable
chmod +x docker-safe-run.sh docker-cleanup.sh

# Run the container
sudo ./docker-safe-run.sh
```

### 3. Access Services

- **noVNC Web Interface**: http://localhost:6080
  - No client installation required
  - Access MT4 GUI from any browser
  
- **VNC Client**: localhost:5901
  - Password: `mt4vnc`
  - Use any VNC client (RealVNC, TightVNC, etc.)
  
- **Python API**: http://localhost:8000
  - REST API for MT4 integration
  
- **Data Bridge**: localhost:9090
  - Direct socket connection for MT4-Python communication

## File Structure

```
mql-python-converter/
├── Dockerfile.mt4-safe          # Main Docker image definition
├── docker-compose.safe.yml      # Docker Compose configuration
├── docker-entrypoint.sh         # Container startup script
├── healthcheck.sh               # Health check script
├── supervisord-safe.conf        # Process supervisor configuration
├── docker-safe-run.sh           # Standalone container runner
├── docker-cleanup.sh            # Cleanup script
├── test-docker-setup.sh         # Setup verification script
└── .env                         # Environment variables
```

## Features

### 1. Process Management
- Supervisord manages all services
- Automatic restart on failure
- Proper signal handling for graceful shutdown
- Health checks for service monitoring

### 2. VNC Access
- X11VNC server for remote desktop
- noVNC for browser-based access
- Configurable resolution and password
- Fluxbox window manager

### 3. Wine/MT4 Integration
- Wine configured for Windows 10 compatibility
- MT4 installation support
- Persistent Wine prefix in Docker volume
- Expert Advisor support

### 4. Python Integration
- Python API server for MT4 communication
- WebSocket support for real-time data
- REST endpoints for commands
- Data persistence in mounted volumes

## Configuration

### Environment Variables (.env)
```bash
# VNC Configuration
VNC_PASSWORD=mt4vnc
VNC_RESOLUTION=1280x720

# Ports
NOVNC_PORT=6080
VNC_PORT=5901
API_PORT=8000
BRIDGE_PORT=9090

# Resource Limits
CPU_LIMIT=2
MEMORY_LIMIT=4G
```

### Volume Mounts
- `./src`: Application source code
- `./server`: Python server code
- `./logs`: Application logs
- `./data`: Persistent data
- `mt4-wine-data`: Wine prefix (persistent)

## Commands

### Build Image
```bash
sudo docker build -f Dockerfile.mt4-safe -t mt4-converter-safe .
```

### Run Tests
```bash
./test-docker-setup.sh
```

### View Logs
```bash
# All services
sudo docker-compose -f docker-compose.safe.yml logs -f

# Specific service
sudo docker logs mt4-safe

# Supervisor logs
sudo docker exec mt4-safe tail -f /app/logs/supervisord.log
```

### Execute Commands in Container
```bash
# Open shell
sudo docker exec -it mt4-safe bash

# Check Wine status
sudo docker exec mt4-safe su - wineuser -c "wineserver -p0"

# Check running processes
sudo docker exec mt4-safe ps aux
```

### Cleanup
```bash
# Stop and remove containers
sudo ./docker-cleanup.sh

# Remove volumes (WARNING: deletes data)
sudo docker volume rm mql-python-converter_mt4-wine

# Remove images
sudo docker rmi mt4-converter-safe
```

## Troubleshooting

### Docker Permission Issues
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Or use sudo with all docker commands
sudo docker-compose -f docker-compose.safe.yml up
```

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :6080

# Kill process
sudo kill -9 <PID>

# Or change port in .env file
```

### Container Won't Start
```bash
# Check logs
sudo docker logs mt4-safe

# Check Docker daemon
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker
```

### VNC Connection Refused
```bash
# Check if X11VNC is running
sudo docker exec mt4-safe ps aux | grep x11vnc

# Restart supervisor services
sudo docker exec mt4-safe supervisorctl restart all
```

### Wine/MT4 Issues
```bash
# Reset Wine prefix
sudo docker exec -u wineuser mt4-safe wineboot --init

# Check Wine version
sudo docker exec mt4-safe wine --version

# Install MT4 manually
sudo docker exec -u wineuser mt4-safe wine /path/to/mt4setup.exe
```

## Security Notes

1. **VNC Password**: Change the default password in production
2. **Port Exposure**: Use firewall rules to restrict access
3. **Resource Limits**: Adjust CPU/memory limits as needed
4. **Volume Permissions**: Ensure proper file permissions

## Performance Tuning

1. **Shared Memory**: Increase for better GUI performance
   ```yaml
   shm_size: '4gb'
   ```

2. **CPU Allocation**: Adjust based on workload
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '4'
   ```

3. **Wine Debug**: Disable for better performance
   ```bash
   WINEDEBUG=-all
   ```

## Support

For issues or questions:
1. Check container logs
2. Verify Docker setup with test script
3. Ensure all required files are present
4. Check system resources (disk, memory, CPU)