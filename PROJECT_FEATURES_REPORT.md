# Publix Price Scraper - Project Features Report

## Overview

The Publix Price Scraper is a comprehensive Python-based solution for automated collection of soda product prices from all Publix stores in Florida (889 stores) and Georgia (220 stores). The system performs weekly data collection, processes and validates the data, and delivers it via Google Sheets and email on a scheduled basis.

## Core Features

### 1. Automated Weekly Data Collection

**Feature**: Weekly scraping workflow that automatically determines the current week of the month and collects data accordingly.

- **Week Detection**: Automatically calculates which week of the month it is (1-4) based on the current date
- **Weekly Execution**: Runs once per week, typically on a designated day (e.g., Monday)
- **Month Management**: Automatically handles month transitions and creates appropriate sheet tabs

**Implementation**:
- `generate_weekly_dataset.py` - Main weekly scraping script
- `src/publix_scraper/utils/week_calculator.py` - Week calculation utilities

### 2. Store Location Management

**Feature**: Comprehensive store locator system for managing Publix store locations.

- **Store Database**: Loads 1,131 stores (909 FL + 222 GA) from `stores.json`
- **Store Validation**: Validates store data integrity before scraping
- **Caching**: Efficient in-memory caching for fast store lookups
- **State Filtering**: Easy filtering by state (FL/GA)

**Implementation**:
- `src/publix_scraper/core/store_locator.py`
- `data/stores.json` - Store database

### 3. API-Based Product Scraping

**Feature**: Efficient API-based scraping using Publix's GraphQL API.

- **Direct API Access**: Uses Publix API endpoint for fast, reliable data collection
- **Pagination Support**: Handles large product catalogs with automatic pagination (100 items per page)
- **Rate Limiting**: Built-in delays and retry mechanisms for polite scraping
- **Error Handling**: Robust error handling with automatic retries
- **No Browser Required**: Pure API calls, no Selenium needed

**Implementation**:
- `src/publix_scraper/core/scraper.py`
- API endpoint: `https://services.publix.com/search/api/search/storeproductssavings/`

**Key Capabilities**:
- Extracts product name, description, identifier, price, ounces, promotions
- Handles products with 0 ounces gracefully
- Calculates price per ounce automatically
- Extracts store location information

### 4. Data Validation and Cleaning

**Feature**: Comprehensive data validation and cleaning pipeline.

- **Field Validation**: Validates all 10 required fields
- **Data Type Checking**: Ensures correct data types (dates, numbers, strings)
- **Range Validation**: Sanity checks for prices, ounces, etc.
- **Zero Ounces Support**: Handles products with 0 ounces (sets price_per_ounce to None)
- **Data Cleaning**: Normalizes text, rounds numbers, handles missing values

**Implementation**:
- `src/publix_scraper/handlers/validator.py`

**Validated Fields**:
1. Product name
2. Product description
3. Product identifier (consistent across weeks)
4. Date
5. Price
6. Ounces
7. Price per ounce
8. Price promotion
9. Week
10. Store

### 5. Google Sheets Integration

**Feature**: Automated Google Sheets upload with weekly tab management.

- **Monthly Sheet Organization**: Uses configured Google Sheet for all data
- **Weekly Tabs**: Creates tabs with format "YYYY-MM Week N" (e.g., "2026-01 Week 2")
- **Full Overwrite**: Each week's tab is completely overwritten with fresh data
- **Auto-Formatting**: Headers are bold and colored, columns auto-resize
- **Service Account Auth**: Secure authentication using Google service account

**Implementation**:
- `src/publix_scraper/integrations/google_sheets.py`
- `service_account.json` - Google service account credentials

**Features**:
- Automatic tab creation for each week
- Full data overwrite (no duplicates)
- Professional formatting
- Direct links to specific tabs in emails

### 6. Email Notification System

**Feature**: Automated email delivery with CSV attachments.

- **Weekly Reports**: Sends email after each weekly scraping session
- **CSV Attachments**: Includes CSV backup file in email
- **Google Sheet Links**: Provides direct links to the updated sheet tabs
- **Error Notifications**: Sends error alerts if scraping fails
- **SMTP Support**: Works with Gmail and other SMTP servers

**Implementation**:
- `src/publix_scraper/integrations/email.py`

**Email Content**:
- Summary statistics (products scraped, stores covered, week)
- Google Sheet link with direct tab access
- CSV file attachment
- Date and time information

### 7. Data Storage and Export

**Feature**: Multiple output formats with organized file management.

- **CSV Export**: Primary format for data export
- **JSON Support**: Optional JSON export for programmatic access
- **Excel Support**: Optional Excel export with formatting
- **Organized Output**: Files organized by week and month
- **Summary Reports**: JSON summary files with metadata

**Implementation**:
- `src/publix_scraper/handlers/storage.py`
- Output directory: `output/csv/`

**File Naming**:
- Weekly: `publix_soda_prices_week{week}_{YYYYMM}.csv`
- Monthly: `publix_soda_prices_monthly_{YYYYMM}.csv`
- Summary: `publix_soda_prices_week{week}_{YYYYMM}_summary.json`

### 8. Project Orchestration

**Feature**: Single-command execution for complete workflow automation.

- **Unified Entry Point**: `run_project.py` orchestrates entire workflow
- **Store Update**: Validates/updates stores.json before scraping
- **Weekly Scraping**: Runs weekly dataset generation
- **Monthly Reports**: Automatically generates monthly reports on last week
- **Auto-Scheduling**: Schedules next run via cron automatically

**Implementation**:
- `run_project.py` - Main orchestrator

**Workflow Steps**:
1. Update/validate stores.json
2. Run weekly scraper for current week
3. Generate CSV, upload to Google Sheets, send email
4. If last week of month: Generate monthly report
5. Schedule next run (next week, 10 AM EST)

**Command-Line Options**:
- `--store-limit N`: Limit stores for testing
- `--week N`: Override week number (1-4)
- `--no-schedule`: Skip cron scheduling (for testing)

### 9. Automated Scheduling

**Feature**: Automatic scheduling of next scraping run.

- **Cron Integration**: Automatically updates crontab
- **Next Week Scheduling**: Schedules next run for same day next week at 10:00 AM EST
- **Timezone Handling**: Proper EST timezone conversion
- **Resume Support**: Can resume from specific store index

**Implementation**:
- `run_project.py` - `schedule_next_run()` function
- `src/publix_scraper/scheduler.py` - Continuous scheduler option

**Scheduling Options**:
- Production mode: Daily at configured time (default: 2:00 AM UTC)
- Test mode: Configurable interval (default: 60 seconds)
- Manual: Run via `run_project.py` with auto-scheduling

### 10. Error Handling and Logging

**Feature**: Comprehensive error handling and logging system.

- **Structured Logging**: Detailed logs with timestamps and log levels
- **Error Notifications**: Automatic email alerts on failures
- **Graceful Degradation**: Continues operation even if some components fail
- **Error Tracking**: Tracks and logs all errors for debugging
- **Retry Mechanisms**: Automatic retries for network errors

**Implementation**:
- `src/publix_scraper/utils/logging_config.py`
- Log files: `logs/weekly_dataset.log`, `logs/project_orchestrator.log`, `logs/scheduler.log`

**Error Handling**:
- Network errors: Automatic retries with exponential backoff
- API errors: Graceful handling with fallback options
- Validation errors: Detailed error messages and logging
- Integration errors: Continues with other components if one fails

### 11. Data Quality Features

**Feature**: Ensures high-quality, consistent data output.

- **Deduplication**: Prevents duplicate entries (handled at CSV level)
- **Incremental Tracking**: Tracks what's been scraped before
- **Data Normalization**: Consistent formatting across all records
- **Field Validation**: Ensures all required fields are present and valid
- **Type Safety**: Proper data types for all fields

**Implementation**:
- `src/publix_scraper/handlers/deduplication.py`
- `src/publix_scraper/handlers/incremental.py`
- `src/publix_scraper/handlers/validator.py`

### 12. Monthly Report Generation

**Feature**: Automatic monthly report compilation.

- **Week Aggregation**: Combines all 4 weeks of data
- **Deduplication**: Removes duplicates across weeks
- **Summary Statistics**: Provides comprehensive monthly statistics
- **Automatic Trigger**: Generates on last week of month

**Implementation**:
- `run_project.py` - `generate_monthly_report()` function

**Monthly Report Includes**:
- All products from all 4 weeks
- Total stores covered
- Weeks included
- Summary statistics

## Technical Architecture

### Technology Stack

- **Language**: Python 3.9+
- **Core Libraries**:
  - `requests` - HTTP API calls
  - `pandas` - Data manipulation
  - `gspread` - Google Sheets API
  - `python-dotenv` - Configuration management
- **Integrations**:
  - Google Sheets API
  - SMTP (Email)
- **Scheduling**: Cron (via `run_project.py`) or Python scheduler

### Project Structure

```
grocery-price-scraper/
├── run_project.py                 # Main orchestrator (single command)
├── generate_weekly_dataset.py     # Weekly scraping script
├── src/publix_scraper/
│   ├── core/
│   │   ├── scraper.py            # API-based scraping
│   │   ├── store_locator.py      # Store management
│   │   ├── models.py             # Data models
│   │   └── config.py             # Configuration
│   ├── handlers/
│   │   ├── validator.py          # Data validation
│   │   ├── storage.py            # Data storage
│   │   ├── deduplication.py       # Deduplication
│   │   └── incremental.py        # Incremental tracking
│   ├── integrations/
│   │   ├── google_sheets.py      # Google Sheets integration
│   │   └── email.py              # Email notifications
│   └── utils/
│       ├── week_calculator.py    # Week calculation
│       └── logging_config.py    # Logging setup
├── data/
│   └── stores.json               # Store database
├── output/
│   └── csv/                      # Output files
└── logs/                         # Log files
```

## Data Flow

1. **Store Update**: Validates/updates `stores.json`
2. **Week Detection**: Determines current week (1-4)
3. **Product Scraping**: Scrapes all stores for current week via API
4. **Data Validation**: Validates and cleans all products
5. **CSV Generation**: Creates weekly CSV file
6. **Google Sheets Upload**: Overwrites weekly tab with fresh data
7. **Email Delivery**: Sends email with sheet link and CSV attachment
8. **Monthly Report**: If last week, generates monthly aggregation
9. **Scheduling**: Schedules next week's run

## Configuration

### Environment Variables (.env)

```bash
# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_PATH=service_account.json
GOOGLE_SHEET_ID=1d-biOqVCzE_pH9M6QSx2q59M-2jufOwAn3eXWbeeceI

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=scrapingserver@gmail.com
EMAIL_TO=recipient@gmail.com

# Scheduler
MODE=production
PRODUCTION_CRON_HOUR=2
PRODUCTION_CRON_MINUTE=0
```

## Usage Examples

### Basic Usage

```bash
# Run complete workflow (all stores, current week)
python3 run_project.py

# Test with limited stores
python3 run_project.py --store-limit 10 --no-schedule

# Run for specific week
python3 run_project.py --week 2 --no-schedule
```

### Weekly Scraping Only

```bash
# Run weekly scraper directly
python3 generate_weekly_dataset.py

# With options
python3 generate_weekly_dataset.py --store-limit 5 --week 1
```

## Deployment Options

### 1. Cron Job (Recommended)

```bash
# Add to crontab (crontab -e)
0 10 * * 1 cd /path/to/project && python3 run_project.py
```

### 2. Continuous Scheduler

```bash
# Run Python scheduler
python3 -m src.publix_scraper.scheduler
```

### 3. GitHub Actions

```yaml
on:
  schedule:
    - cron: '0 10 * * 1'  # Every Monday at 10 AM
```

### 4. Cloud Functions

Deploy `run_project.py` as a scheduled cloud function.

## Output Deliverables

### Weekly Deliverables

1. **Google Sheet Tab**: "YYYY-MM Week N" with all products
2. **CSV File**: `publix_soda_prices_week{N}_{YYYYMM}.csv`
3. **Email Report**: With sheet link and CSV attachment
4. **Summary JSON**: Metadata and statistics

### Monthly Deliverables

1. **Monthly CSV**: Combined data from all 4 weeks
2. **Monthly Summary**: Aggregated statistics
3. **All Weekly Tabs**: Preserved in Google Sheet

## Data Schema

### Product Record (10 Required Fields)

1. **product_name**: String - Product name
2. **product_description**: String - Product description (e.g., "12 - 12 fl oz (355 ml) cans")
3. **product_identifier**: String - Consistent ID across weeks
4. **date**: Date - Scraping date (YYYY-MM-DD)
5. **price**: Float - Product price in USD
6. **ounces**: Float - Product size in ounces (can be 0)
7. **price_per_ounce**: Float - Calculated price per ounce (None if ounces is 0)
8. **price_promotion**: String - Promotion text (e.g., "Buy 2 Get 1 Free") or None
9. **week**: Integer - Week number (1-4)
10. **store**: String - Store identifier (e.g., "FL-1651 - Lakeland, FL")

## Performance Characteristics

- **Scraping Speed**: ~2-3 seconds per store (API-based)
- **Total Time**: ~1-2 hours for all 1,131 stores
- **Data Volume**: ~400-500 products per store
- **Total Products**: ~450,000-550,000 products per week
- **Storage**: ~50-100 MB per weekly CSV file

## Security Features

- **Service Account Auth**: Secure Google Sheets authentication
- **Environment Variables**: Credentials stored in `.env` (not in code)
- **Error Handling**: No sensitive data in error messages
- **Rate Limiting**: Polite API usage with delays

## Monitoring and Maintenance

### Log Files

- `logs/project_orchestrator.log` - Main workflow logs
- `logs/weekly_dataset.log` - Weekly scraping logs
- `logs/scheduler.log` - Scheduler logs

### Health Checks

- Store validation before scraping
- Email notifications on errors
- Summary statistics in logs
- CSV file generation verification

## Future Enhancements

Potential improvements for future versions:

1. **Database Integration**: Store data in SQL database
2. **Webhook Support**: Real-time notifications
3. **Dashboard**: Web interface for monitoring
4. **Price Tracking**: Historical price analysis
5. **Alerting**: Price change notifications
6. **Multi-Store Comparison**: Compare prices across stores
7. **API Endpoint**: REST API for data access

## Support and Documentation

- **Deployment Guide**: `README_DEPLOYMENT.md`
- **Configuration**: `.env` file with comments
- **Logging**: Comprehensive logging for debugging
- **Error Messages**: Clear, actionable error messages

## Conclusion

The Publix Price Scraper is a production-ready, automated solution for weekly price data collection. It provides:

✅ **Automated Workflow**: Single command execution  
✅ **Reliable Data Collection**: API-based, fast, and reliable  
✅ **Professional Delivery**: Google Sheets + Email + CSV  
✅ **Error Resilience**: Comprehensive error handling  
✅ **Scalability**: Handles 1,131 stores efficiently  
✅ **Maintainability**: Clean code, good logging, modular design  

The system is ready for production deployment and can run continuously with minimal maintenance.
