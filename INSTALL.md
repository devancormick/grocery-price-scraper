# Installation Guide

## One-Command Installation

The easiest way to get started:

```bash
./setup.sh
```

This script handles everything automatically.

## What the Setup Script Does

1. **Checks Requirements**
   - Verifies Python 3.9+ is installed
   - Checks for necessary tools

2. **Creates Virtual Environment**
   - Sets up isolated Python environment
   - Prevents dependency conflicts

3. **Installs Dependencies**
   - Installs all required packages from `requirements.txt`
   - Sets up the package in development mode

4. **Creates Directory Structure**
   - `data/raw/` and `data/processed/`
   - `output/csv/`, `output/json/`, `output/excel/`
   - `logs/`, `tests/`, `docs/`, `scripts/`

5. **Sets Up Configuration**
   - Creates `.env` file from template
   - Sets up default configuration

6. **Verifies Installation**
   - Runs demo script to ensure everything works
   - Generates sample data

## Manual Installation

If you prefer to install manually:

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Create directories
mkdir -p data/raw data/processed output/csv output/json output/excel logs

# 4. Set up configuration
cp .env.example .env
# Edit .env with your credentials

# 5. Verify installation
python3 scripts/demo.py
```

## Post-Installation

After running `./setup.sh`:

1. **Update `.env` file** with your credentials:
   ```bash
   nano .env
   ```

2. **Add Google Sheets credentials** (optional):
   - Download `service_account.json` from Google Cloud Console
   - Place it in the project root

3. **Test the installation**:
   ```bash
   source venv/bin/activate
   python3 scripts/demo.py
   ```

## Troubleshooting

### Python Not Found
```bash
# Install Python 3.9+ from python.org or use package manager
# macOS: brew install python3
# Ubuntu: sudo apt-get install python3 python3-pip
```

### Permission Denied
```bash
# Make scripts executable
chmod +x setup.sh start.sh
```

### Virtual Environment Issues
```bash
# Remove and recreate
rm -rf venv
./setup.sh
```

### Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall package
pip install -e .
```

## Verification

After installation, verify everything works:

```bash
# Activate virtual environment
source venv/bin/activate

# Test imports
python3 -c "from publix_scraper.core import Product, Store; print('✅ Imports working')"

# Run demo
python3 scripts/demo.py

# Check data
ls -lh data/publix_soda_prices.csv
```

## Next Steps

Once installed, see:
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [README.md](README.md) - Full documentation
- [FEATURES.md](FEATURES.md) - Feature list
