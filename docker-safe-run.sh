#!/bin/bash

# Safe Docker run script with automatic cleanup

set -e

# Configuration
CONTAINER_NAME="mt4-safe"
IMAGE_NAME="mt4-converter-safe"
DOCKERFILE="Dockerfile.mt4-safe"
COMPOSE_FILE="docker-compose.safe.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Cleanup function
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    
    # Stop container
    sudo docker stop $CONTAINER_NAME 2>/dev/null || true
    sudo docker rm $CONTAINER_NAME 2>/dev/null || true
    
    # Kill Wine processes if any
    sudo docker exec $CONTAINER_NAME sh -c "pkill -f wine || true" 2>/dev/null || true
    sudo docker exec $CONTAINER_NAME sh -c "wineserver -k || true" 2>/dev/null || true
    
    echo -e "${GREEN}Cleanup complete${NC}"
}

# Trap signals for cleanup
trap cleanup EXIT SIGINT SIGTERM

# Check Docker daemon
if ! sudo docker info >/dev/null 2>&1; then
    echo -e "${RED}Docker daemon is not running${NC}"
    exit 1
fi

# Clean up any existing container
echo -e "${YELLOW}Checking for existing containers...${NC}"
if sudo docker ps -a -q -f name=$CONTAINER_NAME | grep -q .; then
    echo "Removing existing container..."
    sudo docker rm -f $CONTAINER_NAME || true
fi

# Build the image
echo -e "${GREEN}Building Docker image...${NC}"
sudo docker build -f $DOCKERFILE -t $IMAGE_NAME --build-arg USER_ID=1000 --build-arg GROUP_ID=1000 --build-arg USERNAME=developer . || {
    echo -e "${RED}Failed to build Docker image${NC}"
    exit 1
}

# Run with docker-compose if compose file exists
if [ -f "$COMPOSE_FILE" ]; then
    echo -e "${GREEN}Starting with Docker Compose...${NC}"
    sudo docker-compose -f $COMPOSE_FILE up -d
    
    echo -e "${GREEN}MT4 Container started successfully!${NC}"
    echo ""
    echo "Access points:"
    echo "  - noVNC Web Interface: http://localhost:6080"
    echo "  - VNC: localhost:5901 (password: mt4vnc)"
    echo "  - Python API: http://localhost:8000"
    echo "  - Data Bridge: localhost:9090"
    echo ""
    echo "To view logs: sudo docker-compose -f $COMPOSE_FILE logs -f"
    echo "To stop: sudo docker-compose -f $COMPOSE_FILE down"
else
    # Run standalone container
    echo -e "${GREEN}Starting Docker container...${NC}"
    sudo docker run -d \
        --name $CONTAINER_NAME \
        --restart unless-stopped \
        -p 6080:6080 \
        -p 5901:5901 \
        -p 8000:8000 \
        -p 9090:9090 \
        -e DISPLAY=:1 \
        -e VNC_PASSWORD=mt4vnc \
        -e PYTHONUNBUFFERED=1 \
        -v $(pwd)/src:/app/converter/src:rw \
        -v $(pwd)/server:/app/converter/server:rw \
        -v $(pwd)/logs:/app/logs:rw \
        -v $(pwd)/data:/app/data:rw \
        --shm-size=2g \
        $IMAGE_NAME
    
    echo -e "${GREEN}MT4 Container started successfully!${NC}"
    echo ""
    echo "Access points:"
    echo "  - noVNC Web Interface: http://localhost:6080"
    echo "  - VNC: localhost:5901 (password: mt4vnc)"
    echo "  - Python API: http://localhost:8000"
    echo "  - Data Bridge: localhost:9090"
    echo ""
    echo "To view logs: sudo docker logs -f $CONTAINER_NAME"
    echo "To stop: sudo docker stop $CONTAINER_NAME"
fi

# Wait for services to be ready
echo ""
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 5

# Check health
if sudo docker exec $CONTAINER_NAME /app/scripts/healthcheck.sh 2>/dev/null; then
    echo -e "${GREEN}All services are healthy!${NC}"
else
    echo -e "${YELLOW}Services are still starting up. Please wait...${NC}"
fi

echo ""
echo "Press Ctrl+C to stop the container"

# Keep script running
wait