"""
Configuration settings for the Publix price scraper
"""
import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

from ..utils.exceptions import ConfigurationError

# Load environment variables
load_dotenv()

# Project paths - relative to project root
# Go up from src/publix_scraper/core/config.py to project root
BASE_DIR = Path(__file__).parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output/csv")

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Publix API/Website endpoints
PUBLIX_BASE_URL = "https://www.publix.com"
PUBLIX_DELIVERY_URL = "https://delivery.publix.com"  # Delivery site shows prices with location
PUBLIX_API_BASE = "https://services.publix.com/api"

# Store locations
FLORIDA_STORE_COUNT = 889
GEORGIA_STORE_COUNT = 220

# Scraping settings
REQUEST_DELAY = 1.0  # Delay between requests in seconds
MAX_RETRIES = 3
TIMEOUT = 30

# Data collection settings
WEEKS_TO_COLLECT = 4  # One month
CATEGORY = "soda"  # Focus on soda products

# Output settings
OUTPUT_FORMAT = "csv"  # csv or json
OUTPUT_FILE = DATA_DIR / "publix_soda_prices.csv"
DATE_FORMAT = "%Y-%m-%d"

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "service_account.json")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = os.getenv("EMAIL_TO", "").split(",") if os.getenv("EMAIL_TO") else []

# Scheduler Configuration
MODE = os.getenv("MODE", "production").lower()  # "test" or "production"

# Test interval in seconds - supports mathematical expressions like "60*1", "300", etc.
def safe_eval_interval(value, default=300):
    """Safely evaluate TEST_INTERVAL_SECONDS, supporting expressions like 60*1"""
    if not value:
        return default
    
    try:
        return int(value)
    except ValueError:
        try:
            allowed_chars = set('0123456789+-*/(). ')
            if all(c in allowed_chars for c in value):
                result = eval(value)
                result_int = int(result)
                if result_int <= 0:
                    raise ValueError("Result must be positive")
                return result_int
            else:
                raise ValueError("Invalid characters in expression")
        except (ValueError, TypeError, SyntaxError, ZeroDivisionError):
            return default

try:
    test_interval_str = os.getenv("TEST_INTERVAL_SECONDS", "300")
    TEST_INTERVAL_SECONDS = safe_eval_interval(test_interval_str, 300)
    if TEST_INTERVAL_SECONDS <= 0:
        TEST_INTERVAL_SECONDS = 300
except Exception:
    TEST_INTERVAL_SECONDS = 300

# Production cron schedule
try:
    PRODUCTION_CRON_HOUR = int(os.getenv("PRODUCTION_CRON_HOUR", "2"))
    if not (0 <= PRODUCTION_CRON_HOUR <= 23):
        raise ValueError("PRODUCTION_CRON_HOUR must be between 0 and 23")
except (ValueError, TypeError):
    PRODUCTION_CRON_HOUR = 2

try:
    PRODUCTION_CRON_MINUTE = int(os.getenv("PRODUCTION_CRON_MINUTE", "0"))
    if not (0 <= PRODUCTION_CRON_MINUTE <= 59):
        raise ValueError("PRODUCTION_CRON_MINUTE must be between 0 and 59")
except (ValueError, TypeError):
    PRODUCTION_CRON_MINUTE = 0


def validate_configuration() -> List[str]:
    """
    Validate configuration settings
    
    Returns:
        List of validation warnings/errors (empty if all valid)
    """
    warnings = []
    
    # Validate paths
    if not BASE_DIR.exists():
        warnings.append(f"Base directory does not exist: {BASE_DIR}")
    
    # Validate numeric settings
    if REQUEST_DELAY < 0:
        warnings.append(f"REQUEST_DELAY must be non-negative, got {REQUEST_DELAY}")
    
    if MAX_RETRIES < 1:
        warnings.append(f"MAX_RETRIES must be at least 1, got {MAX_RETRIES}")
    
    if TIMEOUT < 1:
        warnings.append(f"TIMEOUT must be at least 1, got {TIMEOUT}")
    
    if WEEKS_TO_COLLECT < 1 or WEEKS_TO_COLLECT > 52:
        warnings.append(f"WEEKS_TO_COLLECT should be between 1 and 52, got {WEEKS_TO_COLLECT}")
    
    # Validate Google Sheets config if provided
    if GOOGLE_SHEET_ID:
        if not Path(GOOGLE_SHEETS_CREDENTIALS_PATH).exists():
            warnings.append(
                f"Google Sheets credentials file not found: {GOOGLE_SHEETS_CREDENTIALS_PATH}"
            )
    
    # Validate email config if provided
    if EMAIL_TO:
        if not EMAIL_FROM:
            warnings.append("EMAIL_FROM is required when EMAIL_TO is set")
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            warnings.append("SMTP_USERNAME and SMTP_PASSWORD are required for email")
    
    return warnings


def get_config_summary() -> dict:
    """
    Get a summary of current configuration
    
    Returns:
        Dictionary with configuration summary
    """
    return {
        "base_dir": str(BASE_DIR),
        "data_dir": str(DATA_DIR),
        "logs_dir": str(LOGS_DIR),
        "output_dir": str(OUTPUT_DIR),
        "publix_base_url": PUBLIX_BASE_URL,
        "request_delay": REQUEST_DELAY,
        "max_retries": MAX_RETRIES,
        "timeout": TIMEOUT,
        "weeks_to_collect": WEEKS_TO_COLLECT,
        "category": CATEGORY,
        "output_format": OUTPUT_FORMAT,
        "google_sheets_enabled": bool(GOOGLE_SHEET_ID),
        "email_enabled": bool(EMAIL_TO),
        "mode": MODE,
    }
