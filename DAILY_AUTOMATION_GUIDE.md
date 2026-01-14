# Daily Automation Guide

This guide explains how to use the daily automation features for the Publix Price Scraper.

## 🚀 Quick Start

### Test Mode (60 seconds interval)
```bash
# Set MODE=test in .env file
# Then run:
python3 -m src.publix_scraper.scheduler

# Or use the script:
./run_scheduler.sh
```

### Production Mode (Daily at 2:00 AM UTC)
```bash
# Set MODE=production in .env file
# Then run:
python3 -m src.publix_scraper.scheduler
```

## 📋 Features

### 1. Daily Google Sheets Tabs
- Creates a new tab each day labeled with the date (YYYY-MM-DD format)
- Example: `2024-01-15`, `2024-01-16`, etc.
- Automatically formats headers and resizes columns
- Appends new data to existing tabs if run multiple times per day

### 2. CSV Backup Files
- Creates daily CSV files in `output/csv/` directory
- Filename format: `publix_soda_prices_YYYY-MM-DD.csv`
- Attached to daily email reports

### 3. Daily Email Reports
- Sends email with:
  - Link to Google Sheet
  - CSV file attached
  - Summary statistics (total products, new products, stores covered)
- Subject line: `Publix Price Scraper - Daily Report (YYYY-MM-DD) - X products`

### 4. Error Notifications
- Automatically sends email if scraping job fails
- Includes error details and timestamp
- Subject line: `ERROR: Publix Price Scraper Failed`

## ⚙️ Configuration

### Environment Variables (.env file)

```bash
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

# Scheduler Mode
MODE=test  # or "production"

# Test Mode (runs every X seconds)
TEST_INTERVAL_SECONDS=60

# Production Mode (runs daily at specified time UTC)
PRODUCTION_CRON_HOUR=2
PRODUCTION_CRON_MINUTE=0
```

## 🔄 How It Works

### Test Mode
1. Runs immediately when started
2. Repeats every `TEST_INTERVAL_SECONDS` (default: 60 seconds)
3. Continues running until stopped (Ctrl+C)
4. Perfect for testing the scraping and email delivery

### Production Mode
1. Schedules daily run at specified UTC time
2. Runs once per day at the scheduled time
3. Continues running indefinitely
4. Automatically handles timezone conversion

## 📊 Daily Workflow

1. **Scraping**: Scrapes all weeks (1-4) for all stores
2. **Validation**: Validates and cleans all scraped data
3. **Deduplication**: Removes duplicate records
4. **Google Sheets**: Creates/updates daily tab with all new products
5. **CSV Backup**: Saves daily CSV file
6. **Email**: Sends daily report with link and CSV attachment

## 🛠️ Running the Scheduler

### Option 1: Direct Python
```bash
python3 -m src.publix_scraper.scheduler
```

### Option 2: Using Script
```bash
./run_scheduler.sh
```

### Option 3: Background Process
```bash
nohup python3 -m src.publix_scraper.scheduler > logs/scheduler.out 2>&1 &
```

### Option 4: Systemd Service (Linux)
Create `/etc/systemd/system/publix-scraper.service`:
```ini
[Unit]
Description=Publix Price Scraper Scheduler
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/grocery-price-scraper
ExecStart=/usr/bin/python3 -m src.publix_scraper.scheduler
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable publix-scraper
sudo systemctl start publix-scraper
sudo systemctl status publix-scraper
```

## 📧 Email Configuration

### Gmail Setup
1. Enable 2-Factor Authentication
2. Generate App Password:
   - Go to Google Account → Security → App passwords
   - Generate password for "Mail"
   - Use this password in `.env` file (not your regular password)

### Email Format
- **Daily Report**: Includes summary, Google Sheet link, and CSV attachment
- **Error Notification**: Sent automatically if job fails

## 🔍 Monitoring

### Logs
- Scheduler logs: `logs/scheduler.log`
- Scraper logs: `logs/scraper.log`
- All logs include timestamps and detailed information

### Check Status
```bash
# View scheduler logs
tail -f logs/scheduler.log

# Check if process is running
ps aux | grep scheduler
```

## 🧪 Testing

### Test Mode (Recommended First)
1. Set `MODE=test` in `.env`
2. Set `TEST_INTERVAL_SECONDS=60`
3. Run scheduler: `python3 -m src.publix_scraper.scheduler`
4. Wait 60 seconds and verify:
   - Email received
   - Google Sheet updated
   - CSV file created

### Production Mode
1. Set `MODE=production` in `.env`
2. Set `PRODUCTION_CRON_HOUR` and `PRODUCTION_CRON_MINUTE`
3. Run scheduler: `python3 -m src.publix_scraper.scheduler`
4. Scheduler will wait until scheduled time

## 🚨 Troubleshooting

### Scheduler Not Running
- Check logs: `logs/scheduler.log`
- Verify `.env` file exists and is configured
- Check Python dependencies: `pip install -r requirements.txt`

### Email Not Sending
- Verify SMTP credentials in `.env`
- Check Gmail App Password is correct
- Check logs for SMTP errors
- Verify `EMAIL_TO` is set correctly

### Google Sheets Not Updating
- Verify `service_account.json` exists
- Check Google Sheet is shared with service account email
- Verify `GOOGLE_SHEET_ID` is correct
- Check logs for API errors

### CSV Files Not Created
- Check `OUTPUT_DIR` exists: `mkdir -p output/csv`
- Verify write permissions
- Check logs for file errors

## 📝 Notes

- Scheduler runs continuously and never stops (unless interrupted)
- Test mode runs immediately, then repeats at interval
- Production mode waits until scheduled time
- All times are in UTC
- Daily tabs are created with date format: YYYY-MM-DD
- CSV files are saved with date format: `publix_soda_prices_YYYY-MM-DD.csv`

## 🔐 Security

- Never commit `.env` file to git
- Keep `service_account.json` secure
- Use App Passwords for Gmail (not regular passwords)
- Rotate credentials regularly
