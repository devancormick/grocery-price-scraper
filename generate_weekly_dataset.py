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
from datetime import date, datetime, timedelta
import json
import time

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
    all_validated_products = []  # Store all validated products (not just new ones)
    
    # Chunk configuration
    CSV_UPDATE_INTERVAL = 20  # Update CSV every 20 stores
    SHEETS_UPDATE_INTERVAL = 20  # Update Google Sheets every 20 stores
    EMAIL_UPDATE_INTERVAL = 500  # Send email update every 500 stores
    
    # Progress tracking
    chunk_products = []  # Products collected in current chunk
    start_time = time.time()
    store_times = []  # Track time per store for ETA calculation
    last_email_store_count = 0
    first_sheets_update = True  # Track if this is the first Google Sheets update
    
    logger.info("\n" + "=" * 80)
    logger.info(f"Starting Weekly Data Collection - Week {week}")
    logger.info("=" * 80)
    logger.info(f"Chunk update intervals:")
    logger.info(f"  - CSV update: every {CSV_UPDATE_INTERVAL} stores")
    logger.info(f"  - Google Sheets update: every {SHEETS_UPDATE_INTERVAL} stores")
    logger.info(f"  - Email progress update: every {EMAIL_UPDATE_INTERVAL} stores")
    logger.info("=" * 80)
    
    # Initialize Google Sheets tab if available
    sheet_url = None
    worksheet = None
    if google_sheets:
        try:
            monthly_sheet, sheet_id = google_sheets.get_or_create_monthly_sheet(month_year)
            tab_name = f"{month_year} Week {week}"
            try:
                worksheet = monthly_sheet.worksheet(tab_name)
                logger.info(f"Using existing Google Sheets tab: {tab_name}")
                # Clear existing data for fresh start
                worksheet.clear()
                logger.info(f"Cleared existing data in tab: {tab_name}")
            except:
                worksheet = monthly_sheet.add_worksheet(
                    title=tab_name,
                    rows=1000,
                    cols=10
                )
                logger.info(f"Created new Google Sheets tab: {tab_name}")
            
            # Write header (always write header for fresh start)
            header = google_sheets.format_products_for_sheet([])[0]
            worksheet.update('A1', [header])
            worksheet.format('A1:J1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={worksheet.id}"
        except Exception as e:
            logger.warning(f"Could not initialize Google Sheets tab: {e}")
            google_sheets = None
    
    with scraper:
        logger.info(f"\nScraping Week {week} for all stores...")
        
        for idx, store in enumerate(all_stores, start=start_from):
            store_start_time = time.time()
            
            try:
                logger.info(
                    f"[Week {week}] [{idx+1}/{len(all_stores)}] "
                    f"Scraping {store.store_name} ({store.city}, {store.state})"
                )
                
                products = scraper.scrape_store_products(store, week)
                all_weekly_products.extend(products)
                chunk_products.extend(products)
                summary.products_scraped += len(products)
                summary.stores_processed += 1
                
                # Track time per store
                store_time = time.time() - store_start_time
                store_times.append(store_time)
                
                logger.info(f"  [SUCCESS] Scraped {len(products)} products in {store_time:.1f}s")
                
                # Update CSV and Google Sheets every CSV_UPDATE_INTERVAL stores
                if (idx + 1) % CSV_UPDATE_INTERVAL == 0:
                    if chunk_products:
                        # Validate chunk products
                        validated_chunk, _ = validator.validate_and_clean_products(chunk_products)
                        if validated_chunk:
                            # Filter new products
                            new_chunk = incremental.filter_new_products(validated_chunk)
                            # Deduplicate
                            new_chunk, _ = deduplicator.filter_new_records(new_chunk)
                            
                            if new_chunk:
                                # Update CSV
                                weekly_storage.save_products(new_chunk, append=True)
                                logger.info(f"  [CSV UPDATE] Updated CSV with {len(new_chunk)} products from {CSV_UPDATE_INTERVAL} stores")
                                
                                # Update Google Sheets
                                if google_sheets and worksheet:
                                    try:
                                        rows = google_sheets.format_products_for_sheet(new_chunk)
                                        
                                        if first_sheets_update:
                                            # First update: overwrite with header + data
                                            worksheet.update('A1', rows)
                                            logger.info(f"  [SHEETS UPDATE] First update: Wrote {len(new_chunk)} products to Google Sheets (overwrite)")
                                            first_sheets_update = False
                                        else:
                                            # Subsequent updates: append data only (no header)
                                            rows = rows[1:]  # Remove header
                                            worksheet.append_rows(rows)
                                            logger.info(f"  [SHEETS UPDATE] Updated Google Sheets with {len(new_chunk)} products (append)")
                                    except Exception as e:
                                        logger.warning(f"  [WARNING] Could not update Google Sheets: {e}")
                                
                                chunk_products = []  # Clear chunk after processing
                
                # Send email progress update every EMAIL_UPDATE_INTERVAL stores
                if email_handler and (idx + 1) % EMAIL_UPDATE_INTERVAL == 0:
                    try:
                        # Calculate progress
                        stores_completed = idx + 1
                        stores_remaining = len(all_stores) - stores_completed
                        progress_percent = (stores_completed / len(all_stores)) * 100
                        
                        # Calculate ETA
                        if store_times:
                            avg_time_per_store = sum(store_times) / len(store_times)
                            estimated_remaining_seconds = avg_time_per_store * stores_remaining
                            estimated_remaining = timedelta(seconds=int(estimated_remaining_seconds))
                            
                            # Format ETA
                            hours = estimated_remaining.seconds // 3600
                            minutes = (estimated_remaining.seconds % 3600) // 60
                            if estimated_remaining.days > 0:
                                eta_str = f"{estimated_remaining.days} day(s), {hours}h {minutes}m"
                            else:
                                eta_str = f"{hours}h {minutes}m"
                        else:
                            eta_str = "Calculating..."
                        
                        # Get current product count
                        current_products = len(all_weekly_products)
                        
                        # Send progress email
                        email_handler.send_progress_update(
                            week=week,
                            stores_completed=stores_completed,
                            stores_total=len(all_stores),
                            stores_remaining=stores_remaining,
                            progress_percent=progress_percent,
                            products_found=current_products,
                            estimated_remaining=eta_str,
                            sheet_url=sheet_url or "N/A",
                            month_year=month_year
                        )
                        logger.info(f"  [EMAIL UPDATE] Sent progress email: {stores_completed}/{len(all_stores)} stores ({progress_percent:.1f}%)")
                        last_email_store_count = stores_completed
                    except Exception as e:
                        logger.warning(f"  [WARNING] Could not send progress email: {e}")
                
            except Exception as e:
                logger.error(f"  [ERROR] Error scraping {store.store_name}: {e}", exc_info=True)
                summary.errors.append({
                    'type': 'store_error',
                    'store': str(store),
                    'week': week,
                    'message': str(e)
                })
                continue
        
        # Process remaining chunk products (if any stores didn't complete a full chunk)
        if chunk_products:
            validated_chunk, _ = validator.validate_and_clean_products(chunk_products)
            if validated_chunk:
                new_chunk = incremental.filter_new_products(validated_chunk)
                new_chunk, _ = deduplicator.filter_new_records(new_chunk)
                
                if new_chunk:
                    # Update CSV
                    weekly_storage.save_products(new_chunk, append=True)
                    logger.info(f"  [CSV UPDATE] Final CSV update with {len(new_chunk)} products from remaining stores")
                    
                    # Update Google Sheets
                    if google_sheets and worksheet:
                        try:
                            rows = google_sheets.format_products_for_sheet(new_chunk)
                            
                            if first_sheets_update:
                                # First update: overwrite with header + data
                                worksheet.update('A1', rows)
                                logger.info(f"  [SHEETS UPDATE] Final update (first): Wrote {len(new_chunk)} products to Google Sheets (overwrite)")
                                first_sheets_update = False
                            else:
                                # Subsequent update: append data only (no header)
                                rows = rows[1:]  # Remove header
                                worksheet.append_rows(rows)
                                logger.info(f"  [SHEETS UPDATE] Final Google Sheets update with {len(new_chunk)} products (append)")
                        except Exception as e:
                            logger.warning(f"  [WARNING] Could not update Google Sheets: {e}")
        
        # Validate and clean products for this week
        if all_weekly_products:
            logger.info(f"\nValidating {len(all_weekly_products)} products for week {week}...")
            validated, errors = validator.validate_and_clean_products(all_weekly_products)
            summary.products_valid += len(validated)
            summary.products_invalid += len(errors)
            
            if errors:
                logger.warning(f"  [WARNING]  {len(errors)} products failed validation")
            
            # Store all validated products for final CSV (before filtering)
            all_validated_products = validated
            
            # Incremental filtering (only new products) - for tracking purposes
            new_products = incremental.filter_new_products(validated)
            
            # Deduplication
            new_products, duplicates = deduplicator.filter_new_records(new_products)
            summary.products_new += len(new_products)
            summary.products_duplicate += len(duplicates)
            
            # Save to temporary storage for incremental tracking
            if new_products:
                temp_storage.save_products(new_products, append=True)
                logger.info(f"  [SUCCESS] Added {len(new_products)} new products to collection")
    
    # Generate final weekly dataset
    logger.info("\n" + "=" * 80)
    logger.info("Generating Final Weekly Dataset")
    logger.info("=" * 80)
    
    # Use all validated products (not just new ones) for final CSV
    if not all_validated_products and not all_weekly_products:
        logger.warning("No products collected. Please check the scraper configuration.")
        return None
    
    # Use validated products if available, otherwise validate all weekly products
    if all_validated_products:
        validated_final = all_validated_products
        logger.info(f"Using {len(validated_final)} validated products for final dataset")
    else:
        # Fallback: validate all weekly products
        logger.info(f"Final validation of {len(all_weekly_products)} products...")
        validated_final, final_errors = validator.validate_and_clean_products(all_weekly_products)
        if final_errors:
            logger.warning(f"  [WARNING]  {len(final_errors)} products failed final validation")
    
    # Save final weekly dataset (overwrite with complete dataset)
    logger.info(f"Saving final weekly dataset to {weekly_output}...")
    weekly_storage.save_products(validated_final, append=False)
    
    # Google Sheets was already updated incrementally, so we don't need to overwrite
    # Just ensure we have the sheet URL for the final email
    new_count = summary.products_new
    total_count = len(validated_final)
    
    if not sheet_url and google_sheets:
        try:
            sheet_url = google_sheets.get_sheet_url()
        except:
            pass
    
    if google_sheets and worksheet:
        summary.google_sheets_uploaded = True
        logger.info(f"[SUCCESS] Google Sheets was updated incrementally during scraping")
        logger.info(f"   Sheet URL: {sheet_url}")
        logger.info(f"   Total records: {total_count}")
    
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
