"""
Incremental scraping support - only scrape new or updated records
"""
import logging
from datetime import date, datetime, timedelta
from typing import List, Set, Optional
from ..core.models import Product
from .storage import DataStorage

logger = logging.getLogger(__name__)


class IncrementalScraper:
    """Handles incremental scraping logic"""
    
    def __init__(self, storage: DataStorage):
        """
        Initialize incremental scraper
        
        Args:
            storage: DataStorage instance
        """
        self.storage = storage
        self.existing_records: Set[str] = set()
        self.last_scrape_date: Optional[date] = None
        self._load_existing_data()
    
    def _load_existing_data(self):
        """Load existing records to determine what's already been scraped"""
        try:
            existing_products = self.storage.load_products()
            for product in existing_products:
                # Create composite key
                key = f"{product.product_identifier}|{product.store}|{product.week}|{product.date.isoformat()}"
                self.existing_records.add(key)
            
            if existing_products:
                self.last_scrape_date = max(p.date for p in existing_products)
            
            logger.info(f"Loaded {len(self.existing_records)} existing records for incremental scraping")
        except Exception as e:
            logger.warning(f"Could not load existing data: {e}")
            self.existing_records = set()
    
    def is_new_record(self, product: Product) -> bool:
        """
        Check if a product record is new
        
        Args:
            product: Product object to check
            
        Returns:
            True if record is new
        """
        key = f"{product.product_identifier}|{product.store}|{product.week}|{product.date.isoformat()}"
        return key not in self.existing_records
    
    def filter_new_products(self, products: List[Product]) -> List[Product]:
        """
        Filter to only new products
        
        Args:
            products: List of Product objects
            
        Returns:
            List of new Product objects
        """
        new_products = [p for p in products if self.is_new_record(p)]
        logger.info(f"Incremental filtering: {len(new_products)} new out of {len(products)} total")
        return new_products
    
    def should_scrape_date(self, target_date: date, days_back: int = 7) -> bool:
        """
        Determine if a date should be scraped based on last scrape date
        
        Args:
            target_date: Date to check
            days_back: Number of days to look back for updates
            
        Returns:
            True if date should be scraped
        """
        if not self.last_scrape_date:
            return True
        
        # Always scrape if target date is after last scrape
        if target_date > self.last_scrape_date:
            return True
        
        # Scrape if within lookback window (for updates)
        days_since_scrape = (datetime.now().date() - self.last_scrape_date).days
        if days_since_scrape <= days_back:
            return True
        
        return False
    
    def get_scrape_date_range(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[date]:
        """
        Get list of dates that should be scraped
        
        Args:
            start_date: Start date (default: last scrape date or today)
            end_date: End date (default: today)
            
        Returns:
            List of dates to scrape
        """
        if not end_date:
            end_date = date.today()
        
        if not start_date:
            if self.last_scrape_date:
                start_date = self.last_scrape_date + timedelta(days=1)
            else:
                start_date = end_date
        
        dates = []
        current = start_date
        while current <= end_date:
            if self.should_scrape_date(current):
                dates.append(current)
            current += timedelta(days=1)
        
        return dates
