# Publix Scraping Strategy Implementation

## Overview

Updated the scraper to follow the documented Publix scraping strategy based on:
- Apify Publix Products Scraper documentation
- Instacart platform structure (delivery.publix.com)
- JavaScript-heavy dynamic pages requiring Selenium

## Key Updates

### 1. Collection URL Strategy
- **Primary URL**: `https://delivery.publix.com/store/publix/collections/rc-beverages-soda?location={ZIP}`
- **Pattern**: Following Apify format: `{"url": "collection_url", "location": "address/ZIP"}`
- **Location Parameter**: Required for store-specific pricing
- **Fallback URLs**: Multiple patterns tried in order of preference

### 2. Enhanced Selenium Implementation

#### Improved Page Loading
- **Initial Wait**: 3 seconds for page load
- **ReadyState Check**: Waits up to 15 seconds for `document.readyState == "complete"`
- **Progressive Scrolling**: Incremental scrolling to trigger lazy loading
- **Scroll Strategy**: 
  - Scrolls in 4 increments (25%, 50%, 75%, 100%)
  - Waits 2 seconds between scrolls
  - Checks for new content after each scroll
  - Maximum 5 scroll attempts to avoid infinite loops

#### Better Product Detection
- **Extended Wait Times**: 15 seconds for product elements (up from 10)
- **Multiple Selectors**: 12 different selectors tried for Instacart/Publix structure
- **Selector Priority**:
  1. `[data-testid*='product']` - Instacart data attributes
  2. `[data-testid*='ProductCard']` - Product card components
  3. `a[href*='/products/']` - Product links
  4. Various class-based selectors

#### Product URL Extraction
- **Deduplication**: Uses `set()` to avoid duplicate URLs
- **Absolute URLs**: Converts relative URLs to absolute
- **Fallback Parsing**: If Selenium selectors fail, parses page source with BeautifulSoup
- **Comprehensive Patterns**: Handles both `/products/` and `/product/` URL formats

### 3. Pagination Handling

New `_handle_pagination()` method implements:
- **Load More Detection**: Looks for "Load More" or "Show More" buttons
- **Multiple Selectors**: 8 different selectors for pagination controls
- **Incremental Loading**: Clicks load more and waits for new content
- **URL Collection**: Extracts new product URLs after each page load
- **Safety Limits**: Maximum 10 pages to avoid infinite loops
- **Progress Tracking**: Logs progress through pagination

### 4. Improved Error Handling

- **Graceful Degradation**: Returns empty list instead of raising errors
- **Pattern Fallback**: Tries multiple URL patterns if one fails
- **Detailed Logging**: Logs each step for debugging
- **Exception Handling**: Catches and logs errors without stopping execution

## Implementation Details

### URL Patterns (in order of preference)
1. `rc-beverages-soda?location={ZIP}` - Primary soda collection
2. `rc-beverages-soda` - Soda collection without location
3. `rc-beverages?location={ZIP}` - All beverages with location
4. `rc-beverages` - All beverages
5. `search?q=soda&location={ZIP}` - Search with location
6. `search?q=soda` - Search without location

### Location Parameter
- **Priority**: ZIP code > City, State > Address > Default (33801)
- **Format**: ZIP code as string (e.g., "33801")
- **Purpose**: Ensures store-specific pricing

### Scrolling Strategy
```python
# Progressive scrolling to trigger lazy loading
for i in range(3):
    scroll_position = (i + 1) * (last_height / 4)
    scroll_to(scroll_position)
    wait(2 seconds)
scroll_to(bottom)
wait(2 seconds)
check_for_new_content()
```

### Pagination Strategy
```python
while page < max_pages:
    1. Find "Load More" button
    2. Click button
    3. Wait for new content
    4. Scroll to bottom
    5. Extract new product URLs
    6. Check if new URLs found
    7. If no new URLs, stop
```

## Testing

The updated scraper should:
1. ✅ Load pages with proper JavaScript rendering
2. ✅ Wait for content to fully load
3. ✅ Scroll to trigger lazy loading
4. ✅ Extract product URLs correctly
5. ✅ Handle pagination automatically
6. ✅ Deduplicate URLs
7. ✅ Work with Instacart platform structure

## Next Steps

1. **Test with Real Store**: Run scraper with actual Publix store location
2. **Monitor Logs**: Check for product detection and pagination
3. **Verify URLs**: Ensure extracted URLs are valid product pages
4. **Adjust Selectors**: Fine-tune selectors based on actual page structure
5. **Optimize Timing**: Adjust wait times based on page load speed

## References

- Apify Publix Scraper: https://apify.com/rigelbytes/publix-scraper
- Instacart Platform: delivery.publix.com
- Strategy Document: User-provided scraping methodology
