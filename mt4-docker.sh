#!/bin/bash

# MT4 Docker NoVNC Management Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
COMPOSE_FILE="docker-compose-novnc.yml"
CONTAINER_NAME="mt4-novnc"

# Functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}MT4 Docker NoVNC Manager${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Commands
cmd_build() {
    print_info "Building MT4 NoVNC Docker image..."
    docker-compose -f $COMPOSE_FILE build
    print_success "Build completed"
}

cmd_start() {
    print_info "Starting MT4 NoVNC container..."
    docker-compose -f $COMPOSE_FILE up -d
    sleep 5
    print_success "Container started"
    echo ""
    print_info "Access MT4 at: ${GREEN}http://localhost:6080${NC}"
    print_info "VNC Password: ${GREEN}mt4vnc${NC}"
}

cmd_stop() {
    print_info "Stopping MT4 NoVNC container..."
    docker-compose -f $COMPOSE_FILE down
    print_success "Container stopped"
}

cmd_restart() {
    print_info "Restarting MT4 NoVNC container..."
    docker-compose -f $COMPOSE_FILE restart
    print_success "Container restarted"
}

cmd_status() {
    echo "Container Status:"
    echo "----------------"
    
    if docker ps | grep -q $CONTAINER_NAME; then
        print_success "Container is running"
        echo ""
        echo "Services Status:"
        docker exec $CONTAINER_NAME supervisorctl status 2>/dev/null || print_error "Cannot get service status"
    else
        print_error "Container is not running"
    fi
}

cmd_health() {
    print_info "Running health check..."
    echo ""
    docker exec $CONTAINER_NAME /usr/local/bin/healthcheck.sh || print_error "Health check failed"
}

cmd_logs() {
    print_info "Showing container logs (Ctrl+C to exit)..."
    docker-compose -f $COMPOSE_FILE logs -f
}

cmd_shell() {
    print_info "Opening shell in container..."
    docker exec -it $CONTAINER_NAME bash
}

cmd_clean() {
    print_info "Cleaning up Docker resources..."
    docker-compose -f $COMPOSE_FILE down -v
    docker system prune -f
    print_success "Cleanup completed"
}

cmd_monitor() {
    print_info "Monitoring container (Ctrl+C to exit)..."
    watch -n 2 "docker exec $CONTAINER_NAME supervisorctl status"
}

cmd_backup() {
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    print_info "Creating backup in $BACKUP_DIR..."
    mkdir -p $BACKUP_DIR
    
    # Backup MT4 data
    docker cp $CONTAINER_NAME:/home/mt4user/mt4/MQL4 $BACKUP_DIR/ 2>/dev/null || print_error "Cannot backup MQL4 directory"
    docker cp $CONTAINER_NAME:/home/mt4user/mt4/config $BACKUP_DIR/ 2>/dev/null || print_error "Cannot backup config directory"
    
    print_success "Backup created in $BACKUP_DIR"
}

# Main menu
show_menu() {
    echo ""
    echo "Available Commands:"
    echo "  build    - Build Docker image"
    echo "  start    - Start container"
    echo "  stop     - Stop container"
    echo "  restart  - Restart container"
    echo "  status   - Show container status"
    echo "  health   - Run health check"
    echo "  logs     - Show container logs"
    echo "  shell    - Open shell in container"
    echo "  monitor  - Monitor services"
    echo "  backup   - Backup MT4 data"
    echo "  clean    - Clean up Docker resources"
    echo "  help     - Show this help"
    echo ""
}

# Main
print_header

case "${1:-help}" in
    build)
        cmd_build
        ;;
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    status)
        cmd_status
        ;;
    health)
        cmd_health
        ;;
    logs)
        cmd_logs
        ;;
    shell)
        cmd_shell
        ;;
    monitor)
        cmd_monitor
        ;;
    backup)
        cmd_backup
        ;;
    clean)
        cmd_clean
        ;;
    help|*)
        show_menu
        ;;
esac