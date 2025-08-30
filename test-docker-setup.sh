#!/bin/bash

# Test script for Docker MT4 setup

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Docker MT4 Setup Test ===${NC}"
echo ""

# Check Docker installation
echo "1. Checking Docker installation..."
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker is installed${NC}"
    docker --version
else
    echo -e "${RED}✗ Docker is not installed${NC}"
    exit 1
fi

# Check Docker Compose
echo ""
echo "2. Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose is installed${NC}"
    docker-compose --version
else
    echo -e "${YELLOW}⚠ Docker Compose not found, using docker compose${NC}"
fi

# Check Docker daemon
echo ""
echo "3. Checking Docker daemon..."
if docker info >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker daemon is running${NC}"
else
    echo -e "${RED}✗ Docker daemon is not running${NC}"
    exit 1
fi

# Check required files
echo ""
echo "4. Checking required files..."
required_files=(
    "Dockerfile.mt4-safe"
    "docker-compose.safe.yml"
    "docker-entrypoint.sh"
    "healthcheck.sh"
    "supervisord-safe.conf"
    ".env"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file exists${NC}"
    else
        echo -e "${RED}✗ $file is missing${NC}"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = false ]; then
    echo -e "${RED}Some required files are missing${NC}"
    exit 1
fi

# Check port availability
echo ""
echo "5. Checking port availability..."
ports=(6080 5901 8000 9090)
ports_available=true

for port in "${ports[@]}"; do
    if ! lsof -i :$port >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Port $port is available${NC}"
    else
        echo -e "${YELLOW}⚠ Port $port is in use${NC}"
        ports_available=false
    fi
done

# Build test
echo ""
echo "6. Testing Docker build..."
echo -e "${YELLOW}Building Docker image (this may take a few minutes)...${NC}"

if docker build -f Dockerfile.mt4-safe -t mt4-converter-safe:test . >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    echo -e "${RED}✗ Failed to build Docker image${NC}"
    exit 1
fi

# Summary
echo ""
echo -e "${GREEN}=== Test Summary ===${NC}"
echo ""
echo "All basic checks passed! You can now run:"
echo ""
echo "  1. Start with Docker Compose:"
echo "     docker-compose -f docker-compose.safe.yml up -d"
echo ""
echo "  2. Or use the safe run script:"
echo "     ./docker-safe-run.sh"
echo ""
echo "  3. Access the services at:"
echo "     - noVNC: http://localhost:6080"
echo "     - VNC: localhost:5901 (password: mt4vnc)"
echo "     - API: http://localhost:8000"
echo ""
echo "  4. To stop and cleanup:"
echo "     ./docker-cleanup.sh"

exit 0