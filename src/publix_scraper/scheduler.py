"""
Scheduler for automated price collection with test/production modes
Runs continuously and handles daily scraping with email notifications
"""
import schedule
import time
import sys
from datetime import datetime
from pathlib import Path

from .core.config import MODE, TEST_INTERVAL_SECONDS, PRODUCTION_CRON_HOUR, PRODUCTION_CRON_MINUTE
from .core.store_locator import StoreLocator
from .utils.logging_config import setup_logging, get_logger
from .utils.exceptions import ScrapingError

# Setup logging
setup_logging(
    log_level="INFO",
    log_file=Path("logs/scheduler.log")
)
logger = get_logger(__name__)


def is_stores_json_recent(max_age_hours=24):
    """
    Check if stores.json was updated recently (within max_age_hours)
    
    Args:
        max_age_hours: Maximum age in hours to consider as "recent" (default: 24 hours = 1 day)
    
    Returns:
        bool: True if stores.json exists and was updated within max_age_hours, False otherwise
    """
    from .core.config import DATA_DIR
    stores_file = DATA_DIR / "stores.json"
    
    if not stores_file.exists():
        return False
    
    try:
        import time
        # Get file modification time
        file_mtime = stores_file.stat().st_mtime
        file_age_seconds = time.time() - file_mtime
        file_age_hours = file_age_seconds / 3600
        
        return file_age_hours < max_age_hours
    except Exception:
        return False


def update_stores(force_update=False):
    """
    Update stores.json from Publix API before scraping
    If stores.json was updated less than 1 day ago, skip fetching unless force_update is True
    
    Args:
        force_update: If True, always fetch from API regardless of file age
    
    Returns:
        bool: True if update successful, False otherwise
    """
    logger.info("=" * 80)
    logger.info("Updating stores.json")
    logger.info("=" * 80)
    
    try:
        store_locator = StoreLocator(use_cache=True)
        
        # Check current state
        from .core.config import DATA_DIR
        stores_file = DATA_DIR / "stores.json"
        stores_exist = stores_file.exists()
        
        # Check if stores.json is recent (less than 1 day old)
        if stores_exist and not force_update:
            if is_stores_json_recent(max_age_hours=24):
                # File is recent, use existing stores
                logger.info("stores.json was updated less than 1 day ago.")
                logger.info("Using existing stores.json (skip fetching from API).")
                
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
                    return True
        
        # Fetch stores from API (either file doesn't exist, is old, or force_update is True)
        if force_update:
            logger.info("Force update mode: Fetching ALL stores from Publix API...")
        else:
            logger.info("Fetching ALL stores from Publix API to update stores.json...")
        
        stores_dict = store_locator._fetch_stores_from_api()
        
        if len(stores_dict.get("FL", [])) == 0 and len(stores_dict.get("GA", [])) == 0:
            logger.error("[ERROR] Failed to fetch stores from API")
            logger.error("   Unable to fetch stores. Aborting scraping job.")
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
            logger.error("[ERROR] No stores found after fetch. Cannot proceed with scraping.")
            return False
        
        logger.info(f"[SUCCESS] Successfully fetched and updated stores.json")
        logger.info(f"   Total stores: {len(all_stores)}")
        logger.info(f"   FL stores: {len([s for s in all_stores if s.state == 'FL'])}")
        logger.info(f"   GA stores: {len([s for s in all_stores if s.state == 'GA'])}")
        
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to update stores.json: {e}", exc_info=True)
        return False


def daily_scrape():
    """
    Run weekly scraping job by calling generate_weekly_dataset.py
    This will scrape all stores for the current week, upload to Google Sheets (weekly tab in monthly sheet), and send email
    """
    logger.info("=" * 80)
    logger.info("Starting daily scraping job")
    logger.info(f"Job started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    try:
        # Step 1: Update stores.json before scraping
        if not update_stores():
            raise Exception("Failed to update stores.json. Aborting scraping job.")
        
        # Step 2: Import and run scraping
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        
        from generate_weekly_dataset import generate_weekly_dataset
        
        # Run the weekly dataset generator (which handles weekly tabs and emails)
        dataset_file = generate_weekly_dataset(
            store_limit=None,  # All stores
            week=None,  # Use current week of month
            output_format="csv",
            start_from=0
        )
        
        if dataset_file:
            logger.info("=" * 80)
            logger.info("[SUCCESS] Daily scraping job completed successfully!")
            logger.info(f"Dataset file: {dataset_file}")
            logger.info("=" * 80)
        else:
            raise Exception("Dataset generation returned None")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        raise
    except Exception as e:
        # Log and notify, but do not crash the scheduler loop
        logger.error(f"Fatal error in daily scraping job: {e}", exc_info=True)
        try:
            from .integrations import EmailHandler, EMAIL_AVAILABLE
            if EMAIL_AVAILABLE:
                email_handler = EmailHandler()
                error_msg = (
                    f"Daily scraping job failed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nError: {str(e)}"
                )
                email_handler.send_error_notification(error_msg)
        except Exception as email_error:
            logger.error(f"Failed to send error notification: {email_error}")
        return False

    return True


def setup_scheduler():
    """
    Setup daily scraping schedule based on mode
    Runs continuously and never stops
    """
    if MODE == "test":
        # Test mode: Run at specified interval
        logger.info(f"Test mode: Scheduling to run every {TEST_INTERVAL_SECONDS} seconds")
        schedule.every(TEST_INTERVAL_SECONDS).seconds.do(daily_scrape)
        
        # Run immediately for testing
        logger.info("Running initial test execution...")
        try:
            daily_scrape()
        except Exception as e:
            logger.error(f"Initial test execution failed: {e}", exc_info=True)
        
    elif MODE == "production":
        # Production mode: Run daily at specified time (UTC)
        time_str = f"{PRODUCTION_CRON_HOUR:02d}:{PRODUCTION_CRON_MINUTE:02d}"
        logger.info(f"Production mode: Scheduling daily run at {time_str} UTC")
        schedule.every().day.at(time_str).do(daily_scrape)
        
        # Calculate time until next run
        now = datetime.now()
        next_run = now.replace(hour=PRODUCTION_CRON_HOUR, minute=PRODUCTION_CRON_MINUTE, second=0, microsecond=0)
        if next_run <= now:
            next_run = next_run.replace(day=next_run.day + 1)
        wait_seconds = (next_run - now).total_seconds()
        logger.info(f"Next run scheduled in {wait_seconds/3600:.1f} hours")
    else:
        logger.error(f"Invalid MODE: {MODE}. Must be 'test' or 'production'")
        return
    
    logger.info("=" * 80)
    logger.info("Scheduler configured and running continuously...")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80)
    
    # Keep scheduler running indefinitely
    try:
        while True:
            try:
                schedule.run_pending()
            except Exception as e:
                # Prevent unexpected job errors from killing the scheduler
                logger.error(f"Error while running scheduled jobs: {e}", exc_info=True)
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("Starting Publix Price Scraper Scheduler")
    logger.info(f"Mode: {MODE}")
    if MODE == "test":
        logger.info(f"Test interval: {TEST_INTERVAL_SECONDS} seconds")
        logger.info("Will run continuously and repeat every interval")
    else:
        logger.info(f"Production schedule: Daily at {PRODUCTION_CRON_HOUR:02d}:{PRODUCTION_CRON_MINUTE:02d} UTC")
    logger.info("=" * 80)
    
    setup_scheduler()
