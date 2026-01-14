# Publix URL Research & Fixes

## Research Findings

Based on research, Publix's online shopping platform has the following structure:

### Key Requirements:
1. **Store Selection First**: Publix requires users to select a store location (ZIP code or city/state) before browsing products
2. **JavaScript-Heavy**: The website uses JavaScript/SPA architecture, requiring Selenium for scraping
3. **Department Structure**: Products are organized by departments (e.g., "Beverages" contains "Soda")
4. **No Public API**: Publix does not offer a public API for product data

### URL Structure:
- Base shopping URL: `https://www.publix.com/shop`
- Store selection required before product browsing
- Products organized by departments/categories
- Soda products likely under "Beverages" department

## Implemented Fixes

### 1. Store Selection Method
Added `_select_store()` method that:
- Navigates to Publix shop page
- Finds ZIP code input field
- Enters store ZIP code
- Submits store selection
- Handles cases where store is already selected

### 2. Updated URL Patterns
Changed from incorrect patterns to:
1. `/shop/department/beverages` - Beverages department (contains soda)
2. `/shop/department/beverages/soda` - Soda under beverages
3. `/shop/products/soda` - Direct products category
4. `/shop/browse/soda` - Browse category
5. `/shop/search?q=soda` - Search for category

### 3. Enhanced Selenium Selectors
Added multiple selectors to find products:
- `[data-testid*='product']` - Data attribute selectors
- `.product-card`, `.product-tile` - Class-based selectors
- Multiple link patterns for product URLs

### 4. Improved Page Loading
- Increased wait times for JavaScript rendering
- Added scrolling to handle lazy-loaded content
- Better error handling for missing elements

### 5. Enabled Selenium by Default
Updated scheduler to use Selenium (`use_selenium=True`) since Publix requires JavaScript rendering.

## Current Implementation

The scraper now:
1. ✅ Selects store location first (using ZIP code)
2. ✅ Uses Selenium for JavaScript-heavy pages
3. ✅ Tries multiple URL patterns
4. ✅ Handles lazy-loaded content with scrolling
5. ✅ Uses multiple selectors to find products
6. ✅ Has proper error handling and retry logic

## Testing

To test the updated scraper:

```bash
# Restart scheduler with updated code
python3 -m src.publix_scraper.scheduler
```

Watch logs for:
- Store selection success
- URL patterns being tried
- Product URLs found
- Any errors or warnings

## Potential Issues & Solutions

### Issue 1: Store Selection Fails
**Solution**: May need to inspect actual Publix website to find correct selectors for store selection elements.

### Issue 2: Products Not Found
**Solution**: 
- Inspect Publix website in browser to find actual product container classes
- May need to filter by "soda" within beverages department
- Could require search functionality instead of direct category browsing

### Issue 3: Instacart Partnership
**Note**: Publix partners with Instacart. If direct scraping fails, may need to:
- Use Instacart's API (if available)
- Scrape Instacart's Publix storefront
- URL: `https://www.instacart.com/store/publix/storefront`

## Next Steps

1. **Test with Real Store**: Run scraper and monitor logs
2. **Inspect Website**: Use browser dev tools to find actual selectors
3. **Adjust Selectors**: Update based on actual Publix website structure
4. **Consider Alternatives**: If direct scraping fails, explore Instacart API

## Files Modified

- `src/publix_scraper/core/scraper.py`:
  - Added `_select_store()` method
  - Updated `_get_product_urls()` with new URL patterns
  - Enhanced Selenium selectors
  - Added scrolling for lazy loading

- `src/publix_scraper/scheduler.py`:
  - Changed to use Selenium by default (`use_selenium=True`)

## Status

✅ Code updated and compiled successfully
✅ Store selection logic implemented
✅ Multiple URL patterns configured
✅ Enhanced selectors added
⏳ Ready for testing with actual Publix website
