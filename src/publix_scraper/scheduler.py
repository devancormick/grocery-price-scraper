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
from .utils.logging_config import setup_logging, get_logger
from .utils.exceptions import ScrapingError

# Setup logging
setup_logging(
    log_level="INFO",
    log_file=Path("logs/scheduler.log")
)
logger = get_logger(__name__)


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
        # Import generate_monthly_dataset function
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
            logger.info("✅ Daily scraping job completed successfully!")
            logger.info(f"Dataset file: {dataset_file}")
            logger.info("=" * 80)
        else:
            raise Exception("Dataset generation returned None")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        raise
    except Exception as e:
        logger.error(f"Fatal error in daily scraping job: {e}", exc_info=True)
        # Send error notification
        try:
            from .integrations import EmailHandler, EMAIL_AVAILABLE
            if EMAIL_AVAILABLE:
                email_handler = EmailHandler()
                error_msg = f"Daily scraping job failed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nError: {str(e)}"
                email_handler.send_error_notification(error_msg)
        except Exception as email_error:
            logger.error(f"Failed to send error notification: {email_error}")
        raise


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
            schedule.run_pending()
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
