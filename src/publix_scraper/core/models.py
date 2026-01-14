"""
Data models for product and store information
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Product:
    """Represents a soda product with all required fields"""
    product_name: str
    product_description: str
    product_identifier: str
    date: date
    price: float
    ounces: float
    price_per_ounce: float
    price_promotion: Optional[str]
    week: int
    store: str
    
    def to_dict(self):
        """Convert to dictionary for CSV/JSON export"""
        return {
            "product_name": self.product_name,
            "product_description": self.product_description,
            "product_identifier": self.product_identifier,
            "date": self.date.isoformat(),
            "price": self.price,
            "ounces": self.ounces,
            "price_per_ounce": self.price_per_ounce,
            "price_promotion": self.price_promotion or "",
            "week": self.week,
            "store": self.store
        }


@dataclass
class Store:
    """Represents a Publix store location"""
    store_id: str
    store_name: str
    address: str
    city: str
    state: str
    zip_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    def __str__(self):
        return f"{self.store_name} - {self.city}, {self.state}"
