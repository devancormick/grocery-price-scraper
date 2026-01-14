# Quick Start - Daily Automation

## 🚀 Start Testing (60 Second Intervals)

### Step 1: Verify Configuration
The `.env` file is already configured with:
- ✅ Test mode enabled (`MODE=test`)
- ✅ 60-second intervals (`TEST_INTERVAL_SECONDS=60`)
- ✅ Google Sheets credentials
- ✅ Email credentials

### Step 2: Run the Scheduler
```bash
cd /Users/administrator/Documents/github/grocery-price-scraper
python3 -m src.publix_scraper.scheduler
```

### Step 3: What Happens
1. **Immediately**: First scraping run starts
2. **After 60 seconds**: Second run starts
3. **Continues**: Repeats every 60 seconds until you stop it (Ctrl+C)

### Step 4: Verify Results
After the first run (about 1-2 minutes), check:

1. **Email**: Check `victorianlambrix230@gmail.com`
   - Subject: "Publix Price Scraper - Daily Report (YYYY-MM-DD)"
   - Contains Google Sheet link
   - CSV file attached

2. **Google Sheet**: Open the link in email
   - New tab created with today's date (e.g., "2024-01-15")
   - Data populated in the tab

3. **CSV File**: Check `output/csv/` directory
   - File: `publix_soda_prices_YYYY-MM-DD.csv`

4. **Logs**: Check `logs/scheduler.log`
   - All actions logged with timestamps

## 📧 Email Format

You'll receive an email like this:

```
Subject: Publix Price Scraper - Daily Report (2024-01-15) - 150 products

Publix Grocery Store Price Scraping - Daily Report

Date: 2024-01-15
Report Generated: 2024-01-15 10:30:00

Summary:
- Total products scraped: 150
- New products: 120
- Duplicate products: 30
- Stores covered: 5

✅ Data has been successfully collected and uploaded to Google Sheets.

📊 Google Sheet Link:
https://docs.google.com/spreadsheets/d/1d-biOqVCzE_pH9M6QSx2q59M-2jufOwAn3eXWbeeceI/edit#gid=123456

📎 A CSV backup file is attached to this email.
   File: publix_soda_prices_2024-01-15.csv
```

## 🔄 Switch to Production Mode

When ready for daily production runs:

1. **Edit `.env` file**:
   ```bash
   MODE=production
   PRODUCTION_CRON_HOUR=2
   PRODUCTION_CRON_MINUTE=0
   ```

2. **Run scheduler**:
   ```bash
   python3 -m src.publix_scraper.scheduler
   ```

3. **Scheduler will**:
   - Wait until 2:00 AM UTC
   - Run once per day
   - Continue running indefinitely

## 🛑 Stop the Scheduler

Press `Ctrl+C` to stop the scheduler gracefully.

## 🐛 Troubleshooting

### No Email Received
- Check spam folder
- Verify SMTP credentials in `.env`
- Check logs: `tail -f logs/scheduler.log`

### Google Sheet Not Updating
- Verify `service_account.json` exists
- Check Google Sheet is shared with service account email
- Check logs for API errors

### Scheduler Not Running
- Check Python version: `python3 --version` (needs 3.9+)
- Install dependencies: `pip install -r requirements.txt`
- Check logs: `cat logs/scheduler.log`

## 📚 More Information

- **Full Guide**: See `DAILY_AUTOMATION_GUIDE.md`
- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`
- **Code Optimizations**: See `OPTIMIZATION_SUMMARY.md`

## ✅ Ready to Test!

Run this command to start:
```bash
python3 -m src.publix_scraper.scheduler
```

The scheduler will:
1. ✅ Run immediately (first test)
2. ✅ Create Google Sheet tab with today's date
3. ✅ Create CSV backup file
4. ✅ Send email with link and CSV attachment
5. ✅ Repeat every 60 seconds

**Watch the logs to see it working!**
