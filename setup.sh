#!/bin/bash
# One-command setup script for Publix Price Scraper

set -e  # Exit on error

echo "=========================================="
echo "Publix Price Scraper - Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo "✅ Dependencies installed"
else
    echo "⚠️  requirements.txt not found, installing from pyproject.toml..."
    pip install -e . --quiet
    echo "✅ Package installed"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p data/raw data/processed
mkdir -p output/csv output/json output/excel
mkdir -p logs
mkdir -p tests docs scripts
echo "✅ Directories created"

# Copy .env.example to .env if .env doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo ""
        echo "Creating .env file from template..."
        cp .env.example .env
        echo "✅ .env file created (please update with your credentials)"
    else
        echo ""
        echo "⚠️  .env.example not found, creating basic .env..."
        cat > .env << 'EOF'
# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH=service_account.json
GOOGLE_SHEET_ID=

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
EMAIL_FROM=
EMAIL_TO=

# Output Configuration
OUTPUT_DIR=output/csv

# Scheduler Configuration
MODE=production
TEST_INTERVAL_SECONDS=60
PRODUCTION_CRON_HOUR=2
PRODUCTION_CRON_MINUTE=0
EOF
        echo "✅ Basic .env file created"
    fi
else
    echo "✅ .env file already exists"
fi

# Check for service_account.json
if [ ! -f "service_account.json" ]; then
    echo ""
    echo "⚠️  service_account.json not found"
    echo "   To enable Google Sheets integration:"
    echo "   1. Create a service account in Google Cloud Console"
    echo "   2. Download the JSON key file"
    echo "   3. Save it as service_account.json in the project root"
fi

# Run demo to verify installation
echo ""
echo "Running demo to verify installation..."
python3 scripts/demo.py > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Demo completed successfully"
else
    echo "⚠️  Demo had issues, but installation may still be correct"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Quick Start:"
echo "  1. Update .env with your credentials"
echo "  2. Run: source venv/bin/activate"
echo "  3. Run: python3 scripts/demo.py"
echo ""
echo "Or use the Makefile:"
echo "  make demo    # Run demo"
echo "  make run     # Run scraper"
echo "  make scheduler  # Run scheduler"
echo ""
echo "For more information, see README.md"
echo ""
