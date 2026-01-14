"""
Main scraper module for Publix soda products using API
Rebuilt from scratch using working API test
"""
import re
import time
import random
import json
from datetime import date
from typing import List, Optional, Dict, Any
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..core.models import Product, Store
from ..core.config import (
    PUBLIX_BASE_URL, PUBLIX_DELIVERY_URL, PUBLIX_API_BASE, REQUEST_DELAY, MAX_RETRIES, 
    TIMEOUT, CATEGORY, BASE_DIR
)
from ..utils.exceptions import NetworkError, ParsingError, ScrapingError
from ..utils.retry import retry_network_request
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

# Publix API constants
PUBLIX_SODA_CATEGORY_ID = "0a052223-5cd2-4547-99fa-0e27af38bfdc"
PUBLIX_API_URL = "https://services.publix.com/search/api/search/storeproductssavings/"

# GraphQL query for products
GRAPHQL_QUERY = """query GetStoreProductsSavingsSearchResultAsync($keyword: String, $skip: Int!, $take: Int!, $facetOverrideStr: String, $facets: String, $sortOrder: String, $ispu: Boolean, $categoryID: String, $minMatch: Int!, $boostVarIndex: Int!, $wildcardSearch: Boolean!, $isPreviewSite: Boolean!, $segmentVarIndex: Int!, $getOrderHistory: Boolean!, $filterQuery: String, $reorderItemCodes: [Int!], $intents: [String!], $searchRetryIndex: Int!, $intentVarIndex: Int!, $boostBuryQuery: String, $source: String, $elevatedProducts: [KeyValuePairOfStringAndStringInput!], $couponId: String, $forceElevation: Boolean, $searchVariation: [KeyValuePairOfStringAndStringInput!], $userCoupon: String) {
  storeProductsSavingsSearchResult(
    keyword: $keyword
    skip: $skip
    take: $take
    facetOverrideStr: $facetOverrideStr
    facets: $facets
    sortOrder: $sortOrder
    ispu: $ispu
    categoryID: $categoryID
    minMatch: $minMatch
    boostVarIndex: $boostVarIndex
    wildcardSearch: $wildcardSearch
    isPreviewSite: $isPreviewSite
    segmentVarIndex: $segmentVarIndex
    getOrderHistory: $getOrderHistory
    filterQuery: $filterQuery
    reorderItemCodes: $reorderItemCodes
    intents: $intents
    boostBuryQuery: $boostBuryQuery
    searchRetryIndex: $searchRetryIndex
    intentVarIndex: $intentVarIndex
    source: $source
    elevatedProducts: $elevatedProducts
    couponId: $couponId
    forceElevation: $forceElevation
    searchVariation: $searchVariation
    userCoupon: $userCoupon
  ) {
    storeProducts {
      baseProductId
      itemCode
      title
      shortDescription
      sizeDescription
      savingLine
      onSale
      priceLine
      specialPromotionDescription
      promoMsg
      promoType
      promoValidThruMsg
      originalPriceLine
      inStoreLocation
      storeNbr
    }
    totalCount
  }
}"""


class PublixScraper:
    """Scraper for Publix soda products using API"""
    
    def __init__(self, use_selenium: bool = False):
        """
        Initialize the scraper
        
        Args:
            use_selenium: Not used for API method, kept for compatibility
        """
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy"""
        session = requests.Session()
        
        # Set headers
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
        })
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=REQUEST_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def scrape_store_products(self, store: Store, week: int) -> List[Product]:
        """
        Scrape all soda products for a specific store using API
        
        Args:
            store: Store object
            week: Week number (1-4 for monthly collection)
            
        Returns:
            List of Product objects
        """
        products = []
        current_date = date.today()
        
        logger.info(f"Scraping products for {store} (Week {week})")
        
        try:
            products = self._scrape_products_via_api(store, week, current_date)
            if products:
                logger.info(f"✅ Scraped {len(products)} products via API from {store}")
        except Exception as e:
            logger.error(f"Error scraping store {store.store_id}: {e}", exc_info=True)
        
        return products
    
    def _extract_store_number(self, store: Store) -> Optional[int]:
        """
        Extract store number from store_id (e.g., "FL-1651" -> 1651, "GA-776" -> 776)
        
        Args:
            store: Store object
            
        Returns:
            Store number as integer, or None if cannot extract
        """
        try:
            # Store ID format: "FL-1651" or "GA-776"
            if '-' in store.store_id:
                number_part = store.store_id.split('-')[1]
                return int(number_part)
        except (ValueError, IndexError):
            pass
        return None
    
    @retry_network_request(max_retries=MAX_RETRIES, initial_delay=REQUEST_DELAY)
    def _scrape_products_via_api(self, store: Store, week: int, scrape_date: date) -> List[Product]:
        """
        Scrape products using Publix API with pagination
        Uses take=100, skip=0, 100, 200, 300... to get all products
        
        Args:
            store: Store object
            week: Week number
            scrape_date: Date of scraping
            
        Returns:
            List of Product objects
        """
        store_number = self._extract_store_number(store)
        if not store_number:
            raise ValueError(f"Cannot extract store number from {store.store_id}")
        
        all_products = []
        skip = 0
        take = 100  # API maximum per request
        page = 1
        
        # Headers for API request
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "priority": "u=1, i",
            "publixstore": str(store_number),
            "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "x-src": "WEB_SEARCH_20240506",
            "referer": "https://www.publix.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Paginate through all products: skip=0, 100, 200, 300...
        while True:
            variables = {
                "take": take,
                "skip": skip,
                "sortOrder": "srchViewsMonth desc, srchViewsYear desc",
                "ispu": False,
                "categoryID": PUBLIX_SODA_CATEGORY_ID,
                "keyword": "",
                "facets": "",
                "minMatch": -41,
                "boostVarIndex": 1,
                "wildcardSearch": False,
                "isPreviewSite": False,
                "getOrderHistory": False,
                "filterQuery": "",
                "reorderItemCodes": None,
                "boostBuryQuery": "",
                "elevatedProducts": [],
                "forceElevation": False,
                "searchRetryIndex": 0,
                "source": "WEB_SEARCH",
                "searchVariation": [
                    {"key": "configurable_add_to_cart", "value": "true"},
                    {"key": "boost_field", "value": "A"}
                ],
                "segmentVarIndex": 1,
                "intents": [],
                "userCoupon": None,
                "intentVarIndex": 1
            }
            
            payload = {
                "operationName": "GetStoreProductsSavingsSearchResultAsync",
                "variables": variables,
                "query": GRAPHQL_QUERY
            }
            
            logger.debug(f"API request: store={store_number}, skip={skip}, take={take} (page {page})")
            
            # Make API request
            try:
                response = self.session.post(
                    f"{PUBLIX_API_URL}?keyword=&storeNumber={store_number}&cat={PUBLIX_SODA_CATEGORY_ID}&source=WEB_SEARCH",
                    headers=headers,
                    json=payload,
                    timeout=TIMEOUT
                )
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    logger.warning(f"403 Forbidden for store {store_number}. API may require authentication.")
                    raise NetworkError(f"API access denied for store {store_number}", details={"store_id": store.store_id})
                raise
            
            data = response.json()
            
            # Extract products from GraphQL response
            if 'data' in data and 'storeProductsSavingsSearchResult' in data['data']:
                result = data['data']['storeProductsSavingsSearchResult']
                store_products = result.get('storeProducts', [])
                total_count = result.get('totalCount', 0)
                
                logger.info(f"API page {page}: {len(store_products)} products (skip={skip}, total={total_count})")
                
                # Convert API products to Product objects
                for api_product in store_products:
                    product = self._convert_api_product_to_model(api_product, store, scrape_date, week)
                    if product:
                        all_products.append(product)
                
                # Check if there are more products to fetch
                if len(store_products) == take and skip + take < total_count:
                    # More products available, continue pagination
                    skip += take  # Next: skip=100, 200, 300, etc.
                    page += 1
                    # Respectful delay between API requests
                    time.sleep(random.uniform(1.0, 2.0))
                else:
                    # No more products to fetch
                    logger.info(f"Completed pagination: collected {len(all_products)} products from {page} page(s)")
                    break
            else:
                logger.warning(f"Unexpected API response structure: {list(data.keys())}")
                break
        
        return all_products
    
    def _convert_api_product_to_model(self, api_product: Dict[str, Any], store: Store, 
                                     scrape_date: date, week: int) -> Optional[Product]:
        """
        Convert API product data to Product model
        
        Args:
            api_product: Product data from API
            store: Store object
            scrape_date: Date of scraping
            week: Week number
            
        Returns:
            Product object or None if conversion fails
        """
        try:
            # Extract product name
            product_name = api_product.get('title', '').strip()
            if not product_name:
                return None
            
            # Extract product description
            product_description = api_product.get('sizeDescription', '') or api_product.get('shortDescription', '')
            
            # Extract product identifier (use itemCode or baseProductId)
            product_id = str(api_product.get('itemCode') or api_product.get('baseProductId', ''))
            if not product_id:
                # Fallback: use product name hash
                product_id = str(abs(hash(product_name)))[:10]
            
            # Extract price
            price_line = api_product.get('priceLine', '')
            price = self._parse_price_from_string(price_line)
            
            # Extract ounces from description
            ounces = self._extract_ounces(product_description)
            
            # Calculate price per ounce (handle division by zero)
            try:
                if ounces and ounces > 0:
                    price_per_ounce = round(price / ounces, 4)
                else:
                    price_per_ounce = None  # Cannot calculate if ounces is 0 or None
            except (ZeroDivisionError, TypeError):
                price_per_ounce = None
            
            # Extract promotion
            promotion = (
                api_product.get('promoMsg') or 
                api_product.get('specialPromotionDescription') or 
                api_product.get('savingLine') or
                None
            )
            
            # Create Product object
            product = Product(
                product_name=product_name,
                product_description=product_description or "",
                product_identifier=product_id,
                date=scrape_date,
                price=price,
                ounces=ounces,
                price_per_ounce=price_per_ounce,
                price_promotion=promotion,
                week=week,
                store=f"{store.store_id} - {store.city}, {store.state}"
            )
            
            return product
            
        except Exception as e:
            logger.warning(f"Error converting API product to model: {e}")
            return None
    
    def _parse_price_from_string(self, price_str: str) -> float:
        """
        Parse price from string (e.g., "$11.59", "$6.99/ea", etc.)
        
        Args:
            price_str: Price string
            
        Returns:
            Price as float
        """
        if not price_str:
            return 0.0
        
        # Remove currency symbols and extract numeric value
        price_match = re.search(r'[\d.]+', price_str.replace('$', '').replace(',', ''))
        if price_match:
            try:
                return float(price_match.group())
            except ValueError:
                pass
        
        return 0.0
    
    def _extract_ounces(self, description: str) -> float:
        """Extract ounces from product description"""
        if not description:
            return 0.0
        
        # Priority: bracket format > multi-pack > largest fl oz value > liters > ml
        
        # Pattern 1: Total ounces in square brackets (e.g., "[144 fl oz (4.26 l)]")
        bracket_match = re.search(r'\[(\d+(?:\.\d+)?)\s*fl\s*oz', description, re.IGNORECASE)
        if bracket_match:
            return float(bracket_match.group(1))
        
        # Pattern 2: Multi-pack format (e.g., "12 - 12 fl oz cans" = 144 oz)
        pack_match = re.search(r'(\d+)\s*-\s*(\d+(?:\.\d+)?)\s*fl\s*oz', description, re.IGNORECASE)
        if pack_match:
            count = float(pack_match.group(1))
            size = float(pack_match.group(2))
            total = count * size
            # Verify this looks correct (should be reasonable total)
            if total > 0 and total < 10000:  # Reasonable max
                return total
        
        # Pattern 3: Find all fl oz values and take the largest (handles "2 liter (2 qt 3.6 fl oz) 67.6 fl oz")
        fl_oz_matches = re.findall(r'(\d+(?:\.\d+)?)\s*fl\s*oz', description, re.IGNORECASE)
        if fl_oz_matches:
            # Convert to floats and get the largest (most likely the total volume)
            fl_oz_values = [float(m) for m in fl_oz_matches]
            return max(fl_oz_values)  # Return largest value
        
        # Pattern 4: Liters (e.g., "2 liter" = ~67.6 fl oz)
        liter_match = re.search(r'(\d+(?:\.\d+)?)\s*l(?:iter)?', description, re.IGNORECASE)
        if liter_match:
            liters = float(liter_match.group(1))
            return liters * 33.814  # Convert liters to fl oz
        
        # Pattern 5: Milliliters
        ml_match = re.search(r'(\d+)\s*ml', description, re.IGNORECASE)
        if ml_match:
            ml = float(ml_match.group(1))
            return ml / 29.5735  # Convert to fl oz
        
        return 0.0
    
    def close(self):
        """Clean up resources"""
        if self.session:
            try:
                self.session.close()
            except Exception as e:
                logger.warning(f"Error closing requests session: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False
