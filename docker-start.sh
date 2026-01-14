#!/bin/bash
# Docker Start Script for Grocery Price Scraper

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Starting Grocery Price Scraper with Docker"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed."
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose is not installed."
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "ERROR: Docker daemon is not running."
    echo ""
    echo "Please start Docker Desktop:"
    echo "  - macOS: Open Docker Desktop application"
    echo "  - Linux: sudo systemctl start docker"
    echo ""
    echo "Wait for Docker to start, then try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "WARNING: .env file not found"
    echo "Creating .env from .env.example..."
    if [ -f "$SCRIPT_DIR/.env.example" ]; then
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
        echo "✅ Created .env file. Please edit it with your configuration."
        echo ""
        read -p "Press Enter to continue after editing .env, or Ctrl+C to cancel..."
    else
        echo "ERROR: .env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Check if service_account.json exists
if [ ! -f "$SCRIPT_DIR/service_account.json" ]; then
    echo "WARNING: service_account.json not found"
    echo "Please ensure service_account.json is in the project root"
    read -p "Press Enter to continue anyway, or Ctrl+C to cancel..."
fi

# Create necessary directories
mkdir -p "$SCRIPT_DIR/data" "$SCRIPT_DIR/logs" "$SCRIPT_DIR/output/csv"

# Use docker compose (newer) or docker-compose (older)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Use docker-compose.yml from docker folder
COMPOSE_FILE="docker/docker-compose.yml"

echo ""
echo "Building and starting containers..."
echo ""

# Build and start (run from project root, compose file in docker/)
$COMPOSE_CMD -f "$COMPOSE_FILE" up -d --build

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Container started successfully!"
    echo "=========================================="
    echo ""
    echo "Useful commands:"
    echo "  $COMPOSE_CMD -f $COMPOSE_FILE logs -f scraper    - View logs"
    echo "  $COMPOSE_CMD -f $COMPOSE_FILE ps                  - Check status"
    echo "  $COMPOSE_CMD -f $COMPOSE_FILE stop scraper        - Stop container"
    echo "  $COMPOSE_CMD -f $COMPOSE_FILE restart scraper      - Restart container"
    echo "  $COMPOSE_CMD -f $COMPOSE_FILE down                 - Stop and remove container"
    echo ""
    echo "Viewing logs..."
    echo ""
    sleep 2
    $COMPOSE_CMD -f "$COMPOSE_FILE" logs -f --tail=50 scraper
else
    echo ""
    echo "ERROR: Failed to start container"
    echo "Check logs with: $COMPOSE_CMD -f $COMPOSE_FILE logs scraper"
    exit 1
fi
