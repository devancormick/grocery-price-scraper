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
    Run daily scraping job
    Scrapes all weeks (1-4) and sends daily email with Google Sheet link and CSV
    """
    logger.info("=" * 80)
    logger.info("Starting daily scraping job")
    logger.info(f"Job started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    try:
        # Import required modules
        from .core.scraper import PublixScraper
        from .core.store_locator import StoreLocator
        from .core.models import Store
        from .core.config import WEEKS_TO_COLLECT, OUTPUT_DIR
        from .handlers import (
            DataStorage, DataValidator, DeduplicationHandler,
            IncrementalScraper, RunSummary
        )
        from .integrations import GoogleSheetsHandler, EmailHandler
        
        # Initialize components
        store_locator = StoreLocator()
        scraper = PublixScraper(use_selenium=True)  # Use Selenium for JavaScript-heavy pages
        storage = DataStorage(format='csv')
        validator = DataValidator()
        deduplicator = DeduplicationHandler(storage)
        incremental = IncrementalScraper(storage)
        summary = RunSummary()
        
        # Initialize integrations
        google_sheets = None
        email_handler = None
        
        try:
            google_sheets = GoogleSheetsHandler()
            logger.info("Google Sheets handler initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Google Sheets: {e}")
        
        try:
            email_handler = EmailHandler()
            logger.info("Email handler initialized")
        except Exception as e:
            logger.warning(f"Could not initialize email handler: {e}")
        
        # Get store locations
        logger.info("Fetching store locations...")
        stores = []
        try:
            fl_stores = store_locator.get_florida_stores()
            stores.extend(fl_stores)
            logger.info(f"Found {len(fl_stores)} Florida stores")
        except Exception as e:
            logger.warning(f"Error fetching FL stores: {e}")
        
        try:
            ga_stores = store_locator.get_georgia_stores()
            stores.extend(ga_stores)
            logger.info(f"Found {len(ga_stores)} Georgia stores")
        except Exception as e:
            logger.warning(f"Error fetching GA stores: {e}")
        
        if not stores:
            logger.warning("No stores found. Using placeholder stores.")
            stores = [
                Store(store_id=f"FL-{i:04d}", store_name=f"Publix Store {i}",
                      address=f"Address {i}", city="Lakeland", state="FL", zip_code="33801")
                for i in range(1, 6)
            ]
        
        # Scrape all weeks
        all_products = []
        current_date = datetime.now().date()
        date_str = current_date.strftime('%Y-%m-%d')
        
        with scraper:
            for week in range(1, WEEKS_TO_COLLECT + 1):
                logger.info(f"Scraping week {week}...")
                try:
                    week_products = []
                    for store in stores:
                        try:
                            products = scraper.scrape_store_products(store, week)
                            week_products.extend(products)
                            summary.products_scraped += len(products)
                            summary.stores_processed += 1
                        except Exception as e:
                            logger.warning(f"Error scraping store {store.store_id}: {e}")
                            continue
                    
                    # Validate and clean
                    if week_products:
                        validated, errors = validator.validate_and_clean_products(week_products)
                        summary.products_valid += len(validated)
                        summary.products_invalid += len(errors)
                        
                        # Incremental filtering
                        new_products = incremental.filter_new_products(validated)
                        
                        # Deduplication
                        new_products, duplicates = deduplicator.filter_new_records(new_products)
                        summary.products_new += len(new_products)
                        summary.products_duplicate += len(duplicates)
                        
                        all_products.extend(new_products)
                        
                        # Save to storage
                        if new_products:
                            storage.save_products(new_products, append=True)
                    
                    logger.info(f"Week {week} completed: {len(week_products)} products scraped")
                    
                except Exception as e:
                    logger.error(f"Error scraping week {week}: {e}", exc_info=True)
                    summary.errors.append({
                        'type': 'scraping_error',
                        'week': week,
                        'message': str(e)
                    })
        
        # Upload to Google Sheets and send email
        if all_products and google_sheets:
            try:
                # Create daily tab in Google Sheets
                sheet_url, new_count, total_count = google_sheets.create_daily_tab(
                    date_str, all_products
                )
                summary.google_sheets_uploaded = True
                logger.info(f"Data uploaded to Google Sheets: {sheet_url}")
                
                # Create daily CSV backup
                daily_csv = OUTPUT_DIR / f"publix_soda_prices_{date_str}.csv"
                daily_storage = DataStorage(output_file=daily_csv, format='csv')
                daily_storage.save_products(all_products, append=False)
                summary.files_created.append(str(daily_csv))
                
                # Send daily email report
                if email_handler:
                    email_handler.send_daily_report(
                        date=date_str,
                        product_count=len(all_products),
                        new_count=summary.products_new,
                        store_count=len(stores),
                        sheet_url=sheet_url,
                        csv_path=str(daily_csv)
                    )
                    summary.email_sent = True
                    logger.info("Daily report email sent successfully")
                    
            except Exception as e:
                logger.error(f"Error uploading to Google Sheets or sending email: {e}", exc_info=True)
                summary.errors.append({
                    'type': 'integration_error',
                    'message': str(e)
                })
        
        # Finalize summary
        summary.finish()
        summary.log_summary()
        
        logger.info("=" * 80)
        logger.info("Daily scraping job completed successfully!")
        logger.info(f"Total products: {summary.products_scraped}, New: {summary.products_new}")
        logger.info("=" * 80)
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        raise
    except Exception as e:
        logger.error(f"Fatal error in daily scraping job: {e}", exc_info=True)
        # Send error notification
        try:
            from .integrations import EmailHandler
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
