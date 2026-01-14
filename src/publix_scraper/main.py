"""
Main entry point for Publix Price Scraper
"""
import argparse
import time
import sys
from datetime import date
from typing import List, Optional
from pathlib import Path
from tqdm import tqdm

from .core.scraper import PublixScraper
from .core.store_locator import StoreLocator
from .core.models import Store, Product
from .core.config import (
    WEEKS_TO_COLLECT, FLORIDA_STORE_COUNT, GEORGIA_STORE_COUNT,
    OUTPUT_DIR, DATE_FORMAT, validate_configuration, get_config_summary
)
from .handlers import (
    DataStorage, DataValidator, DeduplicationHandler,
    IncrementalScraper, RunSummary
)
from .integrations import (
    GoogleSheetsHandler, EmailHandler, WebhookHandler, DatabaseHandler,
    GOOGLE_SHEETS_AVAILABLE, EMAIL_AVAILABLE, WEBHOOK_AVAILABLE, DATABASE_AVAILABLE
)
from .utils.logging_config import setup_logging, get_logger
from .utils.exceptions import ConfigurationError, ScrapingError

# Setup logging
setup_logging(
    log_level="INFO",
    log_file=Path("logs/scraper.log")
)
logger = get_logger(__name__)


def scrape_week_enhanced(
    week: int,
    stores: List[Store],
    scraper: PublixScraper,
    storage: DataStorage,
    validator: DataValidator,
    deduplicator: DeduplicationHandler,
    incremental: Optional[IncrementalScraper],
    summary: RunSummary,
    database: Optional[DatabaseHandler] = None
) -> tuple[int, int, int]:
    """
    Enhanced scraping with validation, deduplication, and incremental support
    
    Returns:
        Tuple of (total_scraped, new_count, duplicate_count)
    """
    logger.info(f"Starting week {week} scraping for {len(stores)} stores")
    summary.weeks_processed.append(week)
    
    all_products = []
    new_count = 0
    duplicate_count = 0
    
    with tqdm(total=len(stores), desc=f"Week {week}") as pbar:
        for store in stores:
            try:
                products = scraper.scrape_store_products(store, week)
                all_products.extend(products)
                summary.products_scraped += len(products)
                summary.stores_processed += 1
                pbar.update(1)
                
            except Exception as e:
                error_msg = f"Error scraping store {store.store_id}: {e}"
                logger.error(error_msg)
                summary.errors.append({
                    'type': 'scraping_error',
                    'store': store.store_id,
                    'message': str(e)
                })
                pbar.update(1)
                continue
    
    # Validate and clean products
    if all_products:
        validated_products, validation_errors = validator.validate_and_clean_products(all_products)
        summary.products_valid = len(validated_products)
        summary.products_invalid = len(validation_errors)
        summary.validation_errors.extend(validation_errors)
        
        # Incremental filtering
        if incremental:
            validated_products = incremental.filter_new_products(validated_products)
        
        # Deduplication
        new_products, duplicates = deduplicator.filter_new_records(validated_products)
        new_count = len(new_products)
        duplicate_count = len(duplicates)
        
        # Save new products
        if new_products:
            storage.save_products(new_products, append=True)
            
            # Save to database if available
            if database:
                try:
                    database.save_products(new_products, deduplicate=True)
                except Exception as e:
                    logger.error(f"Error saving to database: {e}")
                    summary.errors.append({
                        'type': 'database_error',
                        'message': str(e)
                    })
        
        summary.products_new = new_count
        summary.products_duplicate = duplicate_count
    
    logger.info(f"Week {week} completed: {len(all_products)} scraped, {new_count} new, {duplicate_count} duplicates")
    return len(all_products), new_count, duplicate_count


def main():
    """Enhanced main execution function"""
    parser = argparse.ArgumentParser(
        description='Publix Price Scraper - Comprehensive Web Scraping & Data Automation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scraping
  python -m publix_scraper --week 1 --store-limit 10
  
  # With all features
  python -m publix_scraper --week 1 --output-format excel --incremental
  
  # Test mode
  python -m publix_scraper --store-limit 2 --states FL
        """
    )
    parser.add_argument('--week', type=int, help='Specific week to scrape (1-4)')
    parser.add_argument('--store-limit', type=int, help='Limit number of stores to scrape (for testing)')
    parser.add_argument('--states', nargs='+', choices=['FL', 'GA'], 
                       default=['FL', 'GA'], help='States to scrape')
    parser.add_argument('--use-selenium', action='store_true', 
                       help='Use Selenium for JavaScript-heavy pages')
    parser.add_argument('--skip-google-sheets', action='store_true',
                       help='Skip Google Sheets upload')
    parser.add_argument('--skip-email', action='store_true',
                       help='Skip email notifications')
    parser.add_argument('--skip-database', action='store_true',
                       help='Skip database storage')
    parser.add_argument('--output-format', choices=['csv', 'json', 'excel'],
                       default='csv', help='Output file format')
    parser.add_argument('--incremental', action='store_true',
                       help='Only scrape new/updated records')
    parser.add_argument('--webhook-url', type=str,
                       help='Webhook URL for notifications')
    
    args = parser.parse_args()
    
    # Validate configuration
    config_warnings = validate_configuration()
    if config_warnings:
        logger.warning("Configuration warnings:")
        for warning in config_warnings:
            logger.warning(f"  - {warning}")
    
    # Initialize run summary
    summary = RunSummary()
    
    logger.info("=" * 80)
    logger.info("Initializing Enhanced Publix Price Scraper")
    logger.info("=" * 80)
    
    # Log configuration summary
    config_summary = get_config_summary()
    logger.debug(f"Configuration: {config_summary}")
    
    # Initialize core components
    store_locator = StoreLocator()
    scraper = PublixScraper(use_selenium=args.use_selenium)
    storage = DataStorage(format=args.output_format)
    validator = DataValidator()
    deduplicator = DeduplicationHandler(storage)
    incremental = IncrementalScraper(storage) if args.incremental else None
    
    # Initialize optional integrations
    google_sheets = None
    if GOOGLE_SHEETS_AVAILABLE and not args.skip_google_sheets:
        try:
            google_sheets = GoogleSheetsHandler()
        except Exception as e:
            logger.warning(f"Could not initialize Google Sheets: {e}")
            summary.warnings.append(f"Google Sheets unavailable: {e}")
    
    email_handler = None
    if EMAIL_AVAILABLE and not args.skip_email:
        try:
            email_handler = EmailHandler()
        except Exception as e:
            logger.warning(f"Could not initialize email handler: {e}")
            summary.warnings.append(f"Email unavailable: {e}")
    
    webhook_handler = None
    if WEBHOOK_AVAILABLE and args.webhook_url:
        try:
            webhook_handler = WebhookHandler(args.webhook_url)
        except Exception as e:
            logger.warning(f"Could not initialize webhook handler: {e}")
    
    database = None
    if DATABASE_AVAILABLE and not args.skip_database:
        try:
            database = DatabaseHandler()
        except Exception as e:
            logger.warning(f"Could not initialize database: {e}")
            summary.warnings.append(f"Database unavailable: {e}")
    
    try:
        # Get store locations
        logger.info("Fetching store locations...")
        stores = []
        
        try:
            if 'FL' in args.states:
                fl_stores = store_locator.get_florida_stores()
                stores.extend(fl_stores)
                logger.info(f"Found {len(fl_stores)} Florida stores")
            
            if 'GA' in args.states:
                ga_stores = store_locator.get_georgia_stores()
                stores.extend(ga_stores)
                logger.info(f"Found {len(ga_stores)} Georgia stores")
        except Exception as e:
            logger.warning(f"Error fetching stores: {e}. Using placeholder stores.")
        
        if not stores:
            logger.warning("No stores found. Using placeholder stores for demonstration.")
            stores = [
                Store(store_id=f"FL-{i:04d}", store_name=f"Publix Store {i}",
                      address=f"Address {i}", city="Lakeland", state="FL", zip_code="33801")
                for i in range(1, min(10, FLORIDA_STORE_COUNT + 1))
            ]
            stores.extend([
                Store(store_id=f"GA-{i:04d}", store_name=f"Publix Store {i}",
                      address=f"Address {i}", city="Atlanta", state="GA", zip_code="30301")
                for i in range(1, min(10, GEORGIA_STORE_COUNT + 1))
            ])
        
        if args.store_limit:
            stores = stores[:args.store_limit]
            logger.info(f"Limited to {len(stores)} stores for testing")
        
        # Determine weeks to scrape
        if args.week:
            weeks = [args.week]
        else:
            weeks = list(range(1, WEEKS_TO_COLLECT + 1))
        
        # Scrape each week using context manager for proper cleanup
        total_new = 0
        with scraper:
            for week in weeks:
                total_scraped, new_count, dup_count = scrape_week_enhanced(
                    week, stores, scraper, storage, validator, deduplicator,
                    incremental, summary, database
                )
                total_new += new_count
            
            # Upload to Google Sheets if available
            if google_sheets and new_count > 0:
                try:
                    all_products = storage.load_products()
                    week_products = [p for p in all_products if p.week == week]
                    
                    if week_products:
                        sheet_url, new_count_gs, total_count = google_sheets.create_weekly_tab(
                            week, week_products
                        )
                        summary.google_sheets_uploaded = True
                        logger.info(f"Week {week} data uploaded to Google Sheets: {sheet_url}")
                        
                        # Create weekly CSV backup
                        weekly_csv = OUTPUT_DIR / f"publix_soda_prices_week_{week}.csv"
                        weekly_storage = DataStorage(output_file=weekly_csv, format='csv')
                        weekly_storage.save_products(week_products, append=False)
                        summary.files_created.append(str(weekly_csv))
                        
                        # Send email notification
                        if email_handler:
                            email_handler.send_weekly_report(
                                week=week,
                                product_count=new_count,
                                store_count=len(stores),
                                sheet_url=sheet_url,
                                csv_path=str(weekly_csv)
                            )
                            summary.email_sent = True
                            logger.info(f"Weekly report email sent for week {week}")
                except Exception as e:
                    error_msg = f"Error uploading to Google Sheets or sending email: {e}"
                    logger.error(error_msg)
                    summary.errors.append({
                        'type': 'integration_error',
                        'week': week,
                        'message': str(e)
                    })
            
            # Wait between weeks
            if week < max(weeks):
                time.sleep(60)
        
        # Finalize summary
        summary.finish()
        summary.files_created.append(str(storage.output_file))
        
        # Generate and log summary
        summary.log_summary()
        
        # Save summary to file
        summary_file = OUTPUT_DIR / f"run_summary_{summary.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        summary.save_to_file(summary_file)
        
        # Send webhook if configured
        if webhook_handler:
            try:
                webhook_handler.send_scraping_summary(summary.to_dict())
                summary.webhook_sent = True
            except Exception as e:
                logger.error(f"Error sending webhook: {e}")
        
        # Print final summary
        logger.info("=" * 80)
        logger.info("Scraping completed successfully!")
        logger.info(f"Total products scraped: {summary.products_scraped}")
        # logger.info(f"New products: {summary.products_new}")
        # logger.info(f"Duplicates: {summary.products_duplicate}")
        logger.info(f"Duration: {summary.get_duration()}")
        logger.info("=" * 80)
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        summary.finish()
        summary.errors.append({'type': 'interrupted', 'message': 'User interruption'})
    except (ConfigurationError, ScrapingError) as e:
        logger.error(f"Scraping error: {e.message}", exc_info=True)
        summary.finish()
        summary.errors.append({
            'type': type(e).__name__,
            'message': e.message,
            'details': e.details
        })
        
        # Send error notifications
        if email_handler:
            try:
                email_handler.send_error_notification(str(e.message))
            except Exception as email_err:
                logger.warning(f"Failed to send error email: {email_err}")
        
        if webhook_handler:
            try:
                webhook_handler.send_error_notification(str(e.message), summary.to_dict())
            except Exception as webhook_err:
                logger.warning(f"Failed to send error webhook: {webhook_err}")
        
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        summary.finish()
        summary.errors.append({'type': 'fatal_error', 'message': str(e)})
        
        # Send error notifications
        if email_handler:
            try:
                email_handler.send_error_notification(str(e))
            except Exception as email_err:
                logger.warning(f"Failed to send error email: {email_err}")
        
        if webhook_handler:
            try:
                webhook_handler.send_error_notification(str(e), summary.to_dict())
            except Exception as webhook_err:
                logger.warning(f"Failed to send error webhook: {webhook_err}")
        
        sys.exit(1)
    finally:
        # Cleanup is handled by context manager, but ensure it's closed
        if scraper:
            scraper.close()
        summary.finish()
        summary.save_to_file(OUTPUT_DIR / "latest_run_summary.json")


if __name__ == "__main__":
    main()
