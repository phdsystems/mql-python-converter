#!/bin/bash

# Docker cleanup script for MT4 containers

echo "Starting Docker cleanup..."

# Function to stop container gracefully
stop_container() {
    local container=$1
    if docker ps -q -f name=$container | grep -q .; then
        echo "Stopping container: $container"
        docker stop $container --time 30 || true
        echo "Removing container: $container"
        docker rm $container || true
    else
        echo "Container $container not running"
    fi
}

# Function to cleanup volumes
cleanup_volumes() {
    echo "Cleaning up Docker volumes..."
    docker volume prune -f || true
}

# Function to cleanup networks
cleanup_networks() {
    echo "Cleaning up Docker networks..."
    docker network prune -f || true
}

# Function to cleanup images
cleanup_images() {
    echo "Cleaning up dangling Docker images..."
    docker image prune -f || true
}

# Stop all MT4 related containers
stop_container "mt4-converter"
stop_container "python-server"
stop_container "mt4-safe"

# Kill any orphaned processes in containers
docker ps -q | while read container; do
    echo "Checking container $container for Wine processes..."
    docker exec $container sh -c "pkill -f wine || true" 2>/dev/null || true
    docker exec $container sh -c "pkill -f wineserver || true" 2>/dev/null || true
    docker exec $container sh -c "wineserver -k || true" 2>/dev/null || true
done

# Optional: Full cleanup (uncomment if needed)
# cleanup_volumes
# cleanup_networks
# cleanup_images

echo "Docker cleanup complete"

# Show remaining containers
echo ""
echo "Remaining Docker containers:"
docker ps -a

echo ""
echo "Remaining Docker volumes:"
docker volume ls

exit 0