# Quick Start Guide

## One-Command Setup

```bash
./setup.sh
```

That's it! The setup script will:
- ✅ Check Python version
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Create necessary directories
- ✅ Set up configuration files
- ✅ Verify installation with demo

## After Setup

1. **Update credentials** (optional):
   ```bash
   nano .env  # Edit with your Google Sheets and email credentials
   ```

2. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

3. **Run demo**:
   ```bash
   python3 scripts/demo.py
   ```

## Common Commands

```bash
# Run scraper
python3 -m src.publix_scraper.main --week 1

# Run scheduler
python3 -m src.publix_scraper.scheduler

# Or use Makefile
make demo        # Run demo
make run         # Run scraper
make scheduler   # Run scheduler
make test        # Run tests
```

## What You Get

After running `./setup.sh`, you'll have:

- ✅ All dependencies installed
- ✅ Virtual environment ready
- ✅ Configuration files created
- ✅ Directory structure set up
- ✅ Demo data generated (48 product records)

## Next Steps

1. **Configure Google Sheets** (optional):
   - Create service account in Google Cloud Console
   - Download JSON key as `service_account.json`
   - Update `GOOGLE_SHEET_ID` in `.env`

2. **Configure Email** (optional):
   - Get Gmail App Password
   - Update email settings in `.env`

3. **Start Scraping**:
   ```bash
   python3 -m src.publix_scraper.main --week 1 --store-limit 10
   ```

That's all you need to get started!
