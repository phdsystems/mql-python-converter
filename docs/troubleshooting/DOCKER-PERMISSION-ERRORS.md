# Docker Permission Errors (EPERM)

## Problem

When running the Docker container, you may encounter permission errors like:

```
Error: kill EPERM
    at process.kill (node:internal/process/per_thread:281:13)
    ...
    errno: -1,
    code: 'EPERM',
    syscall: 'kill'
```

## Root Cause

The container was hardcoded to use a specific user ("wineuser") with UID/GID 1000, which didn't match the host user's UID/GID. This mismatch causes permission issues when:
- The container tries to access files mounted from the host
- Processes try to interact with each other across the container boundary
- File ownership conflicts occur between host and container

## Solution

The configuration has been updated to dynamically use the host user's UID/GID at build time.

### Key Changes Made

1. **Dockerfile.mt4-safe** now accepts build arguments:
   ```dockerfile
   ARG USER_ID=1000
   ARG GROUP_ID=1000
   ARG USERNAME=wineuser
   ```

2. **docker-compose.safe.yml** passes host UID/GID:
   ```yaml
   build:
     args:
       USER_ID: ${USER_ID:-1000}
       GROUP_ID: ${GROUP_ID:-1000}
       USERNAME: ${CONTAINER_USER:-wineuser}
   ```

3. **Environment variables** in `.env`:
   ```bash
   USER_ID=1000
   GROUP_ID=1000
   CONTAINER_USER=developer
   ```

### How to Fix

1. **Run the setup script** to automatically configure your environment:
   ```bash
   ./setup-docker-env.sh
   ```
   This script will:
   - Detect your current user's UID and GID
   - Create/update the `.env` file with correct values
   - Set the container username to match your host username

2. **Rebuild the container** with the new configuration:
   ```bash
   sudo docker-compose -f docker-compose.safe.yml build --no-cache
   ```

3. **Run the container**:
   ```bash
   sudo docker-compose -f docker-compose.safe.yml up -d
   ```

### Manual Configuration

If you prefer to configure manually, create a `.env` file:

```bash
# Get your user's UID and GID
echo "USER_ID=$(id -u)" >> .env
echo "GROUP_ID=$(id -g)" >> .env
echo "CONTAINER_USER=$(whoami)" >> .env
```

### Verification

To verify the fix is working:

1. Check that files created in the container have correct ownership:
   ```bash
   ls -la logs/
   # Should show files owned by your user, not root or a numeric UID
   ```

2. Check the container user matches your host user:
   ```bash
   sudo docker-compose -f docker-compose.safe.yml exec mt4-safe whoami
   # Should output your username
   ```

3. Check UIDs match:
   ```bash
   sudo docker-compose -f docker-compose.safe.yml exec mt4-safe id -u
   # Should match: id -u (on host)
   ```

### Prevention

Always use dynamic UID/GID mapping when:
- Building containers that will mount host directories
- Running containers that need to write files accessible by the host
- Developing containers that will be used by multiple users

This approach ensures the container user always matches the host user, preventing permission conflicts.