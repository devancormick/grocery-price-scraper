"""
Module for loading Publix store locations from stores.json
Rebuilt from scratch without Selenium
"""
import json
import requests
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
    
    def _fetch_stores_from_api(self) -> Dict[str, List[Store]]:
        """
        Fetch ALL stores from Publix store locator API for FL and GA
        Uses multiple coordinate points to ensure complete coverage
        
        Returns:
            Dictionary with 'FL' and 'GA' keys containing lists of Store objects
        """
        stores_dict = {"FL": [], "GA": []}
        api_url = "https://services.publix.com/storelocator/api/v1/stores/"
        
        # Multiple coordinate points across each state to ensure we get ALL stores
        # FL coordinates: covering major regions (Panhandle, North, Central, South)
        fl_coords = [
            {"lat": 30.4383, "lon": -84.2807, "city": "florida"},  # Tallahassee (North FL)
            {"lat": 30.3322, "lon": -81.6557, "city": "florida"},  # Jacksonville (Northeast FL)
            {"lat": 28.5383, "lon": -81.3792, "city": "florida"},  # Orlando (Central FL)
            {"lat": 27.7663, "lon": -82.6404, "city": "florida"},  # Tampa (West Central FL)
            {"lat": 26.1224, "lon": -80.1373, "city": "florida"},  # Fort Lauderdale (Southeast FL)
            {"lat": 25.7617, "lon": -80.1918, "city": "florida"},  # Miami (South FL)
        ]
        
        # GA coordinates: covering major regions (North, Central, South, Coastal)
        ga_coords = [
            {"lat": 33.7490, "lon": -84.3880, "city": "georgia"},  # Atlanta (North GA)
            {"lat": 32.0809, "lon": -81.0912, "city": "georgia"},  # Savannah (Coastal GA)
            {"lat": 32.1656, "lon": -82.9001, "city": "georgia"},  # Statesboro (Central GA)
            {"lat": 30.8518, "lon": -83.2785, "city": "georgia"},  # Valdosta (South GA)
            {"lat": 33.4735, "lon": -82.0105, "city": "georgia"},  # Augusta (East GA)
        ]
        
        state_coords_map = {
            "FL": fl_coords,
            "GA": ga_coords
        }
        
        headers = {
            "accept": "application/geo+json",
            "accept-language": "en-US,en;q=0.9",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "Referer": "https://www.publix.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        }
        
        for state in ["FL", "GA"]:
            all_stores = {}  # Use dict to track unique stores by store_id
            coords_list = state_coords_map[state]
            
            logger.info(f"Fetching ALL {state} stores from Publix API using {len(coords_list)} coordinate points...")
            
            for idx, coords in enumerate(coords_list, 1):
                try:
                    # Use large count and distance to get all stores in area
                    params = {
                        "types": "R,G,H,N,S",  # All store types
                        "count": 1000,  # Large count to get all stores
                        "distance": 200,  # Distance radius in miles
                        "includeOpenAndCloseDates": "true",
                        "city": coords["city"],
                        "latitude": coords["lat"],
                        "longitude": coords["lon"],
                        "isWebsite": "true"
                    }
                    
                    logger.info(f"  [{idx}/{len(coords_list)}] Fetching from {coords['city']} ({coords['lat']}, {coords['lon']})...")
                    response = requests.get(api_url, params=params, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Parse GeoJSON format
                        stores = self._parse_geojson_response(data, state)
                        
                        # Add stores to dict (deduplicate by store_id)
                        for store in stores:
                            all_stores[store.store_id] = store
                        
                        logger.info(f"    Found {len(stores)} stores (total unique: {len(all_stores)})")
                    else:
                        logger.warning(f"    API returned status {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"    Error fetching from coordinate point {idx}: {e}")
                    continue
            
            # Convert dict values to list
            stores_dict[state] = list(all_stores.values())
            logger.info(f"[SUCCESS] Total {state} stores fetched: {len(stores_dict[state])}")
        
        return stores_dict
    
    def _parse_geojson_response(self, data: Dict[str, Any], state: str) -> List[Store]:
        """
        Parse GeoJSON response from Publix API
        
        Args:
            data: GeoJSON response data
            state: State abbreviation
            
        Returns:
            List of Store objects
        """
        stores = []
        
        try:
            # GeoJSON format: {"type": "FeatureCollection", "features": [...]}
            if data.get("type") == "FeatureCollection" and "features" in data:
                for feature in data["features"]:
                    store = self._parse_feature_to_store(feature, state)
                    if store:
                        stores.append(store)
            # Alternative format: direct list
            elif isinstance(data, list):
                for item in data:
                    store = self._parse_feature_to_store(item, state)
                    if store:
                        stores.append(store)
                        
        except Exception as e:
            logger.warning(f"Error parsing GeoJSON response: {e}")
        
        return stores
    
    def _parse_feature_to_store(self, feature: Dict[str, Any], state: str) -> Optional[Store]:
        """
        Parse a GeoJSON feature into a Store object
        
        Args:
            feature: GeoJSON feature object
            state: State abbreviation
            
        Returns:
            Store object or None if parsing fails
        """
        try:
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            coordinates = geometry.get("coordinates", [])
            
            # Extract store information
            store_number = properties.get("storeNumber") or properties.get("storeId") or properties.get("id", "")
            store_name = properties.get("name") or properties.get("storeName") or "Publix"
            address = properties.get("address") or properties.get("addressLine1") or ""
            city = properties.get("city") or ""
            zip_code = str(properties.get("zipCode") or properties.get("zip") or "")
            
            # Get coordinates (GeoJSON format: [longitude, latitude])
            longitude = coordinates[0] if len(coordinates) > 0 else None
            latitude = coordinates[1] if len(coordinates) > 1 else None
            
            # Fallback to properties if coordinates not in geometry
            if latitude is None:
                latitude = properties.get("latitude") or properties.get("lat")
            if longitude is None:
                longitude = properties.get("longitude") or properties.get("lng") or properties.get("lon")
            
            # Format store_id as STATE-NUMBER
            if store_number and not str(store_number).startswith(state):
                store_id = f"{state}-{store_number}"
            else:
                store_id = str(store_number) if store_number else f"{state}-unknown"
            
            return Store(
                store_id=store_id,
                store_name=store_name,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                latitude=float(latitude) if latitude is not None else None,
                longitude=float(longitude) if longitude is not None else None
            )
        except Exception as e:
            logger.warning(f"Error parsing store feature: {e}")
            return None
    
    def _save_stores_to_json(self, stores_dict: Dict[str, List[Store]]) -> bool:
        """
        Save stores dictionary to stores.json file
        
        Args:
            stores_dict: Dictionary with 'FL' and 'GA' keys containing Store objects
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Ensure data directory exists
            STORE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert Store objects to dictionaries
            stores_data = {
                "FL": [self._store_to_dict(store) for store in stores_dict.get("FL", [])],
                "GA": [self._store_to_dict(store) for store in stores_dict.get("GA", [])]
            }
            
            # Save to JSON file
            with open(STORE_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(stores_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[SUCCESS] Saved {len(stores_data['FL'])} FL and {len(stores_data['GA'])} GA stores to {STORE_CACHE_FILE}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving stores to JSON: {e}", exc_info=True)
            return False
    
    def _store_to_dict(self, store: Store) -> Dict[str, Any]:
        """
        Convert Store object to dictionary
        
        Args:
            store: Store object
            
        Returns:
            Dictionary representation of store
        """
        return {
            "store_id": store.store_id,
            "store_name": store.store_name,
            "address": store.address,
            "city": store.city,
            "state": store.state,
            "zip_code": store.zip_code,
            "latitude": store.latitude,
            "longitude": store.longitude
        }
    
    def update_stores_json(self, fetch_if_empty: bool = True) -> bool:
        """
        Update/validate stores.json file
        Creates the file with empty structure if it doesn't exist
        Currently, stores.json is static, so this validates the file exists and is readable
        In the future, this could fetch stores from Publix API or website
        
        Returns:
            bool: True if stores.json is valid and accessible
        """
        logger.info("Validating stores.json...")
        
        # Create stores.json with empty structure if it doesn't exist
        if not STORE_CACHE_FILE.exists():
            logger.warning(f"stores.json not found at {STORE_CACHE_FILE}")
            
            # Try to fetch stores from API if enabled
            if fetch_if_empty:
                logger.info("Attempting to fetch stores from Publix API...")
                stores_dict = self._fetch_stores_from_api()
                
                if len(stores_dict.get("FL", [])) > 0 or len(stores_dict.get("GA", [])) > 0:
                    # Save fetched stores
                    if self._save_stores_to_json(stores_dict):
                        # Clear cache to reload
                        self._stores_cache = None
                        stores = self.get_all_target_stores()
                        logger.info(f"✅ Fetched and saved {len(stores)} stores to stores.json")
                        return True
                else:
                    logger.warning("Could not fetch stores from API. Creating empty file.")
            
            logger.info("Creating empty stores.json file...")
            # Ensure data directory exists
            STORE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Create empty stores.json with proper structure
            empty_stores = {"FL": [], "GA": []}
            try:
                with open(STORE_CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(empty_stores, f, indent=2, ensure_ascii=False)
                logger.info(f"[SUCCESS] Created empty stores.json at {STORE_CACHE_FILE}")
                logger.warning("[WARNING] stores.json is empty. Please populate it with store data before scraping.")
                return False  # Return False because file is empty
            except Exception as e:
                logger.error(f"Failed to create stores.json: {e}", exc_info=True)
                return False
        
        try:
            # Validate the file can be loaded
            stores = self.get_all_target_stores()
            if len(stores) == 0:
                logger.warning("stores.json exists but contains no stores")
                
                # Try to fetch stores if enabled
                if fetch_if_empty:
                    logger.info("Attempting to fetch stores from Publix API...")
                    stores_dict = self._fetch_stores_from_api()
                    
                    if len(stores_dict.get("FL", [])) > 0 or len(stores_dict.get("GA", [])) > 0:
                        if self._save_stores_to_json(stores_dict):
                            # Clear cache to reload
                            self._stores_cache = None
                            stores = self.get_all_target_stores()
                            logger.info(f"[SUCCESS] Fetched and saved {len(stores)} stores to stores.json")
                            return True
                
                return False
            
            logger.info(f"[SUCCESS] stores.json validated: {len(stores)} stores found")
            return True
            
        except Exception as e:
            logger.error(f"Error validating stores.json: {e}", exc_info=True)
            return False
