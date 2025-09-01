# Docker Configuration Variants Guide

## Overview
This project offers multiple Docker configurations optimized for different use cases. All configurations implement security best practices with non-root user execution.

## Configuration Comparison

| Variant | Use Case | Image Size | Features | Best For |
|---------|----------|------------|----------|----------|
| **Standard** | Development | ~1.2GB | Full Python env, all libraries | Local development |
| **MT4** | Trading | ~3.5GB | Wine, MT4, Python bridge | MT4 integration |
| **Slim** | Production | ~600MB | Minimal dependencies | Cloud deployment |
| **Secure** | Production | ~1.5GB | Hardened, non-root, limited privileges | Production systems |
| **NoVNC** | Remote | ~4GB | Browser GUI, full MT4 | Remote access |

## Detailed Configurations

### 1. Standard Configuration (`docker-compose.yml`)
**File**: `Dockerfile`
```bash
docker-compose up --build
```
- Full Python development environment
- All optimization libraries included
- Hot-reload for development
- Volume mounts for code editing

### 2. MT4 Configuration (`docker-compose.mt4.yml`)
**File**: `Dockerfile.mt4`
```bash
docker-compose -f docker-compose.mt4.yml up --build
```
- Wine for Windows compatibility
- MetaTrader 4 installation
- Python-MT4 bridge
- Expert Advisor support

### 3. Slim Configuration (`docker-compose.slim.yml`)
**File**: `Dockerfile.mt4-slim`
```bash
docker-compose -f docker-compose.slim.yml up --build
```
- Minimal base image
- Only essential dependencies
- Reduced attack surface
- Faster startup times
- Lower memory footprint

### 4. Secure Configuration (`docker-compose.secure.yml`)
**File**: `Dockerfile.secure`
```bash
docker-compose -f docker-compose.secure.yml up --build
```
- Non-root user execution (UID 1000)
- Read-only root filesystem
- No capability additions
- Security scanning integrated
- Secrets management support

### 5. NoVNC Configuration (`docker-compose-novnc.yml`)
**File**: `Dockerfile.novnc`
```bash
docker-compose -f docker-compose-novnc.yml up --build
# Access at http://localhost:6080
```
- Web-based VNC access
- No client software needed
- Full GUI environment
- Fluxbox window manager
- SSL/TLS support optional

## Security Features

All configurations include:
- **Non-root execution**: Containers run as user `developer` (UID 1000)
- **Minimal privileges**: Only necessary capabilities granted
- **Health checks**: Automatic monitoring and restart
- **Resource limits**: CPU and memory constraints
- **Volume permissions**: Proper ownership and access control

## Choosing the Right Configuration

### For Development
Use **Standard** configuration:
- Fast iteration cycles
- All debugging tools available
- Local file system access

### For MT4 Integration
Use **MT4** or **NoVNC** configuration:
- MT4: Headless or VNC access
- NoVNC: Browser-based GUI

### For Production Python Services
Use **Slim** configuration:
- Minimal attack surface
- Fast deployment
- Lower resource usage

### For Production with MT4
Use **Secure** configuration:
- Hardened security
- Audit logging
- Compliance ready

## Resource Requirements

| Configuration | Min RAM | Recommended RAM | CPU Cores | Disk Space |
|--------------|---------|-----------------|-----------|------------|
| Standard | 1GB | 2GB | 1 | 5GB |
| MT4 | 2GB | 4GB | 2 | 10GB |
| Slim | 512MB | 1GB | 1 | 2GB |
| Secure | 1GB | 2GB | 1 | 5GB |
| NoVNC | 2GB | 4GB | 2 | 12GB |

## Quick Start Commands

```bash
# Build all images
for variant in "" ".mt4" ".mt4-slim" ".secure" ".novnc"; do
  if [ -z "$variant" ]; then
    docker build -t mql-python-converter:latest .
  else
    docker build -f Dockerfile${variant} -t mql-python-converter:${variant#.} .
  fi
done

# Run specific variant
docker-compose -f docker-compose.slim.yml up -d  # Example: slim variant

# Check status
docker ps
docker logs <container-name>

# Clean up
./docker-cleanup.sh
```

## Environment Variables

Common environment variables across all configurations:
```bash
# User configuration
USER_ID=1000
GROUP_ID=1000
USERNAME=developer

# VNC settings (MT4/NoVNC only)
VNC_PASSWORD=mt4vnc
VNC_RESOLUTION=1280x720

# Resource limits
CPU_LIMIT=2
MEMORY_LIMIT=4G

# Ports (customize as needed)
API_PORT=8000
VNC_PORT=5901
NOVNC_PORT=6080
```

## Migration Guide

### From Standalone Python to Docker
1. Choose Standard configuration
2. Mount your code directory
3. Install additional dependencies if needed

### From Windows MT4 to Docker
1. Choose MT4 or NoVNC configuration
2. Copy your EA files to mounted volume
3. Configure MT4 settings via VNC

### From Development to Production
1. Start with Standard for development
2. Test with Secure configuration
3. Deploy with Slim for Python-only
4. Use Secure for MT4 production needs

## Troubleshooting

### Container won't start
- Check Docker daemon: `systemctl status docker`
- Verify ports available: `netstat -tulpn | grep <port>`
- Review logs: `docker logs <container>`

### Permission denied errors
- Ensure USER_ID matches host: `id -u`
- Fix ownership: `chown -R 1000:1000 ./data`

### MT4 not connecting
- Check Wine status: `docker exec <container> wineserver -p`
- Verify network settings in MT4
- Review firewall rules

## Support

For issues specific to each configuration:
- Check the relevant Dockerfile for build details
- Review docker-compose file for runtime settings
- Consult logs for diagnostic information