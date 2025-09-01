# Docker Setup Guide

## Overview
This project provides multiple Docker configurations for different use cases:
- **Standard**: Basic Python environment for MQL/Pine Script conversion
- **MT4**: Full MetaTrader 4 integration with Wine
- **Slim**: Lightweight version with minimal dependencies
- **Secure**: Security-hardened with non-root user execution
- **NoVNC**: Browser-based GUI access for MT4

All configurations run with non-root users for enhanced security.

## Quick Start

### 1. Prerequisites
- Docker installed and running
- Docker Compose installed
- User added to docker group (or use sudo)

### 2. Start the Container

#### Option A: Using Docker Compose (Recommended)
```bash
# Start services
docker-compose -f docker-compose.safe.yml up -d

# View logs
docker-compose -f docker-compose.safe.yml logs -f

# Stop services
docker-compose -f docker-compose.safe.yml down
```

#### Option B: Using the Safe Run Script
```bash
# Make scripts executable
chmod +x docker-safe-run.sh docker-cleanup.sh

# Run the container
./docker-safe-run.sh
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

## Docker Configurations

### Available Dockerfiles
- `Dockerfile` - Standard Python environment with all dependencies
- `Dockerfile.mt4` - MetaTrader 4 with Wine integration
- `Dockerfile.mt4-safe` - Security-hardened MT4 setup (legacy)
- `Dockerfile.mt4-slim` - Lightweight MT4 configuration
- `Dockerfile.novnc` - MT4 with web-based VNC access
- `Dockerfile.secure` - Production-ready secure configuration

### Docker Compose Files
- `docker-compose.yml` - Standard development setup
- `docker-compose.mt4.yml` - MT4 integration setup
- `docker-compose.safe.yml` - Secure MT4 configuration
- `docker-compose.slim.yml` - Minimal resource usage
- `docker-compose.secure.yml` - Production security setup
- `docker-compose-novnc.yml` - Browser-based GUI access

### Support Scripts
- `docker-entrypoint.sh` - Container initialization
- `docker-safe-run.sh` - Secure container launcher
- `docker-cleanup.sh` - Clean up containers and volumes
- `mt4-docker.sh` - MT4-specific launcher
- `safe-docker.sh` - Security-focused launcher
- `setup-docker-env.sh` - Environment setup helper

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

### Build Images

```bash
# Standard Python environment
docker build -t mql-python-converter:latest .

# MT4 with Wine
docker build -f Dockerfile.mt4 -t mql-python-converter:mt4 .

# Secure configuration
docker build -f Dockerfile.secure -t mql-python-converter:secure .

# Slim version
docker build -f Dockerfile.mt4-slim -t mql-python-converter:slim .

# NoVNC for browser access
docker build -f Dockerfile.novnc -t mql-python-converter:novnc .
```

### Run Tests
```bash
./test-docker-setup.sh
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.safe.yml logs -f

# Specific service  
docker logs mt4-safe

# Supervisor logs
sudo docker exec mt4-safe tail -f /app/logs/supervisord.log
```

### Execute Commands in Container
```bash
# Open shell
docker exec -it mt4-safe bash

# Check Wine status (for MT4 configurations)
docker exec mt4-safe su - developer -c "wineserver -p0"

# Check running processes
docker exec mt4-safe ps aux
```

### Cleanup
```bash
# Stop and remove containers
./docker-cleanup.sh

# Remove volumes (WARNING: deletes data)
docker volume rm mql-python-converter_mt4-wine-data

# Remove images
docker rmi mql-python-converter:latest
docker rmi mql-python-converter:mt4
docker rmi mql-python-converter:secure
docker rmi mql-python-converter:slim
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
docker exec -u developer mt4-safe wineboot --init

# Check Wine version
sudo docker exec mt4-safe wine --version

# Install MT4 manually
docker exec -u developer mt4-safe wine /path/to/mt4setup.exe
```

## Security Notes

1. **Non-Root User**: All containers run as non-root user `developer` (UID 1000) for enhanced security
2. **VNC Password**: Change the default password in production
3. **Port Exposure**: Use firewall rules to restrict access
4. **Resource Limits**: Adjust CPU/memory limits as needed
5. **Volume Permissions**: Ensure proper file permissions match container user (UID 1000)

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