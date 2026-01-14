"""
Module for loading Publix store locations from stores.json
Rebuilt from scratch without Selenium
"""
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..core.models import Store
from ..core.config import DATA_DIR
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

# Store cache file
STORE_CACHE_FILE = DATA_DIR / "stores.json"


class StoreLocator:
    """Loads Publix store locations from stores.json file"""
    
    def __init__(self, use_cache: bool = True):
        """
        Initialize store locator
        
        Args:
            use_cache: Whether to use cached store list (always True, loads from stores.json)
        """
        self.use_cache = use_cache
        self._stores_cache: Optional[Dict[str, List[Store]]] = None
    
    def _load_stores_from_json(self) -> Dict[str, List[Store]]:
        """
        Load stores from stores.json file
        
        Returns:
            Dictionary with 'FL' and 'GA' keys containing lists of Store objects
        """
        if not STORE_CACHE_FILE.exists():
            logger.error(f"Store file not found: {STORE_CACHE_FILE}")
            return {"FL": [], "GA": []}
        
        try:
            with open(STORE_CACHE_FILE, 'r', encoding='utf-8') as f:
                stores_data = json.load(f)
            
            stores_dict = {}
            
            # Load Florida stores
            if 'FL' in stores_data:
                fl_stores = [self._dict_to_store(store_dict) for store_dict in stores_data['FL']]
                stores_dict['FL'] = fl_stores
                logger.info(f"Loaded {len(fl_stores)} FL stores from {STORE_CACHE_FILE}")
            else:
                stores_dict['FL'] = []
            
            # Load Georgia stores
            if 'GA' in stores_data:
                ga_stores = [self._dict_to_store(store_dict) for store_dict in stores_data['GA']]
                stores_dict['GA'] = ga_stores
                logger.info(f"Loaded {len(ga_stores)} GA stores from {STORE_CACHE_FILE}")
            else:
                stores_dict['GA'] = []
            
            return stores_dict
            
        except Exception as e:
            logger.error(f"Error loading stores from {STORE_CACHE_FILE}: {e}", exc_info=True)
            return {"FL": [], "GA": []}
    
    def _dict_to_store(self, store_dict: Dict[str, Any]) -> Store:
        """
        Convert dictionary to Store object
        
        Args:
            store_dict: Dictionary with store data
            
        Returns:
            Store object
        """
        return Store(
            store_id=store_dict.get('store_id', ''),
            store_name=store_dict.get('store_name', ''),
            address=store_dict.get('address', ''),
            city=store_dict.get('city', ''),
            state=store_dict.get('state', ''),
            zip_code=store_dict.get('zip_code', ''),
            latitude=store_dict.get('latitude'),
            longitude=store_dict.get('longitude')
        )
    
    def _get_cached_stores(self) -> Dict[str, List[Store]]:
        """
        Get cached stores (loads from JSON if not already loaded)
        
        Returns:
            Dictionary with 'FL' and 'GA' keys containing lists of Store objects
        """
        if self._stores_cache is None:
            self._stores_cache = self._load_stores_from_json()
        return self._stores_cache
    
    def get_stores_by_state(self, state: str) -> List[Store]:
        """
        Get stores for a specific state
        
        Args:
            state: State abbreviation ('FL' or 'GA')
            
        Returns:
            List of Store objects
        """
        stores_dict = self._get_cached_stores()
        return stores_dict.get(state.upper(), [])
    
    def get_florida_stores(self) -> List[Store]:
        """Get all Florida stores"""
        return self.get_stores_by_state("FL")
    
    def get_georgia_stores(self) -> List[Store]:
        """Get all Georgia stores"""
        return self.get_stores_by_state("GA")
    
    def get_all_target_stores(self) -> List[Store]:
        """Get all stores in Florida and Georgia"""
        stores_dict = self._get_cached_stores()
        fl_stores = stores_dict.get('FL', [])
        ga_stores = stores_dict.get('GA', [])
        all_stores = fl_stores + ga_stores
        logger.info(f"Total stores: {len(all_stores)} (FL: {len(fl_stores)}, GA: {len(ga_stores)})")
        return all_stores
    
    def get_store_by_id(self, store_id: str) -> Optional[Store]:
        """
        Get a specific store by store_id
        
        Args:
            store_id: Store ID (e.g., 'FL-1651')
            
        Returns:
            Store object or None if not found
        """
        stores_dict = self._get_cached_stores()
        all_stores = stores_dict.get('FL', []) + stores_dict.get('GA', [])
        
        for store in all_stores:
            if store.store_id == store_id:
                return store
        
        return None
    
    def update_stores_json(self) -> bool:
        """
        Update/validate stores.json file
        Currently, stores.json is static, so this validates the file exists and is readable
        In the future, this could fetch stores from Publix API or website
        
        Returns:
            bool: True if stores.json is valid and accessible
        """
        logger.info("Validating stores.json...")
        
        if not STORE_CACHE_FILE.exists():
            logger.error(f"stores.json not found at {STORE_CACHE_FILE}")
            return False
        
        try:
            # Validate the file can be loaded
            stores = self.get_all_target_stores()
            if len(stores) == 0:
                logger.warning("stores.json exists but contains no stores")
                return False
            
            logger.info(f"✅ stores.json validated: {len(stores)} stores found")
            return True
            
        except Exception as e:
            logger.error(f"Error validating stores.json: {e}", exc_info=True)
            return False
