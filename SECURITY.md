# Security Policy

## Overview
This project implements defense-in-depth security practices across all Docker configurations and Python code.

## Security Features

### Container Security

#### Non-Root Execution
All Docker containers run as non-privileged user `developer` (UID 1000):
- No root access inside containers
- Minimal capability set
- Read-only root filesystem where possible

```dockerfile
# Example from Dockerfiles
RUN useradd -m -u 1000 -s /bin/bash developer
USER developer
```

#### Image Security
- Base images regularly updated
- Multi-stage builds to minimize attack surface
- No unnecessary packages or tools
- Security scanning with Docker Scout

#### Network Security
- Minimal port exposure
- Internal networks for service communication
- Optional TLS/SSL for VNC connections
- API authentication when enabled

### Code Security

#### Python Security
- Input validation on all user data
- Secure file handling with path sanitization
- No execution of user-supplied code
- Dependencies regularly updated

#### MT4 Bridge Security
- Isolated Wine environment
- Restricted file system access
- Communication via secure sockets
- No direct internet access from MT4

### Data Security

#### Volume Permissions
```bash
# Ensure proper ownership
chown -R 1000:1000 ./data
chmod 750 ./data

# Sensitive files
chmod 600 .env
```

#### Environment Variables
- Secrets never hardcoded
- `.env` file for configuration
- Docker secrets support in production

## Security Best Practices

### For Development
1. Use the standard configuration with volume mounts
2. Keep development isolated from production
3. Regular dependency updates
4. Code review all changes

### For Production

#### Use Secure or Slim Configurations
```bash
# Secure configuration
docker-compose -f docker-compose.secure.yml up -d

# Slim configuration (minimal attack surface)
docker-compose -f docker-compose.slim.yml up -d
```

#### Implement Access Controls
```yaml
# docker-compose.secure.yml example
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
  restart_policy:
    condition: on-failure
    max_attempts: 3
```

#### Regular Updates
```bash
# Update base images
docker pull python:3.11-slim
docker-compose build --no-cache

# Update Python dependencies
pip-audit
pip list --outdated
```

## Vulnerability Reporting

### Reporting Process
1. **DO NOT** create public issues for security vulnerabilities
2. Email security concerns to the maintainers
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fixes if any

### Response Timeline
- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Fix Timeline**: Based on severity
  - Critical: 24-48 hours
  - High: 1 week
  - Medium: 2 weeks
  - Low: Next release

## Security Checklist

### Before Deployment
- [ ] Change default VNC password
- [ ] Update all dependencies
- [ ] Run security scan on images
- [ ] Configure firewall rules
- [ ] Set resource limits
- [ ] Enable logging and monitoring
- [ ] Backup configuration
- [ ] Test restore procedures

### Container Hardening
```bash
# Run security scan
docker scout cves mql-python-converter:latest

# Check for vulnerabilities
docker scan mql-python-converter:latest

# Verify non-root user
docker run --rm mql-python-converter:latest whoami
# Should output: developer

# Check capabilities
docker run --rm --cap-drop=ALL mql-python-converter:latest
```

### Network Hardening
```bash
# Restrict port access with firewall
ufw allow from 192.168.1.0/24 to any port 6080
ufw deny 6080

# Use internal networks
docker network create --internal mt4-internal
```

## Compliance

### Standards
- CIS Docker Benchmark compliance
- OWASP best practices for web APIs
- PCI DSS guidelines for financial data

### Audit Logging
All configurations support audit logging:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    labels: "service,version"
```

## Security Tools

### Recommended Security Tools
- **Docker Scout**: Vulnerability scanning
- **Trivy**: Container security scanner
- **pip-audit**: Python dependency audit
- **Bandit**: Python code security linter

### Running Security Scans
```bash
# Install security tools
pip install pip-audit bandit safety

# Audit Python dependencies
pip-audit

# Scan Python code
bandit -r src/

# Check known vulnerabilities
safety check

# Scan Docker images
docker scout cves mql-python-converter:latest
```

## Incident Response

### In Case of Breach
1. Isolate affected containers
2. Preserve logs for analysis
3. Rotate all credentials
4. Apply security patches
5. Document lessons learned

### Recovery Procedures
```bash
# Stop compromised container
docker stop <container-id>

# Backup for forensics
docker commit <container-id> compromised-backup

# Clean rebuild
docker-compose down
docker system prune -a
docker-compose build --no-cache
docker-compose up -d
```

## Security Updates

### Stay Informed
- Monitor GitHub security advisories
- Subscribe to Docker security updates
- Track Python security announcements
- Review dependency updates weekly

### Update Schedule
- **Critical updates**: Immediate
- **Security patches**: Within 48 hours
- **Regular updates**: Weekly
- **Major upgrades**: Quarterly

## Contact

For security concerns, contact the maintainers directly.
Do not post security issues publicly.