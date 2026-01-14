"""
Data storage module for saving scraped product data
Supports CSV, JSON, and Excel formats with batch operations
"""
import csv
import json
from pathlib import Path
from typing import List, Optional, Iterator
from contextlib import contextmanager
import pandas as pd
from datetime import date

from ..core.models import Product
from ..core.config import OUTPUT_FORMAT, OUTPUT_FILE, DATA_DIR, OUTPUT_DIR
from ..utils.exceptions import StorageError
from ..utils.logging_config import get_logger

# Optional Excel support
try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

logger = get_logger(__name__)


class DataStorage:
    """Handles storage of scraped product data"""
    
    def __init__(self, output_file: Optional[Path] = None, format: str = "csv"):
        """
        Initialize data storage
        
        Args:
            output_file: Path to output file
            format: Output format ("csv", "json", or "excel")
        """
        self.format = format.lower()
        self.output_file = output_file or OUTPUT_FILE
        
        # Ensure output directory exists
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize file if it doesn't exist (only for CSV)
        if self.format == "csv" and not self.output_file.exists():
            self._initialize_file()
    
    def _initialize_file(self):
        """Initialize output file with headers"""
        if self.format == "csv":
            with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "product_name", "product_description", "product_identifier",
                    "date", "price", "ounces", "price_per_ounce",
                    "price_promotion", "week", "store"
                ])
                writer.writeheader()
        elif self.format == "json":
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def save_products(self, products: List[Product], append: bool = True):
        """
        Save products to file with batch operations
        
        Args:
            products: List of Product objects
            append: Whether to append to existing file (only for CSV/JSON)
            
        Raises:
            StorageError: If saving fails
        """
        if not products:
            logger.warning("No products to save")
            return
        
        try:
            if self.format == "csv":
                self._save_csv(products, append)
            elif self.format == "json":
                self._save_json(products, append)
            elif self.format == "excel":
                self._save_excel(products, append)
            else:
                raise StorageError(
                    f"Unsupported format: {self.format}",
                    details={"format": self.format, "supported_formats": ["csv", "json", "excel"]}
                )
            
            logger.info(f"Saved {len(products)} products to {self.output_file}")
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(
                f"Unexpected error saving products: {e}",
                details={"file": str(self.output_file), "product_count": len(products)}
            )
    
    def _save_csv(self, products: List[Product], append: bool):
        """
        Save products to CSV file with batch writing
        
        Args:
            products: List of Product objects to save
            append: Whether to append to existing file
        """
        if not products:
            return
        
        mode = 'a' if append and self.output_file.exists() else 'w'
        fieldnames = [
            "product_name", "product_description", "product_identifier",
            "date", "price", "ounces", "price_per_ounce",
            "price_promotion", "week", "store"
        ]
        
        try:
            with open(self.output_file, mode, newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if mode == 'w':
                    writer.writeheader()
                
                # Batch write all products
                writer.writerows([product.to_dict() for product in products])
        except IOError as e:
            raise StorageError(
                f"Error writing to CSV file {self.output_file}: {e}",
                details={"file": str(self.output_file), "product_count": len(products)}
            )
    
    def _save_json(self, products: List[Product], append: bool):
        """
        Save products to JSON file
        
        Args:
            products: List of Product objects to save
            append: Whether to append to existing file
        """
        if not products:
            return
        
        existing_data = []
        
        if append and self.output_file.exists():
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                logger.warning(f"Error reading existing JSON file: {e}. Creating new file.")
                existing_data = []
        
        new_data = [product.to_dict() for product in products]
        all_data = existing_data + new_data
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise StorageError(
                f"Error writing to JSON file {self.output_file}: {e}",
                details={"file": str(self.output_file), "product_count": len(products)}
            )
    
    def _save_excel(self, products: List[Product], append: bool):
        """Save products to Excel file"""
        if not EXCEL_AVAILABLE:
            raise ImportError("openpyxl is required for Excel export. Install with: pip install openpyxl")
        
        # Convert products to DataFrame
        data = [product.to_dict() for product in products]
        df = pd.DataFrame(data)
        
        if append and self.output_file.exists():
            # Load existing data and append
            try:
                existing_df = pd.read_excel(self.output_file)
                df = pd.concat([existing_df, df], ignore_index=True)
            except Exception as e:
                logger.warning(f"Could not append to existing Excel file: {e}. Creating new file.")
        
        # Save to Excel with formatting
        with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Products', index=False)
            
            # Get the worksheet for formatting
            worksheet = writer.sheets['Products']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    def load_products(self) -> List[Product]:
        """Load products from file"""
        if not self.output_file.exists():
            return []
        
        if self.format == "csv":
            return self._load_csv()
        elif self.format == "json":
            return self._load_json()
        elif self.format == "excel":
            return self._load_excel()
        else:
            raise ValueError(f"Unsupported format: {self.format}")
    
    def _load_csv(self) -> List[Product]:
        """Load products from CSV file"""
        products = []
        
        try:
            df = pd.read_csv(self.output_file)
            
            for _, row in df.iterrows():
                product = Product(
                    product_name=row['product_name'],
                    product_description=row.get('product_description', ''),
                    product_identifier=row['product_identifier'],
                    date=pd.to_datetime(row['date']).date(),
                    price=float(row['price']),
                    ounces=float(row['ounces']),
                    price_per_ounce=float(row['price_per_ounce']),
                    price_promotion=row.get('price_promotion') or None,
                    week=int(row['week']),
                    store=row['store']
                )
                products.append(product)
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
        
        return products
    
    def _load_json(self) -> List[Product]:
        """Load products from JSON file"""
        products = []
        
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item in data:
                product = Product(
                    product_name=item['product_name'],
                    product_description=item.get('product_description', ''),
                    product_identifier=item['product_identifier'],
                    date=date.fromisoformat(item['date']),
                    price=float(item['price']),
                    ounces=float(item['ounces']),
                    price_per_ounce=float(item['price_per_ounce']),
                    price_promotion=item.get('price_promotion') or None,
                    week=int(item['week']),
                    store=item['store']
                )
                products.append(product)
        except Exception as e:
            logger.error(f"Error loading JSON: {e}")
        
        return products
    
    def _load_excel(self) -> List[Product]:
        """Load products from Excel file"""
        products = []
        
        if not EXCEL_AVAILABLE:
            raise ImportError("openpyxl is required for Excel import. Install with: pip install openpyxl")
        
        try:
            df = pd.read_excel(self.output_file, sheet_name='Products')
            
            for _, row in df.iterrows():
                product = Product(
                    product_name=row['product_name'],
                    product_description=row.get('product_description', ''),
                    product_identifier=row['product_identifier'],
                    date=pd.to_datetime(row['date']).date(),
                    price=float(row['price']),
                    ounces=float(row['ounces']),
                    price_per_ounce=float(row['price_per_ounce']),
                    price_promotion=row.get('price_promotion') or None,
                    week=int(row['week']),
                    store=row['store']
                )
                products.append(product)
        except Exception as e:
            logger.error(f"Error loading Excel: {e}")
        
        return products
    
    def get_summary_stats(self) -> dict:
        """Get summary statistics of stored data"""
        products = self.load_products()
        
        if not products:
            return {
                "total_products": 0,
                "total_stores": 0,
                "total_weeks": 0,
                "date_range": None
            }
        
        stores = set(p.store for p in products)
        weeks = set(p.week for p in products)
        dates = [p.date for p in products]
        
        return {
            "total_products": len(products),
            "total_stores": len(stores),
            "total_weeks": len(weeks),
            "date_range": {
                "min": min(dates).isoformat() if dates else None,
                "max": max(dates).isoformat() if dates else None
            }
        }
