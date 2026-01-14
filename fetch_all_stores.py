#!/usr/bin/env python3
"""
Script to fetch ALL Publix stores for FL and GA and update stores.json
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.publix_scraper.core.store_locator import StoreLocator
from src.publix_scraper.core.config import DATA_DIR
from src.publix_scraper.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging(log_level="INFO", log_file=project_root / "logs/fetch_stores.log")
logger = get_logger(__name__)


def main():
    """Fetch all stores and update stores.json"""
    logger.info("=" * 80)
    logger.info("Fetching ALL Publix Stores for FL and GA")
    logger.info("=" * 80)
    
    try:
        store_locator = StoreLocator(use_cache=True)
        
        # Fetch all stores from API
        logger.info("Starting store fetch from Publix API...")
        stores_dict = store_locator._fetch_stores_from_api()
        
        # Save stores to JSON
        if store_locator._save_stores_to_json(stores_dict):
            logger.info("=" * 80)
            logger.info("[SUCCESS] Successfully fetched and saved all stores!")
            logger.info(f"   FL stores: {len(stores_dict.get('FL', []))}")
            logger.info(f"   GA stores: {len(stores_dict.get('GA', []))}")
            logger.info(f"   Total stores: {len(stores_dict.get('FL', [])) + len(stores_dict.get('GA', []))}")
            logger.info(f"   Saved to: {DATA_DIR / 'stores.json'}")
            logger.info("=" * 80)
            return True
        else:
            logger.error("[ERROR] Failed to save stores to JSON")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] Error fetching stores: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n[WARNING]  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"[ERROR] Fatal error: {e}", exc_info=True)
        sys.exit(1)

