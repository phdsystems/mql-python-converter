# MT4 NoVNC Docker Container

Complete MT4 trading terminal with web-based access through NoVNC, all bundled in a single Docker container.

## Features

- **All-in-One Container**: Wine, MT4, VNC server, and NoVNC web interface
- **Web-Based Access**: Access MT4 GUI directly from your browser at http://localhost:6080
- **Process Isolation**: All processes run in the same namespace (no EPERM errors)
- **Automatic Startup**: Supervisor manages all services automatically
- **Health Monitoring**: Built-in health checks for all components
- **Persistent Data**: MT4 data and configurations persist across container restarts

## Quick Start

### 1. Build the Docker Image

```bash
docker-compose -f docker-compose-novnc.yml build
```

### 2. Start the Container

```bash
docker-compose -f docker-compose-novnc.yml up -d
```

### 3. Access MT4

Open your browser and navigate to:
- **Web Interface**: http://localhost:6080
- **VNC Password**: mt4vnc (if prompted)

### 4. Check Container Health

```bash
docker exec mt4-novnc /usr/local/bin/healthcheck.sh
```

## Container Management

### View Logs
```bash
# All logs
docker-compose -f docker-compose-novnc.yml logs -f

# Specific service logs
docker exec mt4-novnc tail -f /var/log/supervisor/mt4.log
docker exec mt4-novnc tail -f /var/log/supervisor/novnc.log
```

### Stop Container
```bash
docker-compose -f docker-compose-novnc.yml down
```

### Restart Container
```bash
docker-compose -f docker-compose-novnc.yml restart
```

### Access Container Shell
```bash
docker exec -it mt4-novnc bash
```

### Monitor Services
```bash
docker exec mt4-novnc supervisorctl status
```

## Directory Structure

```
/home/mt4user/
├── mt4/                  # MT4 installation directory
│   ├── terminal.exe      # MT4 executable
│   ├── config/           # Configuration files
│   └── MQL4/             # Expert Advisors, Scripts, Indicators
├── shared/               # Shared directory (mounted from host)
└── .wine/                # Wine prefix
```

## Volumes

The container uses these mounted volumes:
- `./mt4-data`: MT4 MQL4 directory (Expert Advisors, Scripts, etc.)
- `./mt4-logs`: Supervisor logs
- `./shared`: Shared directory for file exchange

## Environment Variables

Configure these in docker-compose-novnc.yml:
- `VNC_PASSWORD`: VNC access password (default: mt4vnc)
- `NOVNC_PORT`: NoVNC web port (default: 6080)
- `VNC_PORT`: VNC server port (default: 5999)
- `WINEDEBUG`: Wine debug level (default: -all)

## Ports

- **6080**: NoVNC web interface
- **5999**: VNC server (for VNC client access)

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose -f docker-compose-novnc.yml logs

# Verify build
docker-compose -f docker-compose-novnc.yml build --no-cache
```

### MT4 Not Running
```bash
# Check MT4 process
docker exec mt4-novnc pgrep -f terminal.exe

# Check Wine errors
docker exec mt4-novnc tail -f /var/log/supervisor/mt4.err
```

### Cannot Access Web Interface
```bash
# Check NoVNC status
docker exec mt4-novnc supervisorctl status novnc

# Check port binding
docker ps | grep 6080
```

### Performance Issues
```bash
# Increase resources in docker-compose-novnc.yml
# Adjust CPU and memory limits under deploy.resources
```

## Security Notes

- Change the default VNC password in production
- Use HTTPS proxy for web access in production
- Restrict port access with firewall rules
- Run container with limited privileges when possible

## Advanced Configuration

### Custom MT4 Server
Place your server configuration in:
```
server/mt4-terminal/config/servers.ini
```

### Install Expert Advisors
Copy .ex4/.mq4 files to:
```
./mt4-data/Experts/
```

### Custom Indicators
Copy indicator files to:
```
./mt4-data/Indicators/
```

## Benefits Over Standalone Setup

1. **No Permission Issues**: All processes run in the same container namespace
2. **Easy Deployment**: Single command to start everything
3. **Web Access**: No need for VNC client installation
4. **Portable**: Runs on any system with Docker
5. **Isolated**: No system-wide Wine installation needed
6. **Manageable**: Supervisor handles process lifecycle

## Support

For issues or questions:
1. Check container health: `docker exec mt4-novnc /usr/local/bin/healthcheck.sh`
2. Review logs: `docker-compose -f docker-compose-novnc.yml logs`
3. Inspect supervisor: `docker exec mt4-novnc supervisorctl status`