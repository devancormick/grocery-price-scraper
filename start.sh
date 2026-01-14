#!/bin/bash
# Quick start script - activates venv and runs demo

set -e

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup..."
    ./setup.sh
fi

# Activate virtual environment
source venv/bin/activate

# Run demo
echo ""
echo "=========================================="
echo "Starting Publix Price Scraper Demo"
echo "=========================================="
echo ""
python3 scripts/demo.py
