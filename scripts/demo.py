"""
Demo script to show scraper functionality with sample data
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import date
from src.publix_scraper.core.models import Product, Store
from src.publix_scraper.handlers import DataStorage

def create_demo_data():
    """Create sample product data to demonstrate the system"""
    
    # Create sample stores
    stores = [
        Store(
            store_id="FL-0001",
            store_name="Publix Super Market",
            address="123 Main St",
            city="Lakeland",
            state="FL",
            zip_code="33801"
        ),
        Store(
            store_id="GA-0001",
            store_name="Publix Super Market",
            address="456 Peach St",
            city="Atlanta",
            state="GA",
            zip_code="30301"
        )
    ]
    
    # Create sample products (based on typical soda products)
    products = []
    
    sample_products = [
        {
            "name": "Coca-Cola Classic",
            "description": "12 - 12 fl oz (355 ml) cans",
            "id": "COKE-12PK-12OZ",
            "price": 6.99,
            "ounces": 144.0,
            "promotion": None
        },
        {
            "name": "Pepsi Cola",
            "description": "12 - 12 fl oz (355 ml) cans",
            "id": "PEPSI-12PK-12OZ",
            "price": 6.49,
            "ounces": 144.0,
            "promotion": "Buy 2 Get 1 Free"
        },
        {
            "name": "Sprite",
            "description": "12 - 12 fl oz (355 ml) cans",
            "id": "SPRITE-12PK-12OZ",
            "price": 5.99,
            "ounces": 144.0,
            "promotion": None
        },
        {
            "name": "Dr Pepper",
            "description": "24 - 12 fl oz (355 ml) cans",
            "id": "DRPEPPER-24PK-12OZ",
            "price": 11.99,
            "ounces": 288.0,
            "promotion": None
        },
        {
            "name": "Mountain Dew",
            "description": "12 - 16.9 fl oz (500 ml) bottles",
            "id": "MTDEW-12PK-16.9OZ",
            "price": 7.49,
            "ounces": 202.8,
            "promotion": None
        },
        {
            "name": "Fanta Orange",
            "description": "12 - 12 fl oz (355 ml) cans",
            "id": "FANTA-12PK-12OZ",
            "price": 5.99,
            "ounces": 144.0,
            "promotion": "Save $1.00"
        }
    ]
    
    # Create products for each store and week
    for week in range(1, 5):  # 4 weeks
        for store in stores:
            for product_data in sample_products:
                price = product_data["price"]
                # Add slight price variation by week
                if week == 2:
                    price *= 0.95  # 5% discount in week 2
                elif week == 3:
                    price *= 1.02  # 2% increase in week 3
                
                product = Product(
                    product_name=product_data["name"],
                    product_description=product_data["description"],
                    product_identifier=product_data["id"],
                    date=date.today(),
                    price=round(price, 2),
                    ounces=product_data["ounces"],
                    price_per_ounce=round(price / product_data["ounces"], 4),
                    price_promotion=product_data["promotion"],
                    week=week,
                    store=f"{store.store_id} - {store.city}, {store.state}"
                )
                products.append(product)
    
    return products, stores

def main():
    """Run demo"""
    print("=" * 60)
    print("Publix Price Scraper - Demo Mode")
    print("=" * 60)
    print()
    
    # Create demo data
    print("Generating sample product data...")
    products, stores = create_demo_data()
    print(f"Created {len(products)} product records")
    print(f"Across {len(stores)} stores")
    print(f"For 4 weeks")
    print()
    
    # Save to storage
    print("Saving data to CSV...")
    storage = DataStorage()
    storage.save_products(products, append=False)
    print(f"Data saved to: {storage.output_file}")
    print()
    
    # Show summary
    print("Data Summary:")
    print("-" * 60)
    stats = storage.get_summary_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    # Show sample products
    print("Sample Products (first 10):")
    print("-" * 60)
    for i, product in enumerate(products[:10], 1):
        print(f"{i}. {product.product_name}")
        print(f"   Store: {product.store}")
        print(f"   Week: {product.week}")
        print(f"   Price: ${product.price:.2f}")
        print(f"   Size: {product.ounces} fl oz")
        print(f"   Price/oz: ${product.price_per_ounce:.4f}")
        if product.price_promotion:
            print(f"   Promotion: {product.price_promotion}")
        print()
    
    print("=" * 60)
    print("Demo completed successfully!")
    print(f"Check {storage.output_file} for the full dataset")
    print("=" * 60)

if __name__ == "__main__":
    main()
