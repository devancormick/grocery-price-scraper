# Install Selenium for Publix Scraping

## ⚠️ Critical Requirement

The Publix delivery website (`delivery.publix.com`) is a **JavaScript Single Page Application (SPA)** powered by Instacart. Products are loaded dynamically via JavaScript, which means:

- ❌ **Requests library won't work** - Only gets initial HTML without products
- ✅ **Selenium is required** - Needs to wait for JavaScript to render products

## Installation

### Step 1: Install Selenium
```bash
cd /Users/administrator/Documents/github/grocery-price-scraper
pip install selenium webdriver-manager
```

### Step 2: Verify Installation
```bash
python3 -c "from selenium import webdriver; print('Selenium installed successfully')"
```

### Step 3: Test Chrome/Chromium
Selenium will automatically download ChromeDriver, but you need Chrome browser installed:
- **macOS**: Chrome should already be installed
- **Linux**: May need to install Chromium: `sudo apt-get install chromium-browser`

## Why Selenium is Needed

1. **JavaScript Rendering**: Publix delivery site uses React/JavaScript to load products
2. **Dynamic Content**: Product listings appear after page load via API calls
3. **SPA Architecture**: Single Page Application requires browser engine
4. **No Static HTML**: Initial HTML doesn't contain product data

## Current Status

- ✅ Code updated to use `delivery.publix.com` URLs
- ✅ Location parameter added (ZIP code)
- ✅ Selenium selectors configured
- ❌ **Selenium not installed** - Install to proceed

## After Installation

Once Selenium is installed:
1. Restart the scheduler
2. It will automatically use Selenium
3. Products should be found and scraped
4. Data will be saved to CSV and Google Sheets

## Alternative: Use Instacart API

If Selenium doesn't work, we could explore:
- Instacart's internal API endpoints
- Reverse engineering the API calls
- Using browser automation tools

But Selenium is the standard, free solution for JavaScript-heavy sites.
