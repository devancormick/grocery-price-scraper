"""
Main scraper module for Publix soda products
"""
import re
import time
from datetime import date
from typing import List, Optional
from contextlib import contextmanager
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Optional Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from ..core.models import Product, Store
from ..core.config import (
    PUBLIX_BASE_URL, PUBLIX_DELIVERY_URL, REQUEST_DELAY, MAX_RETRIES, 
    TIMEOUT, CATEGORY
)
from ..utils.exceptions import NetworkError, ParsingError, ScrapingError
from ..utils.retry import retry_network_request
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class PublixScraper:
    """Scraper for Publix soda products with retry logic and connection pooling"""
    
    def __init__(self, use_selenium: bool = True):
        """
        Initialize the scraper
        
        Args:
            use_selenium: Whether to use Selenium for JavaScript-heavy pages
        """
        self.use_selenium = use_selenium
        self.session = self._create_session()
        self.driver = None
        
        if use_selenium:
            self._init_selenium()
    
    def _create_session(self) -> requests.Session:
        """
        Create a requests session with retry strategy and connection pooling
        
        Returns:
            Configured requests Session
        """
        session = requests.Session()
        
        # Set headers
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
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
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver"""
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium not available. Falling back to requests.")
            self.use_selenium = False
            return
            
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Selenium WebDriver initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Selenium: {e}. Falling back to requests.")
            self.use_selenium = False
    
    def scrape_store_products(self, store: Store, week: int) -> List[Product]:
        """
        Scrape all soda products for a specific store
        
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
            # Get product listings for soda category
            product_urls = self._get_product_urls(store, CATEGORY)
            
            for url in product_urls:
                try:
                    product = self._scrape_product_details(url, store, current_date, week)
                    if product:
                        products.append(product)
                    time.sleep(REQUEST_DELAY)
                except (NetworkError, ParsingError) as e:
                    logger.warning(f"Error scraping product from {url}: {e.message}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error scraping product from {url}: {e}", exc_info=True)
                    continue
                    
        except (NetworkError, ParsingError) as e:
            logger.error(f"Error scraping store {store.store_id}: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error scraping store {store.store_id}: {e}", exc_info=True)
        
        logger.info(f"Scraped {len(products)} products from {store}")
        return products
    
    def _get_location_param(self, store: Store) -> str:
        """
        Get location parameter for Publix delivery URLs
        Uses ZIP code or address for location-based pricing
        
        Args:
            store: Store object with location information
            
        Returns:
            Location string (ZIP code or address)
        """
        # Prefer ZIP code, fallback to city/state
        if store.zip_code:
            return store.zip_code
        elif store.city and store.state:
            return f"{store.city}, {store.state}"
        else:
            return store.address if store.address else "33801"  # Default to Lakeland, FL
    
    @retry_network_request(max_retries=MAX_RETRIES, initial_delay=REQUEST_DELAY)
    def _get_product_urls(self, store: Store, category: str) -> List[str]:
        """
        Get list of product URLs for a category in a store
        
        Based on Publix scraping strategy:
        - Uses delivery.publix.com (Instacart platform)
        - Collection URLs like: /store/publix/collections/rc-beverages-soda
        - Requires location parameter (address/ZIP) for store-specific pricing
        - Pages are JavaScript-heavy, requiring Selenium for rendering
        
        Args:
            store: Store object
            category: Product category (e.g., "soda")
            
        Returns:
            List of product URLs
            
        Raises:
            NetworkError: If network request fails
            ParsingError: If HTML parsing fails
        """
        # Use Publix delivery site which shows prices with location
        # delivery.publix.com requires location parameter to show prices
        # Based on Apify Publix scraper pattern: collection URLs + location
        
        location = self._get_location_param(store)
        base_url = PUBLIX_DELIVERY_URL
        
        # URL patterns to try (in order of preference)
        # Following Apify Publix scraper pattern: collection URLs with location
        # Example: {"url": ".../collections/rc-bogo-dry-grocery", "location": "2300 Griffin Road"}
        url_patterns = [
            f"{base_url}/store/publix/collections/rc-beverages-soda?location={location}",  # Primary: Soda collection with location
            f"{base_url}/store/publix/collections/rc-beverages-soda",  # Fallback: Soda collection without location
            f"{base_url}/store/publix/collections/rc-beverages?location={location}",  # All beverages with location
            f"{base_url}/store/publix/collections/rc-beverages",  # All beverages
            f"{base_url}/store/publix/search?q=soda&location={location}",  # Search with location
            f"{base_url}/store/publix/search?q=soda",  # Search without location
        ]
        
        # Try each URL pattern until one works
        for pattern_idx, search_url in enumerate(url_patterns):
            try:
                logger.debug(f"Trying URL pattern {pattern_idx + 1}: {search_url}")
                urls = []
                
                if self.use_selenium and self.driver:
                    # Navigate to collection page
                    logger.debug(f"Loading page with Selenium: {search_url}")
                    self.driver.get(search_url)
                    
                    # Wait for initial page load - Instacart/SPA sites need time for JS
                    time.sleep(3)
                    
                    # Wait for page to be interactive (Instacart loads content dynamically)
                    try:
                        WebDriverWait(self.driver, 15).until(
                            lambda d: d.execute_script("return document.readyState") == "complete"
                        )
                    except Exception:
                        logger.debug("Page readyState check timed out, continuing anyway")
                    
                    # Scroll progressively to trigger lazy loading
                    # Instacart loads products as you scroll
                    scroll_pause_time = 2
                    last_height = self.driver.execute_script("return document.body.scrollHeight")
                    scroll_attempts = 0
                    max_scroll_attempts = 5  # Limit scroll attempts to avoid infinite loops
                    
                    while scroll_attempts < max_scroll_attempts:
                        # Scroll down incrementally
                        for i in range(3):
                            scroll_position = (i + 1) * (last_height / 4)
                            self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                            time.sleep(scroll_pause_time)
                        
                        # Scroll to bottom
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(scroll_pause_time)
                        
                        # Check if new content loaded
                        new_height = self.driver.execute_script("return document.body.scrollHeight")
                        if new_height == last_height:
                            break
                        last_height = new_height
                        scroll_attempts += 1
                    
                    # Wait for product listings to load - Instacart uses various selectors
                    # Try multiple selectors that match Instacart/Publix delivery site structure
                    selectors_to_try = [
                        (By.CSS_SELECTOR, "[data-testid*='product']"),
                        (By.CSS_SELECTOR, "[data-testid*='Product']"),
                        (By.CSS_SELECTOR, "[data-testid*='ProductCard']"),
                        (By.CSS_SELECTOR, "a[href*='/products/']"),
                        (By.CSS_SELECTOR, "a[href*='/product/']"),
                        (By.CSS_SELECTOR, ".product-item"),
                        (By.CSS_SELECTOR, ".product"),
                        (By.CSS_SELECTOR, ".product-card"),
                        (By.CSS_SELECTOR, ".product-tile"),
                        (By.CSS_SELECTOR, "[class*='ProductCard']"),
                        (By.CSS_SELECTOR, "[class*='product']"),
                        (By.CSS_SELECTOR, "[class*='Product']"),
                    ]
                    
                    products_found = False
                    for selector_type, selector_value in selectors_to_try:
                        try:
                            WebDriverWait(self.driver, 15).until(
                                EC.presence_of_element_located((selector_type, selector_value))
                            )
                            products_found = True
                            logger.debug(f"Found products using selector: {selector_value}")
                            break
                        except Exception:
                            continue
                    
                    if not products_found:
                        logger.warning(f"Could not find product elements for {store.store_id}, trying to extract any product links")
                    
                    # Extract product links - Instacart/Publix delivery site patterns
                    # Product links typically contain /products/ or /product/ in the URL
                    # Following the strategy: extract product URLs from rendered HTML
                    link_selectors = [
                        "a[href*='/products/']",  # Primary: Instacart product links
                        "a[href*='/product/']",  # Alternative product link format
                        "[data-testid*='ProductCard'] a",  # ProductCard component links
                        "[data-testid*='product'] a",  # Product data attribute links
                        "[data-testid*='Product'] a",  # Product (capitalized) links
                        ".product-card a",  # Product card class
                        ".product-tile a",  # Product tile class
                        "[class*='ProductCard'] a",  # ProductCard class (various naming)
                        "[class*='product'] a",  # Generic product class
                        "a[href*='product']",  # Any product link (fallback)
                    ]
                    
                    all_urls = set()  # Use set to avoid duplicates
                    for selector in link_selectors:
                        try:
                            product_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if product_elements:
                                for elem in product_elements:
                                    href = elem.get_attribute("href")
                                    if href and ('/products/' in href or '/product/' in href):
                                        # Make URL absolute if relative
                                        if not href.startswith('http'):
                                            href = f"{PUBLIX_DELIVERY_URL}{href}"
                                        all_urls.add(href)
                                
                                if all_urls:
                                    logger.debug(f"Found {len(all_urls)} unique product URLs using selector: {selector}")
                        except Exception as e:
                            logger.debug(f"Selector {selector} failed: {e}")
                            continue
                    
                    if all_urls:
                        urls = list(all_urls)
                        logger.info(f"Extracted {len(urls)} unique product URLs from collection page")
                    else:
                        # Try extracting from page source as fallback
                        page_source = self.driver.page_source
                        soup = BeautifulSoup(page_source, 'lxml')
                        product_links = soup.find_all('a', href=re.compile(r'/products?/'))
                        if product_links:
                            urls = [
                                link.get('href') if link.get('href').startswith('http') 
                                else f"{PUBLIX_DELIVERY_URL}{link.get('href')}"
                                for link in product_links
                                if link.get('href')
                            ]
                            urls = list(set(urls))  # Remove duplicates
                            logger.info(f"Extracted {len(urls)} product URLs from page source")
                
                else:
                    # delivery.publix.com is a JavaScript SPA (Instacart platform)
                    # Products are loaded dynamically, so requests library won't work
                    # We need Selenium for this site
                    logger.warning(
                        f"delivery.publix.com requires JavaScript rendering. "
                        f"Selenium is needed but not available. "
                        f"Install with: pip install selenium webdriver-manager"
                    )
                    # Try to find any product-related data in the HTML (may be in JSON scripts)
                    headers = {
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Referer': f'{base_url}/store/publix',
                    }
                    response = self.session.get(search_url, headers=headers, timeout=TIMEOUT)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'lxml')
                    
                    # Try to extract product data from JSON in script tags
                    # Instacart/SPA sites often embed data in script tags
                    script_tags = soup.find_all('script', type='application/json')
                    for script in script_tags:
                        try:
                            import json
                            data = json.loads(script.string)
                            # Look for product data in JSON
                            if isinstance(data, dict):
                                # Recursively search for product URLs
                                def find_products(obj, path=""):
                                    if isinstance(obj, dict):
                                        for k, v in obj.items():
                                            if 'product' in k.lower() and isinstance(v, (dict, list)):
                                                return v
                                            result = find_products(v, f"{path}.{k}")
                                            if result:
                                                return result
                                    elif isinstance(obj, list):
                                        for item in obj:
                                            result = find_products(item, path)
                                            if result:
                                                return result
                                    return None
                                
                                products_data = find_products(data)
                                if products_data:
                                    logger.debug("Found product data in JSON script tags")
                        except:
                            pass
                    
                    # Try multiple selectors for product links (may not work without JS)
                    product_links = []
                    selectors = [
                        'a[href*="/products/"]',  # Product links
                        'a[href*="/product/"]',  # Alternative product link format
                        '[data-testid*="product"] a',  # Data attribute selectors
                        'a[href*="storefront"]',  # Storefront links that might contain products
                    ]
                    
                    for selector in selectors:
                        links = soup.select(selector)
                        if links:
                            product_links = links
                            logger.debug(f"Found {len(links)} links using selector: {selector}")
                            break
                    
                    urls = [
                        link.get('href') 
                        for link in product_links 
                        if link.get('href')
                    ]
                    
                    # Make URLs absolute if they're relative
                    urls = [
                        url if url.startswith('http') else f"{PUBLIX_DELIVERY_URL}{url}"
                        for url in urls
                    ]
                    
                    if not urls:
                        logger.warning(
                            "No product URLs found. delivery.publix.com requires JavaScript. "
                            "Please install Selenium: pip install selenium webdriver-manager"
                        )
                
                # If we found URLs, handle pagination and return all URLs
                if urls:
                    logger.info(f"Found {len(urls)} product URLs using pattern {pattern_idx + 1}")
                    
                    # Handle pagination if needed (following strategy: iterate pages until all products collected)
                    # Instacart/Publix may have pagination or "Load More" buttons
                    if self.use_selenium and self.driver:
                        urls = self._handle_pagination(urls, search_url)
                    
                    return urls
                else:
                    logger.debug(f"No URLs found with pattern {pattern_idx + 1}, trying next pattern")
                    continue
                    
            except requests.exceptions.RequestException as e:
                logger.debug(f"Pattern {pattern_idx + 1} failed: {e}")
                if pattern_idx < len(url_patterns) - 1:
                    continue  # Try next pattern
                else:
                    # All patterns failed
                    raise NetworkError(
                        f"Network error getting product URLs for store {store.store_id}: {e}",
                        details={"store_id": store.store_id, "category": category, "url": search_url}
                    )
            except Exception as e:
                logger.debug(f"Pattern {pattern_idx + 1} failed with error: {e}")
                if pattern_idx < len(url_patterns) - 1:
                    continue  # Try next pattern
                else:
                    raise ParsingError(
                        f"Error parsing product URLs for store {store.store_id}: {e}",
                        details={"store_id": store.store_id, "category": category}
                    )
        
        # If we get here, no patterns worked
        logger.warning(f"No product URLs found for {store.store_id} with category {category}")
        return []  # Return empty list instead of raising error - allows graceful degradation
    
    def _handle_pagination(self, initial_urls: List[str], base_url: str) -> List[str]:
        """
        Handle pagination on collection pages to get all products
        
        Following strategy: iterate pages until all products are collected.
        Instacart/Publix may have "Load More" buttons or pagination links.
        
        Args:
            initial_urls: URLs found on first page
            base_url: Base collection URL
            
        Returns:
            Complete list of product URLs from all pages
        """
        if not self.use_selenium or not self.driver:
            return initial_urls
        
        all_urls = set(initial_urls)
        max_pages = 10  # Limit pagination to avoid infinite loops
        page = 1
        
        try:
            # Look for "Load More" button or pagination controls
            while page < max_pages:
                # Try to find and click "Load More" button
                load_more_selectors = [
                    "button[data-testid*='load-more']",
                    "button[data-testid*='LoadMore']",
                    "button:contains('Load More')",
                    "button:contains('Show More')",
                    ".load-more",
                    "[class*='LoadMore']",
                    "a[aria-label*='next']",
                    "a[aria-label*='Next']",
                ]
                
                load_more_found = False
                for selector in load_more_selectors:
                    try:
                        # Try CSS selector first
                        if selector.startswith("button:contains") or selector.startswith("a:contains"):
                            # XPath for contains text
                            xpath = f"//button[contains(text(), 'Load More')] | //button[contains(text(), 'Show More')]"
                            elements = self.driver.find_elements(By.XPATH, xpath)
                        else:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        if elements:
                            # Check if button is visible and clickable
                            for elem in elements:
                                if elem.is_displayed() and elem.is_enabled():
                                    try:
                                        self.driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                                        time.sleep(1)
                                        elem.click()
                                        time.sleep(3)  # Wait for new products to load
                                        load_more_found = True
                                        logger.debug(f"Clicked 'Load More' button on page {page}")
                                        break
                                    except Exception as e:
                                        logger.debug(f"Could not click load more button: {e}")
                                        continue
                            
                            if load_more_found:
                                break
                    except Exception:
                        continue
                
                if not load_more_found:
                    # No more pages or load more button not found
                    logger.debug(f"No more pages found after page {page}")
                    break
                
                # Extract new product URLs from the newly loaded content
                # Scroll to trigger any lazy loading
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Extract new URLs
                link_selectors = [
                    "a[href*='/products/']",
                    "a[href*='/product/']",
                ]
                
                new_urls_count = len(all_urls)
                for selector in link_selectors:
                    try:
                        product_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in product_elements:
                            href = elem.get_attribute("href")
                            if href and ('/products/' in href or '/product/' in href):
                                if not href.startswith('http'):
                                    href = f"{PUBLIX_DELIVERY_URL}{href}"
                                all_urls.add(href)
                    except Exception:
                        continue
                
                # Check if we found new URLs
                if len(all_urls) == new_urls_count:
                    logger.debug(f"No new URLs found on page {page + 1}, stopping pagination")
                    break
                
                page += 1
                logger.debug(f"Page {page}: Found {len(all_urls)} total product URLs")
        
        except Exception as e:
            logger.warning(f"Error handling pagination: {e}. Returning URLs found so far.")
        
        logger.info(f"Pagination complete: Found {len(all_urls)} total product URLs across {page} pages")
        return list(all_urls)
    
    @retry_network_request(max_retries=MAX_RETRIES, initial_delay=REQUEST_DELAY)
    def _scrape_product_details(self, url: str, store: Store, 
                               scrape_date: date, week: int) -> Optional[Product]:
        """
        Scrape detailed product information from a product page
        
        Args:
            url: Product page URL
            store: Store object
            scrape_date: Date of scraping
            week: Week number
            
        Returns:
            Product object or None if scraping fails
            
        Raises:
            NetworkError: If network request fails
            ParsingError: If HTML parsing fails
        """
        try:
            if self.use_selenium and self.driver:
                self.driver.get(url)
                time.sleep(1)
                html = self.driver.page_source
            else:
                response = self.session.get(url, timeout=TIMEOUT)
                response.raise_for_status()
                html = response.content
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract product information from delivery.publix.com
            # Publix delivery site uses specific class names and data attributes
            
            # Product name - try multiple selectors for delivery site
            product_name = self._extract_text(soup, [
                'h1[data-testid*="product-name"]',
                'h1.product-name',
                '[data-testid*="ProductName"]',
                '.product-title',
                'h1',
                '[class*="ProductName"]'
            ])
            
            # Product description
            product_description = self._extract_text(soup, [
                '[data-testid*="product-description"]',
                '.product-description',
                '.product-details',
                '[class*="ProductDescription"]',
                '[data-testid*="description"]'
            ])
            
            product_id = self._extract_product_id(url, soup)
            price = self._extract_price(soup)
            ounces = self._extract_ounces(product_description)
            price_per_ounce = price / ounces if ounces > 0 else 0.0
            promotion = self._extract_promotion(soup)
            
            if not product_name or not product_id:
                logger.warning(f"Missing required fields for product at {url}")
                return None
            
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
            
        except requests.exceptions.RequestException as e:
            raise NetworkError(
                f"Network error scraping product from {url}: {e}",
                details={"url": url, "store_id": store.store_id}
            )
        except Exception as e:
            raise ParsingError(
                f"Error parsing product details from {url}: {e}",
                details={"url": url, "store_id": store.store_id}
            )
    
    def _extract_text(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract text using multiple possible selectors"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return None
    
    def _extract_product_id(self, url: str, soup: BeautifulSoup) -> str:
        """Extract consistent product identifier from delivery.publix.com"""
        # Try to find product ID in URL (delivery.publix.com format)
        # URLs like: /store/publix/products/12345 or /products/12345
        match = re.search(r'/products?/([^/?]+)', url)
        if match:
            return match.group(1)
        
        # Try to find in page data attributes (delivery site format)
        product_element = soup.find(attrs={'data-product-id': True})
        if product_element:
            return product_element.get('data-product-id')
        
        # Try data-testid attributes
        product_element = soup.find(attrs={'data-testid': re.compile(r'.*[Pp]roduct.*[Ii]d.*')})
        if product_element:
            product_id = product_element.get('data-testid') or product_element.get('data-product-id')
            if product_id:
                return str(product_id)
        
        # Try to extract from URL path
        url_parts = url.split('/')
        if 'products' in url_parts:
            idx = url_parts.index('products')
            if idx + 1 < len(url_parts):
                return url_parts[idx + 1].split('?')[0]  # Remove query params
        
        # Fallback: use URL hash (last 10 chars)
        return str(abs(hash(url)))[:10]
    
    def _extract_price(self, soup: BeautifulSoup) -> float:
        """Extract product price from delivery.publix.com"""
        # Try multiple price selectors for delivery site
        price_selectors = [
            '[data-testid*="price"]',  # Data attribute for price
            '[data-testid*="Price"]',  # Alternative case
            '.price',  # Generic price class
            '.product-price',  # Product price class
            '[data-price]',  # Data price attribute
            '.current-price',  # Current price
            '.sale-price',  # Sale price
            '.regular-price',  # Regular price
            '[class*="Price"]',  # Price in class name
            '[class*="price"]',  # Lowercase price in class
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                # Extract numeric value (handle formats like $6.99, $6.99/ea, etc.)
                price_match = re.search(r'[\d.]+', price_text.replace('$', '').replace(',', ''))
                if price_match:
                    price_value = float(price_match.group())
                    if price_value > 0:
                        return price_value
        
        return 0.0
    
    def _extract_ounces(self, description: str) -> float:
        """Extract ounces from product description"""
        if not description:
            return 0.0
        
        # Look for patterns like "12 fl oz", "355 ml", etc.
        # Convert ml to oz if needed (1 fl oz ≈ 29.5735 ml)
        
        # Pattern for fl oz
        fl_oz_match = re.search(r'(\d+(?:\.\d+)?)\s*fl\s*oz', description, re.IGNORECASE)
        if fl_oz_match:
            return float(fl_oz_match.group(1))
        
        # Pattern for ml
        ml_match = re.search(r'(\d+)\s*ml', description, re.IGNORECASE)
        if ml_match:
            ml = float(ml_match.group(1))
            return ml / 29.5735  # Convert to fl oz
        
        # Pattern for total ounces in multi-pack
        # e.g., "12 - 12 fl oz cans" = 144 oz
        pack_match = re.search(r'(\d+)\s*-\s*(\d+(?:\.\d+)?)\s*fl\s*oz', description, re.IGNORECASE)
        if pack_match:
            count = float(pack_match.group(1))
            size = float(pack_match.group(2))
            return count * size
        
        return 0.0
    
    def _extract_promotion(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract promotion information from delivery.publix.com"""
        promotion_selectors = [
            '[data-testid*="promotion"]',  # Data attribute
            '[data-testid*="Promotion"]',  # Alternative case
            '.promotion',  # Generic promotion class
            '.sale-badge',  # Sale badge
            '.deal-text',  # Deal text
            '[data-promotion]',  # Data promotion attribute
            '.special-offer',  # Special offer
            '[class*="Promotion"]',  # Promotion in class name
            '[class*="BOGO"]',  # BOGO deals
            '[class*="bogo"]',  # Lowercase BOGO
        ]
        
        for selector in promotion_selectors:
            element = soup.select_one(selector)
            if element:
                promo_text = element.get_text(strip=True)
                if promo_text:
                    return promo_text
        
        return None
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing Selenium driver: {e}")
        
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
