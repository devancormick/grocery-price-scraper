#!/usr/bin/env python3
"""
Generate Weekly Dataset - Preferred Deliverable

This script generates weekly price data for soda products across all Publix stores.
It runs once per week (e.g., on Monday) and creates a weekly tab in the monthly Google Sheet.

The workflow:
- Week 1 of month: Scrape week 1, create "Week 1" tab in current month's sheet
- Week 2 of month: Scrape week 2, create "Week 2" tab in current month's sheet
- Week 3 of month: Scrape week 3, create "Week 3" tab in current month's sheet
- Week 4 of month: Scrape week 4, create "Week 4" tab in current month's sheet

Usage:
    python generate_weekly_dataset.py [--store-limit N] [--week N] [--output-format csv|json|excel]
"""
import sys
import argparse
from pathlib import Path
from datetime import date, datetime
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.publix_scraper.core.store_locator import StoreLocator
from src.publix_scraper.core.scraper import PublixScraper
from src.publix_scraper.core.config import (
    OUTPUT_DIR, DATA_DIR
)
from src.publix_scraper.handlers import (
    DataStorage, DataValidator, DeduplicationHandler,
    IncrementalScraper, RunSummary
)
from src.publix_scraper.integrations import (
    GoogleSheetsHandler, EmailHandler,
    GOOGLE_SHEETS_AVAILABLE, EMAIL_AVAILABLE
)
from src.publix_scraper.utils.logging_config import setup_logging, get_logger
from src.publix_scraper.utils.week_calculator import (
    get_week_of_month, get_month_year_string, is_last_week_of_month
)

# Setup logging
setup_logging(log_level="INFO", log_file=project_root / "logs/weekly_dataset.log")
logger = get_logger(__name__)


def generate_weekly_dataset(
    store_limit: int = None,
    week: int = None,
    output_format: str = "csv",
    start_from: int = 0
):
    """
    Generate weekly dataset by scraping all stores for the current week
    
    Args:
        store_limit: Limit number of stores to scrape (for testing)
        week: Week number (1-4). If None, uses current week of month
        output_format: Output format (csv, json, or excel)
        start_from: Start from store index N (for resuming)
    
    Returns:
        Path to the generated dataset file
    """
    # Determine which week to scrape
    if week is None:
        week = get_week_of_month()
    
    current_date = date.today()
    month_year = get_month_year_string(current_date)
    is_last_week = is_last_week_of_month(current_date)
    
    logger.info("=" * 80)
    logger.info("Generating Weekly Dataset - Preferred Deliverable")
    logger.info("=" * 80)
    logger.info(f"Current date: {current_date}")
    logger.info(f"Week of month: {week}")
    logger.info(f"Month-Year: {month_year}")
    logger.info(f"Is last week of month: {is_last_week}")
    logger.info(f"Output format: {output_format}")
    logger.info(f"Store limit: {store_limit if store_limit else 'All stores'}")
    logger.info("=" * 80)
    
    # Load stores
    logger.info("Loading Publix store locations...")
    store_locator = StoreLocator(use_cache=True)
    all_stores = store_locator.get_all_target_stores()
    
    if start_from > 0:
        all_stores = all_stores[start_from:]
        logger.info(f"Starting from store index {start_from}")
    
    if store_limit:
        all_stores = all_stores[:store_limit]
        logger.info(f"Limited to {len(all_stores)} stores for testing")
    
    fl_stores = [s for s in all_stores if s.state == 'FL']
    ga_stores = [s for s in all_stores if s.state == 'GA']
    
    logger.info(f"Total stores to process: {len(all_stores)}")
    logger.info(f"  - Florida stores: {len(fl_stores)}")
    logger.info(f"  - Georgia stores: {len(ga_stores)}")
    
    # Initialize components
    scraper = PublixScraper(use_selenium=False)  # Use API method (no Selenium needed)
    validator = DataValidator()
    summary = RunSummary()
    
    # Initialize integrations
    google_sheets = None
    email_handler = None
    
    try:
        if GOOGLE_SHEETS_AVAILABLE:
            google_sheets = GoogleSheetsHandler()
            logger.info("[SUCCESS] Google Sheets handler initialized")
    except Exception as e:
        logger.warning(f"Could not initialize Google Sheets: {e}")
        summary.errors.append({'type': 'google_sheets_init', 'message': str(e)})
    
    try:
        if EMAIL_AVAILABLE:
            email_handler = EmailHandler()
            logger.info("[SUCCESS] Email handler initialized")
    except Exception as e:
        logger.warning(f"Could not initialize email handler: {e}")
        summary.errors.append({'type': 'email_init', 'message': str(e)})
    
    # Create weekly dataset storage
    weekly_filename = f"publix_soda_prices_week{week}_{month_year.replace('-', '')}"
    weekly_output = OUTPUT_DIR / f"{weekly_filename}.{output_format}"
    weekly_storage = DataStorage(output_file=weekly_output, format=output_format)
    
    # Temporary storage for incremental collection
    temp_file = DATA_DIR / f"temp_week{week}_{month_year.replace('-', '')}.csv"
    
    # Clean up any existing temp file before starting
    if temp_file.exists():
        try:
            temp_file.unlink()
            logger.info(f"[SUCCESS] Removed existing temporary file: {temp_file.name}")
        except Exception as e:
            logger.warning(f"[WARNING]  Could not remove existing temp file {temp_file.name}: {e}")
    
    temp_storage = DataStorage(
        output_file=temp_file,
        format="csv"
    )
    deduplicator = DeduplicationHandler(temp_storage)
    incremental = IncrementalScraper(temp_storage)
    
    # Collect products for this week
    all_weekly_products = []
    
    logger.info("\n" + "=" * 80)
    logger.info(f"Starting Weekly Data Collection - Week {week}")
    logger.info("=" * 80)
    
    with scraper:
        logger.info(f"\nScraping Week {week} for all stores...")
        
        for idx, store in enumerate(all_stores, start=start_from):
            try:
                logger.info(
                    f"[Week {week}] [{idx+1}/{len(all_stores)}] "
                    f"Scraping {store.store_name} ({store.city}, {store.state})"
                )
                
                products = scraper.scrape_store_products(store, week)
                all_weekly_products.extend(products)
                summary.products_scraped += len(products)
                summary.stores_processed += 1
                
                logger.info(f"  [SUCCESS] Scraped {len(products)} products")
                
            except Exception as e:
                logger.error(f"  [ERROR] Error scraping {store.store_name}: {e}", exc_info=True)
                summary.errors.append({
                    'type': 'store_error',
                    'store': str(store),
                    'week': week,
                    'message': str(e)
                })
                continue
        
        # Validate and clean products for this week
        if all_weekly_products:
            logger.info(f"\nValidating {len(all_weekly_products)} products for week {week}...")
            validated, errors = validator.validate_and_clean_products(all_weekly_products)
            summary.products_valid += len(validated)
            summary.products_invalid += len(errors)
            
            if errors:
                logger.warning(f"  [WARNING]  {len(errors)} products failed validation")
            
            # Incremental filtering (only new products)
            new_products = incremental.filter_new_products(validated)
            
            # Deduplication
            new_products, duplicates = deduplicator.filter_new_records(new_products)
            summary.products_new += len(new_products)
            summary.products_duplicate += len(duplicates)
            
            # Add to weekly collection
            all_weekly_products = new_products
            
            # Save to temporary storage for incremental tracking
            if new_products:
                temp_storage.save_products(new_products, append=True)
                logger.info(f"  [SUCCESS] Added {len(new_products)} new products to collection")
    
    # Generate final weekly dataset
    logger.info("\n" + "=" * 80)
    logger.info("Generating Final Weekly Dataset")
    logger.info("=" * 80)
    
    if not all_weekly_products:
        logger.warning("No products collected. Please check the scraper configuration.")
        return None
    
    # Validate all products one final time
    logger.info(f"Final validation of {len(all_weekly_products)} products...")
    validated_final, final_errors = validator.validate_and_clean_products(all_weekly_products)
    
    if final_errors:
        logger.warning(f"  [WARNING]  {len(final_errors)} products failed final validation")
    
    # Save final weekly dataset
    logger.info(f"Saving weekly dataset to {weekly_output}...")
    weekly_storage.save_products(validated_final, append=False)
    
    # Upload to Google Sheets (weekly tab in monthly sheet)
    sheet_url = None
    new_count = summary.products_new
    total_count = len(validated_final)
    
    if validated_final and google_sheets:
        try:
            logger.info("\n" + "=" * 80)
            logger.info("Uploading to Google Sheets (Weekly Tab in Monthly Sheet)...")
            
            sheet_url, new_count, total_count, sheet_id = google_sheets.create_weekly_tab_in_monthly_sheet(
                week, validated_final, month_year
            )
            summary.google_sheets_uploaded = True
            logger.info(f"[SUCCESS] Data uploaded to Google Sheets: {sheet_url}")
            logger.info(f"   Monthly Sheet: {month_year}")
            logger.info(f"   Week Tab: Week {week}")
            logger.info(f"   New records: {new_count}, Total records: {total_count}")
                
        except Exception as e:
            logger.error(f"Error uploading to Google Sheets: {e}", exc_info=True)
            summary.errors.append({
                'type': 'google_sheets_error',
                'message': str(e)
            })
            logger.warning("[WARNING]  Google Sheets upload failed, but continuing with email...")
    else:
        if not google_sheets:
            logger.warning("Google Sheets handler not available")
        if not validated_final:
            logger.warning("No products to upload")
    
    # Send weekly email report (even if Google Sheets failed)
    if validated_final and email_handler:
        try:
            logger.info("\n" + "=" * 80)
            logger.info("Sending Weekly Email Report...")
            
            # If no sheet URL, use a placeholder or the base sheet URL
            if not sheet_url and google_sheets:
                try:
                    sheet_url = google_sheets.get_sheet_url()
                except:
                    sheet_url = "Google Sheets upload failed - see CSV attachment"
            
            email_sent = email_handler.send_weekly_report(
                week=week,
                product_count=len(validated_final),
                new_count=new_count,
                store_count=summary.stores_processed,
                sheet_url=sheet_url or "N/A - Google Sheets unavailable",
                csv_path=str(weekly_output),
                month_year=month_year
            )
            if email_sent:
                summary.email_sent = True
                logger.info("[SUCCESS] Weekly report email sent")
            else:
                logger.warning("[WARNING]  Email sending failed")
        except Exception as e:
            logger.error(f"Error sending email: {e}", exc_info=True)
            summary.errors.append({
                'type': 'email_error',
                'message': str(e)
            })
    elif not email_handler:
        logger.warning("Email handler not available - skipping email")
    elif not validated_final:
        logger.warning("No products to report - skipping email")
    
    # Generate summary report
    summary.finish()
    summary_file = OUTPUT_DIR / f"{weekly_filename}_summary.json"
    
    summary_data = {
        "dataset_info": {
            "filename": str(weekly_output),
            "format": output_format,
            "generation_date": datetime.now().isoformat(),
            "week": week,
            "month_year": month_year,
            "is_last_week_of_month": is_last_week
        },
        "data_summary": {
            "total_products": len(validated_final),
            "total_stores": len(set(p.store for p in validated_final)),
            "week": week
        },
        "scraping_summary": {
            "stores_processed": summary.stores_processed,
            "products_scraped": summary.products_scraped,
            "products_valid": summary.products_valid,
            "products_new": summary.products_new,
            "products_duplicate": summary.products_duplicate,
            "products_invalid": summary.products_invalid,
            "errors": summary.errors,
            "duration_seconds": summary.get_duration().total_seconds()
        },
        "fields_included": [
            "product_name",
            "product_description",
            "product_identifier",
            "date",
            "price",
            "ounces",
            "price_per_ounce",
            "price_promotion",
            "week",
            "store"
        ]
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Summary report saved to {summary_file}")
    
    # Print final summary
    logger.info("\n" + "=" * 80)
    logger.info("[SUCCESS] Weekly Dataset Generation Complete!")
    logger.info("=" * 80)
    logger.info(f"Dataset file: {weekly_output}")
    logger.info(f"Summary file: {summary_file}")
    logger.info(f"\nDataset Statistics:")
    logger.info(f"  Total products: {len(validated_final)}")
    logger.info(f"  Total stores: {len(set(p.store for p in validated_final))}")
    logger.info(f"  Week: {week}")
    logger.info(f"  Month-Year: {month_year}")
    logger.info("=" * 80)
    
    # Clean up temporary file (already defined earlier, reuse the variable)
    if temp_file.exists():
        try:
            temp_file.unlink()
            logger.info(f"[SUCCESS] Cleaned up temporary file: {temp_file.name}")
        except Exception as e:
            logger.warning(f"[WARNING]  Could not delete temporary file {temp_file.name}: {e}")
    
    return weekly_output


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate weekly dataset - preferred deliverable"
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
        "--output-format",
        choices=["csv", "json", "excel"],
        default="csv",
        help="Output file format (default: csv)"
    )
    parser.add_argument(
        "--start-from",
        type=int,
        default=0,
        help="Start from store index N (for resuming)"
    )
    
    args = parser.parse_args()
    
    try:
        dataset_file = generate_weekly_dataset(
            store_limit=args.store_limit,
            week=args.week,
            output_format=args.output_format,
            start_from=args.start_from
        )
        
        if dataset_file:
            print(f"\n[SUCCESS] Weekly dataset generated successfully!")
            print(f"[FILE] Dataset file: {dataset_file}")
            sys.exit(0)
        else:
            print("\n[ERROR] Failed to generate dataset")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n[WARNING]  Generation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"[ERROR] Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
