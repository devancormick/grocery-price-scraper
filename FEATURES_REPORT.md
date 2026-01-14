# Publix Price Scraper - Features Report

## Overview

Automated solution for collecting soda product prices from all Publix stores in Florida (889 stores) and Georgia (220 stores). Performs weekly data collection and delivers datasets via Google Sheets and email.

## Key Features

### 1. Automated Weekly Data Collection
Automatically determines week of month (1-4), runs once per week, covers all 1,131 stores (909 FL + 222 GA).

### 2. Complete Product Data
Collects 10 required fields: name, description, identifier, date, price, ounces, price per ounce, promotion, week, and store.

### 3. Google Sheets Integration
Automatic upload with weekly tabs ("YYYY-MM Week N"), professional formatting, full data refresh each week.

### 4. Email Delivery
Automated email reports with Google Sheet link, CSV attachment, and summary statistics.

### 5. Single Command Execution
One command runs complete workflow: store validation, data collection, Google Sheets upload, email delivery, scheduling.

### 6. Monthly Reports
Automatically generates monthly reports on last week, combining all 4 weeks with comprehensive statistics.

### 7. Data Quality & Error Handling
Comprehensive validation, cleaning, automatic retries, email notifications, and logging.

## Deliverables

**Weekly**: Google Sheet tab, CSV file, email report  
**Monthly**: Combined CSV, monthly summary, all weekly tabs preserved

## Usage

```bash
python3 run_project.py                    # Full workflow
python3 run_project.py --store-limit 10   # Test mode
```

## Performance

Collection time: ~1-2 hours | Data volume: ~450K-550K products/week | Output: Google Sheets + CSV + Email
