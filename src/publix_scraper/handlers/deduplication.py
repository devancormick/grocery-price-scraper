"""
Deduplication module for handling unique identifiers
"""
from typing import List, Set, Dict, Tuple
from ..core.models import Product
from .storage import DataStorage
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class DeduplicationHandler:
    """Handles deduplication of product records"""
    
    def __init__(self, storage: DataStorage):
        """
        Initialize deduplication handler
        
        Args:
            storage: DataStorage instance to load existing records
        """
        self.storage = storage
        self.existing_records: Dict[str, Product] = {}
        self._load_existing_records()
    
    def _load_existing_records(self):
        """Load existing records from storage"""
        try:
            existing_products = self.storage.load_products()
            # Create a composite key: product_identifier + store + week + date
            for product in existing_products:
                key = self._generate_key(product)
                self.existing_records[key] = product
            
            logger.info(f"Loaded {len(self.existing_records)} existing records for deduplication")
        except Exception as e:
            logger.warning(f"Could not load existing records for deduplication: {e}")
            self.existing_records = {}
    
    def _generate_key(self, product: Product) -> str:
        """
        Generate a unique key for a product record
        
        Args:
            product: Product object
            
        Returns:
            Unique key string
        """
        # Composite key: identifier + store + week + date
        return f"{product.product_identifier}|{product.store}|{product.week}|{product.date.isoformat()}"
    
    def filter_new_records(self, products: List[Product]) -> Tuple[List[Product], List[Product]]:
        """
        Filter out duplicate records
        
        Args:
            products: List of Product objects to check
            
        Returns:
            Tuple of (new_products, duplicate_products)
        """
        new_products = []
        duplicate_products = []
        
        for product in products:
            key = self._generate_key(product)
            
            if key in self.existing_records:
                duplicate_products.append(product)
            else:
                new_products.append(product)
                # Add to existing records to prevent duplicates within the same batch
                self.existing_records[key] = product
        
        logger.info(f"Deduplication: {len(new_products)} new records, {len(duplicate_products)} duplicates")
        
        return new_products, duplicate_products
    
    def get_existing_product_ids(self) -> Set[str]:
        """Get set of existing product identifiers"""
        return set(p.product_identifier for p in self.existing_records.values())
    
    def get_existing_count(self) -> int:
        """Get count of existing records"""
        return len(self.existing_records)
