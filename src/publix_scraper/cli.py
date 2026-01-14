"""
Command-line interface for Publix Price Scraper
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.publix_scraper.main import main

if __name__ == "__main__":
    main()
