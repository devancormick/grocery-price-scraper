# Grocery Price Scraper - Usage Guide

## Single Command Execution

The project can be run with a single command that handles everything automatically:

```bash
python run_project.py
```

## How It Works

When you run `python run_project.py`, the following happens:

### 1. Immediate Execution
- **Store Locator**: Immediately fetches ALL stores from Publix API and updates `stores.json`
- **Weekly Scraper**: Runs immediately to collect product data
- **CSV Generation**: Creates CSV file with scraped data
- **Google Sheets**: Uploads data to Google Sheets (if configured)
- **Email**: Sends email report (if configured)
- **Monthly Report**: If it's the last week of the month, generates monthly report

### 2. Continuous Scheduling
After the initial run completes:
- **Next Run**: Automatically scheduled for next **Sunday at 10:00 AM EST**
- **Process Stays Active**: The process continues running in the background
- **Automatic Execution**: When Sunday 10:00 AM EST arrives, the workflow repeats automatically

### 3. Workflow Steps (Repeats Weekly)

Each scheduled run executes:
1. **Fetch Stores**: Updates `stores.json` with latest stores from Publix API
2. **Scrape Products**: Collects price data for all products from all stores
3. **Generate CSV**: Creates weekly CSV file
4. **Upload to Google Sheets**: Adds data to weekly tab in monthly sheet
5. **Send Email**: Sends weekly report email
6. **Monthly Report**: If last week of month, generates and saves monthly report

## Command Options

### Run Once (No Continuous Scheduling)
```bash
python run_project.py --run-once
```
Runs the workflow once and exits. Useful for testing.

### Testing Mode
```bash
python run_project.py --store-limit 5
```
Limits scraping to 5 stores for faster testing.

### Week Override
```bash
python run_project.py --week 2
```
Manually specify which week to scrape (1-4).

### Test Mode (200 Second Intervals)
```bash
python run_project.py --test-mode
```
Runs the workflow every 200 seconds instead of weekly. Useful for testing the scheduler functionality.

### Force Update Stores
```bash
python run_project.py --force-update-stores
```
Forces fetching stores from API even if stores.json was updated less than 1 day ago. By default, the system uses cached stores if they're less than 24 hours old.

## Process Management

### Starting the Process
```bash
python run_project.py
```

### Stopping the Process
Press `Ctrl+C` to gracefully stop the scheduler.

### Running in Background (Linux/Mac)
```bash
nohup python run_project.py > logs/output.log 2>&1 &
```

### Running as Windows Service
Use Windows Task Scheduler or a service manager like NSSM.

## Logs

All logs are saved to:
- `logs/project_orchestrator.log` - Main orchestrator logs
- `logs/scheduler.log` - Scheduler-specific logs (if using scheduler.py)

## Schedule Details

- **Frequency**: Weekly
- **Day**: Sunday
- **Time**: 10:00 AM EST
- **Timezone**: US/Eastern (handles daylight saving time automatically)

## Error Handling

- The scheduler continues running even if individual jobs fail
- Errors are logged and email notifications are sent (if configured)
- Failed jobs don't stop the scheduler - it will retry next Sunday

## Requirements

- Python 3.8+
- All dependencies from `requirements.txt`
- Google Sheets credentials (if using Google Sheets integration)
- Email configuration (if using email notifications)

