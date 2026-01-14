#!/bin/bash
# Docker Stop Script for Grocery Price Scraper

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Stopping Grocery Price Scraper"
echo "=========================================="

# Use docker compose (newer) or docker-compose (older)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Use docker-compose.yml from docker folder
COMPOSE_FILE="docker/docker-compose.yml"

# Stop and remove containers
$COMPOSE_CMD -f "$COMPOSE_FILE" down

echo ""
echo "✅ Container stopped and removed"
echo ""
echo "To start again: ./docker-start.sh"
