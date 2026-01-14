#!/bin/bash
# Run the Publix Price Scraper Scheduler
# This script runs the scheduler in test or production mode

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the scheduler
python3 -m src.publix_scraper.scheduler
