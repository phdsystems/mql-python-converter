#!/bin/bash

echo "Testing MT4 Slim Container..."
echo "=============================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command succeeded
check_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1${NC}"
        return 1
    fi
}

# 1. Start the container
echo "1. Starting container..."
sudo docker-compose -f docker-compose.slim.yml up -d
check_result "Container started"

# 2. Wait for services to initialize
echo "2. Waiting for services to initialize..."
sleep 10

# 3. Check container status
echo "3. Checking container status..."
sudo docker-compose -f docker-compose.slim.yml ps
check_result "Container status checked"

# 4. Test VNC availability
echo "4. Testing VNC port (5901)..."
nc -zv localhost 5901
check_result "VNC port is accessible"

# 5. Test NoVNC web interface
echo "5. Testing NoVNC port (6080)..."
nc -zv localhost 6080
check_result "NoVNC web interface is accessible"

# 6. Test Python API
echo "6. Testing Python API port (8000)..."
nc -zv localhost 8000
check_result "Python API port is accessible"

# 7. Check Wine installation
echo "7. Checking Wine installation..."
sudo docker-compose -f docker-compose.slim.yml exec -T mt4-slim wine --version
check_result "Wine is installed"

# 8. Check Python packages
echo "8. Checking Python packages..."
sudo docker-compose -f docker-compose.slim.yml exec -T mt4-slim python3 -c "import flask, numpy, pandas, websockets; print('All packages imported successfully')"
check_result "Python packages are installed"

# 9. Check logs
echo "9. Checking container logs..."
sudo docker-compose -f docker-compose.slim.yml logs --tail=20

echo ""
echo "=============================="
echo "Test Summary:"
echo "- VNC available at: vnc://localhost:5901 (password: mt4vnc)"
echo "- NoVNC web interface at: http://localhost:6080"
echo "- Python API at: http://localhost:8000"
echo ""
echo "To stop the container: sudo docker-compose -f docker-compose.slim.yml down"