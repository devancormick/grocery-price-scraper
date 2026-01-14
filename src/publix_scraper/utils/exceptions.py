"""
Custom exception hierarchy for the Publix scraper
"""
from typing import Optional


class PublixScraperError(Exception):
    """Base exception for all Publix scraper errors"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(PublixScraperError):
    """Raised when there's a configuration issue"""
    pass


class ScrapingError(PublixScraperError):
    """Raised when scraping fails"""
    pass


class NetworkError(ScrapingError):
    """Raised when network requests fail"""
    pass


class ParsingError(ScrapingError):
    """Raised when parsing HTML/data fails"""
    pass


class ValidationError(PublixScraperError):
    """Raised when data validation fails"""
    pass


class StorageError(PublixScraperError):
    """Raised when storage operations fail"""
    pass


class IntegrationError(PublixScraperError):
    """Raised when external integrations fail"""
    pass
