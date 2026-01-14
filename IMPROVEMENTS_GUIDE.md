# Quick Reference: Code Improvements Guide

## 🎯 What Changed

### Error Handling
**Before:**
```python
except Exception as e:
    logger.error(f"Error: {e}")
```

**After:**
```python
from publix_scraper.utils.exceptions import NetworkError, ParsingError

try:
    # code
except NetworkError as e:
    logger.error(f"Network error: {e.message}", extra=e.details)
except ParsingError as e:
    logger.error(f"Parsing error: {e.message}", extra=e.details)
```

### Logging
**Before:**
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

**After:**
```python
from publix_scraper.utils.logging_config import get_logger

logger = get_logger(__name__)
```

### Retry Logic
**Before:**
```python
for attempt in range(MAX_RETRIES):
    try:
        response = session.get(url)
        break
    except Exception:
        time.sleep(REQUEST_DELAY * (attempt + 1))
```

**After:**
```python
from publix_scraper.utils.retry import retry_network_request

@retry_network_request(max_retries=3, initial_delay=1.0)
def fetch_data(url):
    return session.get(url)
```

### Resource Management
**Before:**
```python
scraper = PublixScraper()
try:
    # use scraper
finally:
    scraper.close()
```

**After:**
```python
with PublixScraper() as scraper:
    # use scraper
# Automatically closed
```

### Configuration Validation
**Before:**
```python
# No validation - errors at runtime
```

**After:**
```python
from publix_scraper.core.config import validate_configuration

warnings = validate_configuration()
if warnings:
    for warning in warnings:
        logger.warning(warning)
```

## 📦 New Utilities

### Custom Exceptions
```python
from publix_scraper.utils.exceptions import (
    PublixScraperError,
    ConfigurationError,
    ScrapingError,
    NetworkError,
    ParsingError,
    ValidationError,
    StorageError,
    IntegrationError
)
```

### Logging Setup
```python
from publix_scraper.utils.logging_config import setup_logging, get_logger

# Setup once at application start
setup_logging(log_level="INFO", log_file=Path("logs/app.log"))

# Use in modules
logger = get_logger(__name__)
```

### Retry Decorators
```python
from publix_scraper.utils.retry import retry_with_backoff, retry_network_request

@retry_network_request(max_retries=3, initial_delay=1.0)
def make_request(url):
    return requests.get(url)

@retry_with_backoff(
    max_retries=5,
    initial_delay=2.0,
    max_delay=60.0,
    exponential_base=2.0,
    exceptions=(ValueError, KeyError)
)
def process_data(data):
    # custom retry logic
    pass
```

## 🔧 Usage Examples

### Using the Scraper
```python
from publix_scraper.core.scraper import PublixScraper
from publix_scraper.core.store_locator import StoreLocator

# Context manager ensures cleanup
with PublixScraper(use_selenium=True) as scraper:
    with StoreLocator() as locator:
        stores = locator.get_florida_stores()
        for store in stores:
            products = scraper.scrape_store_products(store, week=1)
```

### Error Handling
```python
from publix_scraper.utils.exceptions import NetworkError, StorageError

try:
    products = scraper.scrape_store_products(store, week=1)
    storage.save_products(products)
except NetworkError as e:
    logger.error(f"Network issue: {e.message}")
    # Handle network error
except StorageError as e:
    logger.error(f"Storage issue: {e.message}")
    # Handle storage error
```

### Configuration
```python
from publix_scraper.core.config import (
    validate_configuration,
    get_config_summary
)

# Validate on startup
warnings = validate_configuration()
if warnings:
    logger.warning("Configuration issues detected")

# Get config summary for debugging
summary = get_config_summary()
logger.debug(f"Config: {summary}")
```

## 🚀 Performance Tips

1. **Use Connection Pooling**: The scraper now uses connection pooling automatically
2. **Batch Operations**: Storage operations are batched for better performance
3. **Retry Logic**: Transient failures are handled automatically
4. **Context Managers**: Always use context managers for proper resource cleanup

## 🐛 Debugging

### Enable Debug Logging
```python
from publix_scraper.utils.logging_config import setup_logging

setup_logging(log_level="DEBUG", log_file=Path("logs/debug.log"))
```

### Check Configuration
```python
from publix_scraper.core.config import get_config_summary

print(get_config_summary())
```

### Handle Errors with Details
```python
try:
    # operation
except PublixScraperError as e:
    logger.error(f"Error: {e.message}")
    if e.details:
        logger.debug(f"Details: {e.details}")
```

## 📝 Migration Checklist

- [x] Replace generic `Exception` with specific exception types
- [x] Update logging to use `get_logger()`
- [x] Add retry decorators to network operations
- [x] Use context managers for resource management
- [x] Add configuration validation
- [x] Update type hints
- [x] Test error handling paths
- [x] Verify resource cleanup

## 🔍 Key Benefits

1. **Better Error Messages**: Specific exceptions with context
2. **Automatic Retries**: Transient failures handled automatically
3. **Performance**: Connection pooling and batch operations
4. **Reliability**: Proper resource cleanup and error recovery
5. **Maintainability**: Clear structure and consistent patterns
