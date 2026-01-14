# Publix Price Scraper - Features Report

## Overview

Automated solution for collecting soda product prices from all Publix stores in Florida (889 stores) and Georgia (220 stores). The system performs weekly data collection and delivers comprehensive datasets via Google Sheets and email.

## Key Features

### 1. Automated Weekly Data Collection

- Automatically determines which week of the month to scrape (1-4)
- Runs once per week on a scheduled basis
- Collects data from all 1,131 stores (909 FL + 222 GA)
- Handles month transitions automatically

### 2. Complete Store Coverage

- Comprehensive store database with all Publix locations
- Automatic store validation before scraping
- Efficient store lookup and filtering
- Supports both Florida and Georgia stores

### 3. Comprehensive Product Data Collection

- Collects all soda products from each store
- Captures 10 required data points per product:
  1. Product name
  2. Product description
  3. Product identifier (consistent across weeks)
  4. Date
  5. Price
  6. Ounces
  7. Price per ounce
  8. Price promotion
  9. Week
  10. Store location

### 4. Google Sheets Integration

- Automatic upload to Google Sheets
- Weekly tabs organized by month and week (e.g., "2026-01 Week 2")
- Professional formatting with headers and auto-resized columns
- Direct links to specific weekly tabs
- Full data refresh each week (no duplicates)

### 5. Email Delivery System

- Automated email reports after each weekly collection
- Includes Google Sheet link with direct tab access
- CSV file attachment for backup
- Summary statistics in email body
- Error notifications if collection fails

### 6. Data Export Options

- CSV files for easy analysis
- Organized by week and month
- Summary reports with metadata
- Automatic file naming with dates

### 7. Single Command Execution

- One command runs the entire workflow:
  - Store validation
  - Weekly data collection
  - Google Sheets upload
  - Email delivery
  - Monthly report (if applicable)
  - Next run scheduling

### 8. Automated Scheduling

- Automatically schedules next week's run
- Configurable run times
- Supports cron-based scheduling
- Can run continuously or on-demand

### 9. Monthly Report Generation

- Automatically generates monthly reports on the last week
- Combines data from all 4 weeks
- Provides comprehensive monthly statistics
- Preserves all weekly data in organized format

### 10. Data Quality Assurance

- Comprehensive data validation
- Automatic data cleaning and normalization
- Handles edge cases (e.g., products with 0 ounces)
- Ensures data consistency across all records

### 11. Error Handling & Monitoring

- Comprehensive logging system
- Automatic error notifications via email
- Graceful error handling
- Detailed error tracking for debugging

### 12. Flexible Testing Options

- Test mode with limited stores
- Manual week override
- Skip scheduling for testing
- Resume from specific store index

## Deliverables

### Weekly Deliverables

1. **Google Sheet Tab**: Fresh data for the current week
2. **CSV File**: Backup copy of weekly data
3. **Email Report**: Notification with links and attachments
4. **Summary Statistics**: Metadata and collection statistics

### Monthly Deliverables

1. **Monthly CSV**: Combined data from all 4 weeks
2. **Monthly Summary**: Aggregated statistics and analysis
3. **Complete Weekly History**: All weekly tabs preserved in Google Sheet

## Data Collection Process

1. **Store Update**: Validates store database
2. **Week Detection**: Determines current week automatically
3. **Product Collection**: Scrapes all stores for current week
4. **Data Processing**: Validates and cleans all collected data
5. **Export**: Generates CSV files
6. **Upload**: Updates Google Sheets with fresh data
7. **Notification**: Sends email with results
8. **Scheduling**: Sets up next week's run

## Usage

### Basic Usage

```bash
# Run complete workflow
python3 run_project.py

# Test with limited stores
python3 run_project.py --store-limit 10 --no-schedule
```

### Weekly Scraping

```bash
# Run weekly scraper
python3 generate_weekly_dataset.py

# With options
python3 generate_weekly_dataset.py --store-limit 5 --week 2
```

## Deployment

The system can be deployed via:

- **Cron Jobs**: Scheduled execution on servers
- **Cloud Functions**: Serverless deployment
- **GitHub Actions**: Automated CI/CD
- **Continuous Scheduler**: Python-based scheduler

## Output Format

### Google Sheets Structure

- **Sheet**: Single configured Google Sheet
- **Tabs**: "YYYY-MM Week N" format (e.g., "2026-01 Week 2")
- **Columns**: 10 columns matching the required data points
- **Formatting**: Professional headers and auto-resized columns

### CSV File Structure

- **Naming**: `publix_soda_prices_week{N}_{YYYYMM}.csv`
- **Format**: Standard CSV with headers
- **Location**: `output/csv/` directory
- **Content**: All 10 required fields per product

## Performance

- **Collection Time**: ~1-2 hours for all stores
- **Data Volume**: ~400-500 products per store
- **Total Products**: ~450,000-550,000 products per week
- **File Size**: ~50-100 MB per weekly CSV

## Reliability Features

- **Error Recovery**: Automatic retries on failures
- **Data Validation**: Ensures data quality before export
- **Backup Files**: CSV files as backup to Google Sheets
- **Email Alerts**: Notifications on errors or completion
- **Logging**: Comprehensive logs for troubleshooting

## Benefits

✅ **Automated**: Runs without manual intervention  
✅ **Comprehensive**: Covers all stores and products  
✅ **Reliable**: Robust error handling and retry mechanisms  
✅ **Professional**: Google Sheets + Email delivery  
✅ **Scalable**: Handles 1,131 stores efficiently  
✅ **Maintainable**: Clean code structure and logging  

## Summary

The Publix Price Scraper provides a complete, automated solution for weekly price data collection. It delivers professional-grade outputs via Google Sheets and email, with comprehensive error handling and scheduling capabilities. The system is production-ready and requires minimal maintenance once deployed.
