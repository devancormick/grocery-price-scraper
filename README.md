# Publix Grocery Store Price Scraper

A comprehensive Python-based web scraping and data automation solution for collecting soda product prices from Publix grocery stores in Florida and Georgia.

## 🚀 Quick Start (One Command)

```bash
./setup.sh
```

**That's it!** The setup script will install everything and get you running. See [QUICKSTART.md](QUICKSTART.md) for details.

## Features

- ✅ **Automated Data Collection** - Web scraping from Publix website with API support
- ✅ **Pagination Handling** - Automatic pagination for large datasets
- ✅ **Date & Field Filtering** - Flexible filtering by date, week, store, and category
- ✅ **Incremental Scraping** - Only scrape new or updated records
- ✅ **Data Validation** - Comprehensive validation and cleaning
- ✅ **Deduplication** - Unique identifier-based deduplication
- ✅ **Multiple Output Formats** - CSV, JSON, Excel, Google Sheets, Database
- ✅ **Email Notifications** - Automated email reports with attachments
- ✅ **Webhook Support** - Real-time webhook delivery
- ✅ **Scheduled Execution** - Test and production modes with cron scheduling
- ✅ **Comprehensive Logging** - Detailed logs and run summaries
- ✅ **Error Handling** - Retry logic and failure notifications

## Project Structure

```
grocery-price-scraper/
├── src/publix_scraper/    # Main package
│   ├── core/              # Core modules (models, config, scraper)
│   ├── handlers/          # Data handlers (storage, validation, etc.)
│   ├── integrations/      # External integrations (Google Sheets, email, etc.)
│   └── utils/             # Utility functions
├── tests/                 # Test files
├── docs/                  # Documentation
├── scripts/               # Utility scripts
├── data/                  # Data storage
│   ├── raw/              # Raw scraped data
│   └── processed/        # Processed data
├── output/                # Output files by format
└── logs/                  # Application logs
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed structure documentation.

## Quick Start (One Command)

```bash
./setup.sh
```

This single command will:
- ✅ Check Python version
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Set up directory structure
- ✅ Create configuration files
- ✅ Verify installation

**That's it!** See [QUICKSTART.md](QUICKSTART.md) for details.

## Installation (Manual)

### Prerequisites

- Python 3.9 or higher
- pip

### Install from Source

```bash
# Clone the repository
git clone <repository-url>
cd grocery-price-scraper

# Run setup script (recommended)
./setup.sh

# Or install manually
pip install -e .
# or
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your credentials:
```env
# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_PATH=service_account.json
GOOGLE_SHEET_ID=your_sheet_id

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=scrapingserver@gmail.com
EMAIL_TO=recipient@example.com

# Scheduler
MODE=production
PRODUCTION_CRON_HOUR=2
PRODUCTION_CRON_MINUTE=0
```

3. Set up Google Sheets API:
   - Create a service account in Google Cloud Console
   - Download JSON key file as `service_account.json`
   - Share your Google Sheet with the service account email

## Usage

### Command Line

```bash
# Basic scraping
python -m src.publix_scraper.main --week 1 --store-limit 10

# With all features
python -m src.publix_scraper.main \
  --week 1 \
  --output-format excel \
  --incremental \
  --webhook-url https://your-webhook.com/endpoint

# Run scheduler
python -m src.publix_scraper.scheduler
```

### Using Makefile

```bash
# Install dependencies
make install

# Run scraper
make run

# Run demo
make demo

# Run scheduler
make scheduler

# Run tests
make test

# Format code
make format

# Lint code
make lint
```

### As a Python Package

```python
from publix_scraper.core import Product, Store, PublixScraper
from publix_scraper.handlers import DataStorage, DataValidator
from publix_scraper.integrations import GoogleSheetsHandler, EmailHandler

# Your code here
```

## Output Formats

The scraper supports multiple output formats:

- **CSV** (default): `data/publix_soda_prices.csv`
- **JSON**: Set `--output-format json`
- **Excel**: Set `--output-format excel`
- **Google Sheets**: Automatic upload (if configured)
- **Database**: SQLite or PostgreSQL (if enabled)

## Data Schema

Each product record contains 10 required variables:

1. `product_name` - Product name
2. `product_description` - Product details
3. `product_identifier` - Unique identifier
4. `date` - Scraping date
5. `price` - Product price
6. `ounces` - Total ounces
7. `price_per_ounce` - Calculated price per ounce
8. `price_promotion` - Promotion text (if any)
9. `week` - Week number (1-4)
10. `store` - Store identifier and location

## Scheduling

### Production Mode
Runs daily at specified UTC time (default: 2:00 AM):
```bash
python -m src.publix_scraper.scheduler
```

### Test Mode
Runs at configurable intervals (set `MODE=test` in `.env`):
```bash
python -m src.publix_scraper.scheduler
```

## Development

### Running Tests
```bash
make test
# or
pytest tests/ -v
```

### Code Formatting
```bash
make format
# or
black src/ tests/
```

### Linting
```bash
make lint
# or
flake8 src/ tests/
```

## Documentation

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Project structure details
- [FEATURES.md](FEATURES.md) - Comprehensive feature list
- Code is well-documented with docstrings

## License

This project is for educational and research purposes. Please ensure compliance with Publix's terms of service and robots.txt when using this scraper.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Support

For issues and questions, please open an issue on the repository.
