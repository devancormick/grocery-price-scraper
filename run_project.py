#!/usr/bin/env python3
"""
Main Project Orchestrator

This script orchestrates the entire project workflow:
1. Updates stores.json via StoreLocator
2. Runs weekly scraper
3. Generates CSV, uploads to Google Sheets, sends email
4. If last week of month, prepares monthly report
5. Schedules next operation using cron

Usage:
    python3 run_project.py
"""
import sys
import argparse
import subprocess
import json
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


def update_stores_json():
    """
    Always fetch ALL stores from Publix API and update stores.json
    This ensures we have the latest store data before scraping
    
    Returns:
        bool: True if update successful, False otherwise
    """
    logger.info("=" * 80)
    logger.info("Step 1: Fetching ALL stores from Publix API")
    logger.info("=" * 80)
    logger.info("This step will:")
    logger.info("  - Always fetch ALL stores from Publix API")
    logger.info("  - Update stores.json with the latest store data")
    logger.info("  - Validate stores before proceeding to product scraping")
    logger.info("=" * 80)
    
    try:
        store_locator = StoreLocator(use_cache=True)
        
        # Check current state
        from src.publix_scraper.core.config import DATA_DIR
        stores_file = DATA_DIR / "stores.json"
        stores_exist = stores_file.exists()
        
        if stores_exist:
            # Check if file has stores
            all_stores_before = store_locator.get_all_target_stores()
            logger.info(f"Current stores.json found: {len(all_stores_before)} stores")
        else:
            logger.info("stores.json not found.")
        
        # Always fetch stores from API to ensure we have the latest data
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
        
        logger.info(f"[SUCCESS] Successfully updated/validated stores.json")
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


def calculate_next_run_time():
    """
    Calculate next run time (next week, same day, 10:00 AM EST)
    
    Returns:
        datetime: Next run time
    """
    from datetime import time
    import pytz
    
    # Get current time in EST
    est = pytz.timezone('US/Eastern')
    now_est = datetime.now(est)
    
    # Next week, same day of week, at 10:00 AM EST
    next_run = now_est + timedelta(weeks=1)
    next_run = next_run.replace(hour=10, minute=0, second=0, microsecond=0)
    
    return next_run


def schedule_next_run():
    """
    Schedule next run using cron (Linux/Mac) or provide instructions for Windows
    
    Returns:
        bool: True if scheduled successfully
    """
    import platform
    
    logger.info("\n" + "=" * 80)
    logger.info("Step 4: Scheduling Next Run")
    logger.info("=" * 80)
    
    try:
        next_run = calculate_next_run_time()
        
        # Check if running on Windows
        if platform.system() == "Windows":
            logger.warning("[WARNING] Cron scheduling is not available on Windows")
            logger.warning("   Please use Windows Task Scheduler to schedule the next run")
            logger.info(f"   Next run should be: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            logger.info(f"   Command to run: {sys.executable} {Path(__file__).absolute()}")
            return False
        
        # Linux/Mac: Use cron
        # Convert to cron format
        # Cron format: minute hour day month weekday
        cron_minute = next_run.minute
        cron_hour = next_run.hour
        cron_day = next_run.day
        cron_month = next_run.month
        cron_weekday = next_run.weekday()  # 0=Monday, 6=Sunday
        
        # Build cron command
        cron_command = f"{cron_minute} {cron_hour} {cron_day} {cron_month} {cron_weekday}"
        
        # Get absolute path to this script
        script_path = Path(__file__).absolute()
        python_path = sys.executable
        
        # Full command to run
        full_command = f"{python_path} {script_path}"
        
        # Create cron entry
        cron_entry = f"{cron_command} {full_command} >> {project_root}/logs/cron.log 2>&1\n"
        
        # Get current crontab
        try:
            result = subprocess.run(
                ['crontab', '-l'],
                capture_output=True,
                text=True,
                check=False
            )
            current_crontab = result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            current_crontab = ""
        
        # Remove existing entry for this script if any
        lines = current_crontab.split('\n')
        filtered_lines = [
            line for line in lines
            if str(script_path) not in line and line.strip()
        ]
        
        # Add new entry
        filtered_lines.append(cron_entry.strip())
        
        # Write updated crontab
        new_crontab = '\n'.join(filtered_lines) + '\n'
        
        process = subprocess.Popen(
            ['crontab', '-'],
            stdin=subprocess.PIPE,
            text=True
        )
        process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            logger.info(f"[SUCCESS] Next run scheduled successfully")
            logger.info(f"   Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            logger.info(f"   Cron entry: {cron_entry.strip()}")
            return True
        else:
            logger.error("[ERROR] Failed to schedule next run")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] Error scheduling next run: {e}", exc_info=True)
        return False


def main():
    """Main orchestrator function"""
    parser = argparse.ArgumentParser(
        description="Publix Price Scraper - Project Orchestrator"
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
        "--no-schedule",
        action="store_true",
        help="Skip scheduling next run (useful for testing)"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("Publix Price Scraper - Project Orchestrator")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.store_limit:
        logger.info(f"Store limit: {args.store_limit} (testing mode)")
    if args.week:
        logger.info(f"Week override: {args.week}")
    if args.no_schedule:
        logger.info("Scheduling disabled (--no-schedule)")
    logger.info("=" * 80)
    
    # Step 1: Update stores.json
    if not update_stores_json():
        logger.error("[ERROR] Store update failed. Aborting.")
        sys.exit(1)
    
    # Step 2: Run weekly scraper
    dataset_file = run_weekly_scraper(
        store_limit=args.store_limit,
        week=args.week
    )
    if not dataset_file:
        logger.error("[ERROR] Weekly scraper failed. Aborting.")
        sys.exit(1)
    
    # Step 3: Generate monthly report if last week of month
    current_date = datetime.now().date()
    month_year = get_month_year_string(current_date)
    is_last_week = is_last_week_of_month(current_date)
    
    if is_last_week:
        logger.info(f"\n[WARNING] Last week of month detected. Generating monthly report...")
        monthly_report = generate_monthly_report(month_year)
        if monthly_report:
            logger.info(f"[SUCCESS] Monthly report generated: {monthly_report}")
        else:
            logger.warning("[WARNING] Monthly report generation failed, but continuing...")
    
    # Step 4: Schedule next run (unless disabled)
    if not args.no_schedule:
        schedule_next_run()
    else:
        logger.info("\n[INFO] Scheduling skipped (--no-schedule flag)")
    
    logger.info("\n" + "=" * 80)
    logger.info("[SUCCESS] Project Orchestration Complete!")
    logger.info("=" * 80)
    logger.info(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)


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
