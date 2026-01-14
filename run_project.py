#!/usr/bin/env python3
"""
Main Project Orchestrator - Continuous Scheduler

This script orchestrates the entire project workflow and runs continuously:
1. Immediately updates stores.json via StoreLocator
2. Runs weekly scraper
3. Generates CSV, uploads to Google Sheets, sends email
4. If last week of month, prepares monthly report
5. Schedules next run for next week (Sunday at 10:00 AM EST)
6. Keeps running and repeats the process when scheduled time arrives

Usage:
    python3 run_project.py
"""
import sys
import argparse
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.publix_scraper.core.store_locator import StoreLocator
from src.publix_scraper.core.config import DATA_DIR
from src.publix_scraper.utils.logging_config import setup_logging, get_logger
from src.publix_scraper.utils.week_calculator import (
    get_week_of_month, get_month_year_string, is_last_week_of_month
)
from generate_weekly_dataset import generate_weekly_dataset

# Setup logging
setup_logging(log_level="INFO", log_file=project_root / "logs/project_orchestrator.log")
logger = get_logger(__name__)


def is_stores_json_recent(max_age_hours=24):
    """
    Check if stores.json was updated recently (within max_age_hours)
    
    Args:
        max_age_hours: Maximum age in hours to consider as "recent" (default: 24 hours = 1 day)
    
    Returns:
        bool: True if stores.json exists and was updated within max_age_hours, False otherwise
    """
    from src.publix_scraper.core.config import DATA_DIR
    stores_file = DATA_DIR / "stores.json"
    
    if not stores_file.exists():
        return False
    
    try:
        # Get file modification time
        file_mtime = stores_file.stat().st_mtime
        file_age_seconds = time.time() - file_mtime
        file_age_hours = file_age_seconds / 3600
        
        return file_age_hours < max_age_hours
    except Exception:
        return False


def update_stores_json(force_update=False):
    """
    Update stores.json from Publix API
    If stores.json was updated less than 1 day ago, skip fetching unless force_update is True
    
    Args:
        force_update: If True, always fetch from API regardless of file age
    
    Returns:
        bool: True if update successful, False otherwise
    """
    logger.info("=" * 80)
    logger.info("Step 1: Updating stores.json")
    logger.info("=" * 80)
    
    try:
        store_locator = StoreLocator(use_cache=True)
        
        # Check current state
        from src.publix_scraper.core.config import DATA_DIR
        stores_file = DATA_DIR / "stores.json"
        stores_exist = stores_file.exists()
        
        # Check if stores.json is recent (less than 1 day old)
        if stores_exist and not force_update:
            if is_stores_json_recent(max_age_hours=24):
                # File is recent, use existing stores
                logger.info("stores.json was updated less than 1 day ago.")
                logger.info("Using existing stores.json (skip fetching from API).")
                logger.info("Use --force-update-stores to force fetching from API.")
                
                # Validate existing stores
                all_stores = store_locator.get_all_target_stores()
                
                if len(all_stores) == 0:
                    logger.warning("[WARNING] stores.json exists but is empty. Will fetch from API...")
                    force_update = True  # Force update if file is empty
                else:
                    logger.info(f"[SUCCESS] Using existing stores.json")
                    logger.info(f"   Total stores: {len(all_stores)}")
                    logger.info(f"   FL stores: {len([s for s in all_stores if s.state == 'FL'])}")
                    logger.info(f"   GA stores: {len([s for s in all_stores if s.state == 'GA'])}")
                    logger.info("=" * 80)
                    logger.info("[SUCCESS] Stores are ready. Proceeding to product scraping...")
                    logger.info("=" * 80)
                    return True
        
        # Fetch stores from API (either file doesn't exist, is old, or force_update is True)
        if force_update:
            logger.info("Force update mode: Fetching ALL stores from Publix API...")
        else:
            logger.info("Fetching ALL stores from Publix API to update stores.json...")
        
        stores_dict = store_locator._fetch_stores_from_api()
        
        if len(stores_dict.get("FL", [])) == 0 and len(stores_dict.get("GA", [])) == 0:
            logger.error("[ERROR] Failed to fetch stores from API")
            logger.error("   Unable to fetch stores. Aborting.")
            return False
        
        # Save fetched stores to JSON
        if not store_locator._save_stores_to_json(stores_dict):
            logger.error("[ERROR] Failed to save stores to stores.json")
            return False
        
        # Clear cache to reload
        store_locator._stores_cache = None
        
        # Get all stores to verify
        all_stores = store_locator.get_all_target_stores()
        
        if len(all_stores) == 0:
            logger.error("[ERROR] No stores found after update. Cannot proceed with scraping.")
            return False
        
        logger.info(f"[SUCCESS] Successfully fetched and updated stores.json")
        logger.info(f"   Total stores: {len(all_stores)}")
        logger.info(f"   FL stores: {len([s for s in all_stores if s.state == 'FL'])}")
        logger.info(f"   GA stores: {len([s for s in all_stores if s.state == 'GA'])}")
        logger.info("=" * 80)
        logger.info("[SUCCESS] Stores are ready. Proceeding to product scraping...")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to update stores.json: {e}", exc_info=True)
        return False


def run_weekly_scraper(store_limit=None, week=None):
    """
    Run the weekly scraper
    
    Args:
        store_limit: Limit number of stores to scrape (for testing)
        week: Week number (1-4). If None, uses current week of month
    
    Returns:
        Path to generated CSV file or None if failed
    """
    logger.info("\n" + "=" * 80)
    logger.info("Step 2: Running Weekly Scraper")
    logger.info("=" * 80)
    
    if store_limit:
        logger.info(f"   Store limit: {store_limit} (testing mode)")
    if week:
        logger.info(f"   Week: {week} (manual override)")
    
    try:
        dataset_file = generate_weekly_dataset(
            store_limit=store_limit,
            week=week,
            output_format="csv",
            start_from=0
        )
        
        if dataset_file:
            logger.info(f"[SUCCESS] Weekly scraper completed successfully")
            logger.info(f"   Dataset file: {dataset_file}")
            return dataset_file
        else:
            logger.error("[ERROR] Weekly scraper failed - no dataset generated")
            return None
            
    except Exception as e:
        logger.error(f"[ERROR] Weekly scraper failed: {e}", exc_info=True)
        return None


def generate_monthly_report(month_year: str):
    """
    Generate monthly report by combining all weekly data
    
    Args:
        month_year: Month-year string (e.g., "2026-01")
    
    Returns:
        Path to monthly report file or None if failed
    """
    logger.info("\n" + "=" * 80)
    logger.info("Step 3: Generating Monthly Report")
    logger.info("=" * 80)
    
    try:
        from src.publix_scraper.core.config import OUTPUT_DIR
        from src.publix_scraper.handlers import DataStorage
        from src.publix_scraper.core.models import Product
        import pandas as pd
        
        # Find all weekly CSV files for this month
        month_str = month_year.replace('-', '')
        weekly_files = list(OUTPUT_DIR.glob(f"publix_soda_prices_week*_{month_str}.csv"))
        
        if not weekly_files:
            logger.warning(f"No weekly files found for {month_year}")
            return None
        
        logger.info(f"Found {len(weekly_files)} weekly files for {month_year}")
        
        # Combine all weekly data
        all_products = []
        for weekly_file in sorted(weekly_files):
            logger.info(f"  Reading {weekly_file.name}...")
            df = pd.read_csv(weekly_file)
            # Convert DataFrame rows to Product objects (simplified - just for aggregation)
            all_products.append(df)
        
        # Combine all dataframes
        monthly_df = pd.concat(all_products, ignore_index=True)
        
        # Remove duplicates based on product_identifier, date, store, week
        monthly_df = monthly_df.drop_duplicates(
            subset=['product_identifier', 'date', 'store', 'week'],
            keep='first'
        )
        
        # Save monthly report
        monthly_filename = f"publix_soda_prices_monthly_{month_str}"
        monthly_output = OUTPUT_DIR / f"{monthly_filename}.csv"
        monthly_df.to_csv(monthly_output, index=False)
        
        logger.info(f"[SUCCESS] Monthly report generated: {monthly_output}")
        logger.info(f"   Total products: {len(monthly_df)}")
        logger.info(f"   Total stores: {monthly_df['store'].nunique()}")
        logger.info(f"   Weeks covered: {sorted(monthly_df['week'].unique().tolist())}")
        
        # Generate summary
        summary = {
            "month_year": month_year,
            "generation_date": datetime.now().isoformat(),
            "total_products": len(monthly_df),
            "total_stores": int(monthly_df['store'].nunique()),
            "weeks_covered": sorted(monthly_df['week'].unique().tolist()),
            "weekly_files": [str(f.name) for f in weekly_files]
        }
        
        summary_file = OUTPUT_DIR / f"{monthly_filename}_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"   Summary saved: {summary_file}")
        
        return monthly_output
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to generate monthly report: {e}", exc_info=True)
        return None


def calculate_next_sunday_10am_est():
    """
    Calculate next Sunday at 10:00 AM EST
    
    Returns:
        datetime: Next Sunday at 10:00 AM EST
    """
    import pytz
    
    # Get current time in EST
    est = pytz.timezone('US/Eastern')
    now_est = datetime.now(est)
    
    # Find next Sunday
    days_until_sunday = (6 - now_est.weekday()) % 7
    if days_until_sunday == 0:
        # If today is Sunday, check if we've passed 10 AM
        if now_est.hour < 10 or (now_est.hour == 10 and now_est.minute == 0):
            # Today is Sunday but before 10 AM, use today
            next_sunday = now_est.replace(hour=10, minute=0, second=0, microsecond=0)
        else:
            # Today is Sunday but after 10 AM, use next Sunday
            next_sunday = now_est + timedelta(days=7)
            next_sunday = next_sunday.replace(hour=10, minute=0, second=0, microsecond=0)
    else:
        # Not Sunday yet, calculate next Sunday
        next_sunday = now_est + timedelta(days=days_until_sunday)
        next_sunday = next_sunday.replace(hour=10, minute=0, second=0, microsecond=0)
    
    return next_sunday


def run_weekly_workflow(store_limit=None, week=None, force_update_stores=False):
    """
    Run the complete weekly workflow:
    1. Update stores.json
    2. Run weekly scraper
    3. Generate monthly report if last week of month
    
    Args:
        store_limit: Limit number of stores (for testing)
        week: Week number override
        force_update_stores: Force fetching stores from API even if recent
    
    Returns:
        bool: True if successful
    """
    try:
        # Step 1: Update stores.json
        if not update_stores_json(force_update=force_update_stores):
            logger.error("[ERROR] Store update failed.")
            return False
        
        # Step 2: Run weekly scraper
        dataset_file = run_weekly_scraper(
            store_limit=store_limit,
            week=week
        )
        if not dataset_file:
            logger.error("[ERROR] Weekly scraper failed.")
            return False
        
        # Step 3: Generate monthly report if last week of month
        current_date = datetime.now().date()
        month_year = get_month_year_string(current_date)
        is_last_week = is_last_week_of_month(current_date)
        
        if is_last_week:
            logger.info(f"\n[INFO] Last week of month detected. Generating monthly report...")
            monthly_report = generate_monthly_report(month_year)
            if monthly_report:
                logger.info(f"[SUCCESS] Monthly report generated: {monthly_report}")
            else:
                logger.warning("[WARNING] Monthly report generation failed, but continuing...")
        
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Error in weekly workflow: {e}", exc_info=True)
        return False


def main():
    """
    Main orchestrator function - Runs continuously
    Executes workflow immediately, then schedules next run for Sunday at 10:00 AM EST
    """
    parser = argparse.ArgumentParser(
        description="Publix Price Scraper - Continuous Project Orchestrator"
    )
    parser.add_argument(
        "--store-limit",
        type=int,
        default=None,
        help="Limit number of stores to scrape (for testing)"
    )
    parser.add_argument(
        "--week",
        type=int,
        choices=[1, 2, 3, 4],
        default=None,
        help="Week number (1-4). If not specified, uses current week of month"
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run once and exit (no continuous scheduling)"
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Test mode: schedule runs every 200 seconds instead of weekly"
    )
    parser.add_argument(
        "--force-update-stores",
        action="store_true",
        help="Force fetching stores from API even if stores.json was updated less than 1 day ago"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("Publix Price Scraper - Continuous Project Orchestrator")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.store_limit:
        logger.info(f"Store limit: {args.store_limit} (testing mode)")
    if args.week:
        logger.info(f"Week override: {args.week}")
    if args.test_mode:
        logger.info("Test mode: Scheduling runs every 200 seconds")
    if args.force_update_stores:
        logger.info("Force update stores: Will fetch stores from API even if recent")
    logger.info("=" * 80)
    
    # Run workflow immediately
    logger.info("\n[INFO] Running initial workflow execution...")
    run_weekly_workflow(store_limit=args.store_limit, week=args.week, force_update_stores=args.force_update_stores)
    
    # If run-once flag is set, exit after first run
    if args.run_once:
        logger.info("\n[INFO] Run-once mode: Exiting after initial run")
        logger.info("=" * 80)
        return
    
    # Test mode: Schedule every 200 seconds
    if args.test_mode:
        TEST_INTERVAL = 200  # 200 seconds
        logger.info("\n" + "=" * 80)
        logger.info("Setting up test mode scheduler...")
        logger.info("=" * 80)
        logger.info(f"Test mode: Scheduling runs every {TEST_INTERVAL} seconds")
        logger.info("The process will continue running and execute the workflow every 200 seconds.")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 80)
        
        # Keep scheduler running indefinitely
        try:
            last_run_time = None
            while True:
                try:
                    current_time = time.time()
                    
                    # Check if 200 seconds have passed since last run
                    if last_run_time is None or (current_time - last_run_time) >= TEST_INTERVAL:
                        # Time to run!
                        logger.info("\n" + "=" * 80)
                        logger.info(f"[INFO] Scheduled time reached: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        logger.info("=" * 80)
                        
                        # Run the workflow
                        try:
                            if run_weekly_workflow(store_limit=args.store_limit, week=None, force_update_stores=args.force_update_stores):
                                last_run_time = current_time
                                logger.info("\n[SUCCESS] Workflow completed successfully")
                                logger.info(f"Next run in {TEST_INTERVAL} seconds")
                            else:
                                logger.error(f"[ERROR] Workflow failed, will retry in {TEST_INTERVAL} seconds")
                                last_run_time = current_time  # Still update time to prevent immediate retry
                        except Exception as workflow_error:
                            # Log error but don't stop scheduler
                            logger.error(f"[ERROR] Workflow execution error: {workflow_error}", exc_info=True)
                            logger.error(f"[ERROR] Will retry in {TEST_INTERVAL} seconds")
                            last_run_time = current_time  # Still update time to prevent immediate retry
                        
                        logger.info("=" * 80)
                        logger.info("Scheduler continues running...")
                        logger.info("=" * 80)
                    
                except Exception as e:
                    # Prevent unexpected errors from killing the scheduler
                    logger.error(f"[ERROR] Error in scheduler loop: {e}", exc_info=True)
                
                time.sleep(10)  # Check every 10 seconds in test mode
                
        except KeyboardInterrupt:
            logger.info("\n[INFO] Scheduler stopped by user")
            sys.exit(0)
    
    # Production mode: Schedule for Sunday at 10:00 AM EST
    import pytz
    est = pytz.timezone('US/Eastern')
    next_sunday = calculate_next_sunday_10am_est()
    
    logger.info("\n" + "=" * 80)
    logger.info("Setting up continuous scheduler...")
    logger.info("=" * 80)
    logger.info(f"Next scheduled run: {next_sunday.strftime('%A, %B %d, %Y at %I:%M %p %Z')}")
    logger.info("The process will continue running and execute the workflow at the scheduled time.")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80)
    
    # Keep scheduler running indefinitely
    # Check every minute if it's time to run (Sunday at 10:00 AM EST)
    try:
        last_run_week = None
        while True:
            try:
                # Get current time in EST
                now_est = datetime.now(est)
                current_week = now_est.isocalendar()[1]  # ISO week number
                
                # Check if it's Sunday and 10:00 AM EST (within 5 minute window to account for timing)
                if (now_est.weekday() == 6 and  # Sunday
                    now_est.hour == 10 and 
                    0 <= now_est.minute < 5 and  # Within first 5 minutes of 10 AM
                    (last_run_week is None or current_week != last_run_week)):
                    # Time to run!
                    logger.info("\n" + "=" * 80)
                    logger.info(f"[INFO] Scheduled time reached: {now_est.strftime('%A, %B %d, %Y at %I:%M %p %Z')}")
                    logger.info("=" * 80)
                    
                    # Run the workflow
                    try:
                        if run_weekly_workflow(store_limit=args.store_limit, week=None, force_update_stores=args.force_update_stores):
                            last_run_week = current_week
                            logger.info("\n[SUCCESS] Weekly workflow completed successfully")
                            
                            # Calculate next Sunday
                            next_sunday = calculate_next_sunday_10am_est()
                            logger.info(f"Next scheduled run: {next_sunday.strftime('%A, %B %d, %Y at %I:%M %p %Z')}")
                        else:
                            logger.error("[ERROR] Weekly workflow failed, will retry next Sunday")
                    except Exception as workflow_error:
                        # Log error but don't stop scheduler
                        logger.error(f"[ERROR] Workflow execution error: {workflow_error}", exc_info=True)
                        logger.error("[ERROR] Will retry next Sunday")
                    
                    logger.info("=" * 80)
                    logger.info("Scheduler continues running...")
                    logger.info("=" * 80)
                
            except Exception as e:
                # Prevent unexpected errors from killing the scheduler
                logger.error(f"[ERROR] Error in scheduler loop: {e}", exc_info=True)
            
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("\n[INFO] Scheduler stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except KeyboardInterrupt:
        logger.info("\n[WARNING] Orchestration interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"[ERROR] Fatal error: {e}", exc_info=True)
        sys.exit(1)
