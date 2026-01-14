"""
Database integration for storing scraped data
Supports SQLite (default) and PostgreSQL
"""
import logging
from typing import List, Optional
from pathlib import Path
from sqlalchemy import create_engine, Column, String, Float, Integer, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import date

from ..core.models import Product
from ..core.config import DATA_DIR

logger = logging.getLogger(__name__)

Base = declarative_base()


class ProductRecord(Base):
    """SQLAlchemy model for product records"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(200), nullable=False)
    product_description = Column(Text)
    product_identifier = Column(String(100), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    price = Column(Float, nullable=False)
    ounces = Column(Float, nullable=False)
    price_per_ounce = Column(Float, nullable=False)
    price_promotion = Column(Text)
    week = Column(Integer, nullable=False, index=True)
    store = Column(String(200), nullable=False, index=True)
    
    # Composite unique constraint
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class DatabaseHandler:
    """Handles database operations"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database handler
        
        Args:
            database_url: Database URL (default: SQLite in data directory)
        """
        if not database_url:
            db_path = DATA_DIR / "publix_prices.db"
            database_url = f"sqlite:///{db_path}"
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        logger.info(f"Database initialized: {database_url}")
    
    def save_products(self, products: List[Product], deduplicate: bool = True):
        """
        Save products to database
        
        Args:
            products: List of Product objects
            deduplicate: Whether to skip duplicates
        """
        session = self.SessionLocal()
        saved_count = 0
        duplicate_count = 0
        
        try:
            for product in products:
                # Check for duplicates if enabled
                if deduplicate:
                    existing = session.query(ProductRecord).filter_by(
                        product_identifier=product.product_identifier,
                        store=product.store,
                        week=product.week,
                        date=product.date
                    ).first()
                    
                    if existing:
                        duplicate_count += 1
                        continue
                
                # Create new record
                record = ProductRecord(
                    product_name=product.product_name,
                    product_description=product.product_description,
                    product_identifier=product.product_identifier,
                    date=product.date,
                    price=product.price,
                    ounces=product.ounces,
                    price_per_ounce=product.price_per_ounce,
                    price_promotion=product.price_promotion,
                    week=product.week,
                    store=product.store
                )
                
                session.add(record)
                saved_count += 1
            
            session.commit()
            logger.info(f"Saved {saved_count} products to database ({duplicate_count} duplicates skipped)")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving to database: {e}")
            raise
        finally:
            session.close()
    
    def load_products(self, week: Optional[int] = None, store: Optional[str] = None,
                     start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Product]:
        """
        Load products from database with optional filters
        
        Args:
            week: Filter by week
            store: Filter by store
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            List of Product objects
        """
        session = self.SessionLocal()
        products = []
        
        try:
            query = session.query(ProductRecord)
            
            if week:
                query = query.filter_by(week=week)
            if store:
                query = query.filter_by(store=store)
            if start_date:
                query = query.filter(ProductRecord.date >= start_date)
            if end_date:
                query = query.filter(ProductRecord.date <= end_date)
            
            records = query.all()
            
            for record in records:
                product = Product(
                    product_name=record.product_name,
                    product_description=record.product_description or "",
                    product_identifier=record.product_identifier,
                    date=record.date,
                    price=record.price,
                    ounces=record.ounces,
                    price_per_ounce=record.price_per_ounce,
                    price_promotion=record.price_promotion,
                    week=record.week,
                    store=record.store
                )
                products.append(product)
            
            logger.info(f"Loaded {len(products)} products from database")
            return products
            
        except Exception as e:
            logger.error(f"Error loading from database: {e}")
            return []
        finally:
            session.close()
    
    def get_stats(self) -> dict:
        """Get database statistics"""
        session = self.SessionLocal()
        
        try:
            total = session.query(ProductRecord).count()
            stores = session.query(ProductRecord.store).distinct().count()
            weeks = session.query(ProductRecord.week).distinct().count()
            
            return {
                'total_records': total,
                'unique_stores': stores,
                'unique_weeks': weeks
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
        finally:
            session.close()
