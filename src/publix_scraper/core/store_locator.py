"""
Module for locating and managing Publix store locations
"""
import requests
import json
import time
from typing import List, Optional, Dict, Any
from ..core.models import Store
from ..core.config import PUBLIX_API_BASE, REQUEST_DELAY, MAX_RETRIES, TIMEOUT
from ..utils.exceptions import NetworkError
from ..utils.retry import retry_network_request
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class StoreLocator:
    """Handles Publix store location discovery with retry logic"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        })
    
    @retry_network_request(max_retries=MAX_RETRIES, initial_delay=REQUEST_DELAY)
    def get_stores_by_state(self, state: str) -> List[Store]:
        """
        Get all Publix stores in a given state
        
        Args:
            state: State abbreviation (e.g., "FL", "GA")
            
        Returns:
            List of Store objects
            
        Raises:
            NetworkError: If network request fails
        """
        stores = []
        
        # Publix store locator API endpoint
        # Note: This is a placeholder - actual implementation may need to
        # use the Publix website's store locator or API
        url = f"{PUBLIX_API_BASE}/v1/stores"
        
        params = {
            "state": state,
            "limit": 1000  # Adjust based on actual API limits
        }
        
        try:
            response = self.session.get(url, params=params, timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                stores = self._parse_store_data(data, state)
            elif response.status_code == 404:
                # If API doesn't exist, use alternative method
                logger.warning(f"API endpoint not found for {state}, using website fallback")
                stores = self._get_stores_from_website(state)
            else:
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching stores for {state}: {e}. Using website fallback.")
            stores = self._get_stores_from_website(state)
        
        return stores
    
    def _parse_store_data(self, data: Dict[str, Any], state: str) -> List[Store]:
        """
        Parse store data from API response
        
        Args:
            data: API response data
            state: State abbreviation
            
        Returns:
            List of Store objects
        """
        stores = []
        
        # Adjust parsing based on actual API response structure
        if isinstance(data, dict) and "stores" in data:
            store_list = data["stores"]
        elif isinstance(data, list):
            store_list = data
        else:
            logger.warning(f"Unexpected data format for {state} stores")
            return stores
        
        for store_data in store_list:
            try:
                store = Store(
                    store_id=str(store_data.get("id", "")),
                    store_name=store_data.get("name", ""),
                    address=store_data.get("address", ""),
                    city=store_data.get("city", ""),
                    state=state,
                    zip_code=str(store_data.get("zip", "")),
                    latitude=store_data.get("latitude"),
                    longitude=store_data.get("longitude")
                )
                stores.append(store)
            except Exception as e:
                logger.warning(f"Error parsing store data: {e}")
                continue
        
        return stores
    
    def _get_stores_from_website(self, state: str) -> List[Store]:
        """
        Fallback method to get stores from Publix website
        This would involve scraping the store locator page
        
        Args:
            state: State abbreviation
            
        Returns:
            List of Store objects (empty list as placeholder)
        """
        stores = []
        
        # This is a placeholder implementation
        # In practice, you would:
        # 1. Navigate to Publix store locator
        # 2. Search by state
        # 3. Extract store information from results
        # 4. Handle pagination if needed
        
        logger.info(f"Using website scraping fallback for {state} stores")
        logger.debug("Website scraping implementation required")
        
        return stores
    
    def close(self):
        """Clean up resources"""
        if self.session:
            try:
                self.session.close()
            except Exception as e:
                logger.warning(f"Error closing session: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False
    
    def get_florida_stores(self) -> List[Store]:
        """Get all Florida stores"""
        return self.get_stores_by_state("FL")
    
    def get_georgia_stores(self) -> List[Store]:
        """Get all Georgia stores"""
        return self.get_stores_by_state("GA")
    
    def get_all_target_stores(self) -> List[Store]:
        """Get all stores in Florida and Georgia"""
        fl_stores = self.get_florida_stores()
        ga_stores = self.get_georgia_stores()
        return fl_stores + ga_stores
