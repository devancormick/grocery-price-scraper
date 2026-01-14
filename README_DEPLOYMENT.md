# Publix Price Scraper - Deployment Guide

## Daily Automated Data Collection

This scraper automatically collects soda product prices from all Publix stores in Florida (889) and Georgia (220) and delivers the data daily via Google Sheets and email.

## Features

✅ **Daily Google Sheets Output**: New tab each day labeled with date (YYYY-MM-DD)  
✅ **CSV Backup**: Automatic CSV file generation  
✅ **Daily Email Delivery**: Email with Google Sheet link and CSV attachment  
✅ **Error Notifications**: Email alerts if the job fails  
✅ **Automated Scheduling**: Runs daily via cron, GitHub Actions, or cloud functions  

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Credentials

The `.env` file and `service_account.json` are already configured with your credentials.

**Important**: Make sure the Google Sheet is shared with the service account email:
`sheets-service@sheets-api-project-484202.iam.gserviceaccount.com`

### 3. Test Run

```bash
# Test with a few stores
python3 generate_weekly_dataset.py --store-limit 5

# Full run (all stores, current week)
python3 generate_weekly_dataset.py

# Run for a specific week
python3 generate_weekly_dataset.py --week 2
```

## Deployment Options

### Option 1: Cron Job (Linux/macOS)

Add to crontab (`crontab -e`):

```bash
# Run daily at 2:00 AM UTC (adjust timezone as needed)
0 2 * * * cd /path/to/grocery-price-scraper && /usr/bin/python3 run_daily.py >> logs/cron.log 2>&1
```

### Option 2: GitHub Actions

Create `.github/workflows/daily_scrape.yml`:

```yaml
name: Daily Price Scrape

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2:00 AM UTC
  workflow_dispatch:  # Allow manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run daily scrape
        env:
          GOOGLE_SHEETS_CREDENTIALS_PATH: ${{ secrets.GOOGLE_SHEETS_CREDENTIALS }}
          GOOGLE_SHEET_ID: ${{ secrets.GOOGLE_SHEET_ID }}
          SMTP_USERNAME: ${{ secrets.SMTP_USERNAME }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          EMAIL_TO: ${{ secrets.EMAIL_TO }}
        run: python3 run_daily.py
```

### Option 3: Cloud Functions (AWS Lambda, Google Cloud Functions, etc.)

Package the code and deploy as a scheduled function. Use `run_daily.py` as the entry point.

### Option 4: Continuous Scheduler (Python)

Run the built-in scheduler:

```bash
python3 -m src.publix_scraper.scheduler
```

This runs continuously and executes daily at the time specified in `.env` (default: 2:00 AM UTC).

## Output

### Google Sheets
- **Location**: Sheet ID `1d-biOqVCzE_pH9M6QSx2q59M-2jufOwAn3eXWbeeceI`
- **Format**: New tab each day named with date (e.g., "2024-01-15")
- **Columns**: product_name, product_description, product_identifier, date, price, ounces, price_per_ounce, price_promotion, week, store

### CSV Files
- **Location**: `output/csv/publix_soda_prices_monthly_YYYYMMDD.csv`
- **Format**: Same columns as Google Sheets
- **Attached**: Sent via email daily

### Email Reports
- **Frequency**: Daily
- **Content**: 
  - Summary statistics
  - Google Sheet link
  - CSV file attachment
- **Recipient**: victorianlambrix230@gmail.com

## Error Handling

If the job fails:
1. Error is logged to `logs/daily_run.log` or `logs/scheduler.log`
2. Error notification email is sent automatically
3. Job can be retried manually or automatically

## Monitoring

Check logs:
```bash
tail -f logs/daily_run.log
tail -f logs/scheduler.log
tail -f logs/monthly_dataset.log
```

## Configuration

Edit `.env` to adjust:
- `MODE`: "test" (runs every 60 seconds) or "production" (daily at 2 AM UTC)
- `PRODUCTION_CRON_HOUR`: Hour to run (0-23, UTC)
- `PRODUCTION_CRON_MINUTE`: Minute to run (0-59, UTC)

## Troubleshooting

1. **Google Sheets not updating**: Check that the sheet is shared with the service account email
2. **Email not sending**: Verify SMTP credentials in `.env`
3. **Scraping errors**: Check API rate limits and network connectivity
4. **Missing dependencies**: Run `pip install -r requirements.txt`
