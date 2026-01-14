"""
Data validation and cleaning module
"""
import re
from typing import List, Dict, Tuple
from datetime import date
from ..core.models import Product
from ..utils.logging_config import get_logger
from ..utils.exceptions import ValidationError

logger = get_logger(__name__)


class DataValidator:
    """Handles data validation and cleaning"""
    
    @staticmethod
    def validate_product(product: Product) -> Tuple[bool, List[str]]:
        """
        Validate a product record
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate product name
        if not product.product_name or len(product.product_name.strip()) == 0:
            errors.append("Missing product name")
        elif len(product.product_name) > 200:
            errors.append(f"Product name too long: {len(product.product_name)} characters")
        
        # Validate product identifier
        if not product.product_identifier or len(product.product_identifier.strip()) == 0:
            errors.append("Missing product identifier")
        
        # Validate price
        if product.price is None:
            errors.append("Missing price")
        elif product.price < 0:
            errors.append(f"Invalid price: {product.price}")
        elif product.price > 10000:  # Sanity check
            errors.append(f"Suspiciously high price: {product.price}")
        
        # Validate ounces (allow 0)
        if product.ounces is None:
            errors.append("Missing ounces")
        elif product.ounces < 0:
            errors.append(f"Invalid ounces: {product.ounces}")
        elif product.ounces > 10000:  # Sanity check
            errors.append(f"Suspiciously high ounces: {product.ounces}")
        
        # Validate price per ounce (can be None or 0 if ounces is 0)
        if product.ounces == 0:
            # If ounces is 0, price_per_ounce can be None or 0
            if product.price_per_ounce is not None and product.price_per_ounce < 0:
                errors.append(f"Invalid price per ounce: {product.price_per_ounce}")
        else:
            # If ounces > 0, price_per_ounce must be valid
            if product.price_per_ounce is None:
                errors.append("Missing price per ounce")
            elif product.price_per_ounce < 0:
                errors.append(f"Invalid price per ounce: {product.price_per_ounce}")
            elif product.price_per_ounce > 10:  # Sanity check
                errors.append(f"Suspiciously high price per ounce: {product.price_per_ounce}")
        
        # Validate date
        if not isinstance(product.date, date):
            errors.append(f"Invalid date type: {type(product.date)}")
        
        # Validate week
        if product.week < 1 or product.week > 52:
            errors.append(f"Invalid week: {product.week}")
        
        # Validate store
        if not product.store or len(product.store.strip()) == 0:
            errors.append("Missing store")
        
        # Cross-validation: price per ounce should match calculation (only if ounces > 0)
        if product.price and product.ounces and product.ounces > 0 and product.price_per_ounce is not None:
            try:
                expected_ppo = product.price / product.ounces
                if abs(product.price_per_ounce - expected_ppo) > 0.01:  # Allow small floating point differences
                    errors.append(f"Price per ounce mismatch: expected {expected_ppo:.4f}, got {product.price_per_ounce:.4f}")
            except (ZeroDivisionError, TypeError):
                # Should not happen since we check ounces > 0, but handle gracefully
                pass
        
        return len(errors) == 0, errors
    
    @staticmethod
    def clean_product(product: Product) -> Product:
        """
        Clean and normalize a product record
        
        Returns:
            Cleaned Product object
        """
        # Clean product name
        if product.product_name:
            product.product_name = product.product_name.strip()
            # Remove extra whitespace
            product.product_name = re.sub(r'\s+', ' ', product.product_name)
        
        # Clean product description
        if product.product_description:
            product.product_description = product.product_description.strip()
            product.product_description = re.sub(r'\s+', ' ', product.product_description)
        
        # Clean product identifier
        if product.product_identifier:
            product.product_identifier = product.product_identifier.strip().upper()
        
        # Round price to 2 decimal places
        if product.price is not None:
            product.price = round(product.price, 2)
        
        # Round ounces to 1 decimal place
        if product.ounces is not None:
            product.ounces = round(product.ounces, 1)
        
        # Recalculate price per ounce (handle division by zero)
        if product.price is not None and product.ounces is not None:
            try:
                if product.ounces > 0:
                    product.price_per_ounce = round(product.price / product.ounces, 4)
                else:
                    # If ounces is 0, set price_per_ounce to None or 0
                    product.price_per_ounce = None
            except (ZeroDivisionError, TypeError):
                product.price_per_ounce = None
        
        # Clean promotion text
        if product.price_promotion:
            if isinstance(product.price_promotion, str):
                product.price_promotion = product.price_promotion.strip()
                if len(product.price_promotion) == 0:
                    product.price_promotion = None
            else:
                product.price_promotion = None
        
        # Clean store
        if product.store:
            product.store = product.store.strip()
        
        return product
    
    @staticmethod
    def validate_and_clean_products(products: List[Product]) -> tuple[List[Product], List[Dict]]:
        """
        Validate and clean a list of products
        
        Returns:
            Tuple of (cleaned_products, validation_errors)
        """
        cleaned_products = []
        validation_errors = []
        
        for idx, product in enumerate(products):
            # Clean first
            cleaned_product = DataValidator.clean_product(product)
            
            # Then validate
            is_valid, errors = DataValidator.validate_product(cleaned_product)
            
            if is_valid:
                cleaned_products.append(cleaned_product)
            else:
                validation_errors.append({
                    'index': idx,
                    'product_identifier': cleaned_product.product_identifier,
                    'product_name': cleaned_product.product_name,
                    'errors': errors
                })
                logger.warning(f"Product validation failed: {cleaned_product.product_identifier} - {errors}")
        
        logger.info(f"Validated {len(products)} products: {len(cleaned_products)} valid, {len(validation_errors)} invalid")
        
        return cleaned_products, validation_errors
