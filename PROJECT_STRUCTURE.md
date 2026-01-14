# Project Structure

This document describes the best-practice project structure for the Publix Price Scraper.

## Directory Layout

```
grocery-price-scraper/
├── .github/
│   └── workflows/          # GitHub Actions workflows
├── data/
│   ├── raw/               # Raw scraped data
│   └── processed/         # Processed/cleaned data
├── docs/                  # Documentation
├── logs/                  # Application logs
├── output/                # Output files
│   ├── csv/              # CSV exports
│   ├── json/             # JSON exports
│   └── excel/            # Excel exports
├── scripts/               # Utility scripts
│   └── demo.py           # Demo script
├── src/                   # Source code
│   └── publix_scraper/   # Main package
│       ├── __init__.py
│       ├── cli.py        # CLI entry point
│       ├── main.py       # Main execution logic
│       ├── scheduler.py  # Scheduler
│       ├── core/         # Core modules
│       │   ├── __init__.py
│       │   ├── models.py      # Data models
│       │   ├── config.py      # Configuration
│       │   ├── scraper.py     # Web scraper
│       │   └── store_locator.py
│       ├── handlers/     # Data handlers
│       │   ├── __init__.py
│       │   ├── storage.py      # Data storage
│       │   ├── validator.py    # Data validation
│       │   ├── deduplication.py
│       │   ├── incremental.py  # Incremental scraping
│       │   └── summary.py      # Run summaries
│       ├── integrations/ # External integrations
│       │   ├── __init__.py
│       │   ├── google_sheets.py
│       │   ├── email.py
│       │   ├── webhook.py
│       │   └── database.py
│       └── utils/        # Utilities
│           └── __init__.py
├── tests/                 # Test files
├── .env                   # Environment variables (gitignored)
├── .env.example          # Environment template
├── .gitignore
├── Makefile              # Build commands
├── pyproject.toml        # Project configuration
├── README.md
├── FEATURES.md
└── requirements.txt      # Dependencies (legacy)
```

## Package Organization

### Core Modules (`src/publix_scraper/core/`)
- **models.py**: Data models (Product, Store)
- **config.py**: Configuration management
- **scraper.py**: Web scraping logic
- **store_locator.py**: Store location management

### Handlers (`src/publix_scraper/handlers/`)
- **storage.py**: Multi-format data storage (CSV/JSON/Excel)
- **validator.py**: Data validation and cleaning
- **deduplication.py**: Deduplication logic
- **incremental.py**: Incremental scraping support
- **summary.py**: Run summary generation

### Integrations (`src/publix_scraper/integrations/`)
- **google_sheets.py**: Google Sheets integration
- **email.py**: Email notifications
- **webhook.py**: Webhook delivery
- **database.py**: Database integration

## Best Practices Applied

1. **Separation of Concerns**: Core logic, handlers, and integrations are separated
2. **Package Structure**: Proper Python package with `__init__.py` files
3. **Configuration Management**: Centralized config with environment variables
4. **Modularity**: Each feature in its own module
5. **Testability**: Tests directory for unit tests
6. **Documentation**: Comprehensive docs directory
7. **Build System**: Modern `pyproject.toml` instead of `setup.py`
8. **Entry Points**: CLI entry point via `cli.py`
9. **Data Organization**: Separate raw/processed data directories
10. **Output Management**: Organized output by format

## Usage

### As a Package
```bash
# Install in development mode
pip install -e .

# Run as module
python -m src.publix_scraper.main --week 1

# Run scheduler
python -m src.publix_scraper.scheduler
```

### As a Script
```bash
# Run demo
python scripts/demo.py

# Run with Makefile
make run
make demo
make scheduler
```

## Import Examples

```python
# From package
from publix_scraper.core import Product, Store, PublixScraper
from publix_scraper.handlers import DataStorage, DataValidator
from publix_scraper.integrations import GoogleSheetsHandler, EmailHandler

# Direct imports
from src.publix_scraper.core.models import Product
from src.publix_scraper.handlers.storage import DataStorage
```
