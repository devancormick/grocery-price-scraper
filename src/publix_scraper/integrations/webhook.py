"""
Webhook handler for automated delivery
"""
import logging
import requests
import json
from typing import Dict, Optional, List
from datetime import datetime
from ..core.models import Product

logger = logging.getLogger(__name__)


class WebhookHandler:
    """Handles webhook delivery for scraped data"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize webhook handler
        
        Args:
            webhook_url: Webhook URL for delivery
        """
        self.webhook_url = webhook_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Publix-Price-Scraper/1.0'
        })
    
    def send_webhook(self, data: Dict, event_type: str = "scraping_complete") -> bool:
        """
        Send data to webhook URL
        
        Args:
            data: Data dictionary to send
            event_type: Type of event (e.g., "scraping_complete", "error", "summary")
            
        Returns:
            True if successful
        """
        if not self.webhook_url:
            logger.warning("No webhook URL configured")
            return False
        
        payload = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        try:
            response = self.session.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Webhook sent successfully: {event_type}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending webhook: {e}")
            return False
    
    def send_scraping_summary(self, summary: Dict) -> bool:
        """
        Send scraping summary to webhook
        
        Args:
            summary: Summary dictionary with scraping results
            
        Returns:
            True if successful
        """
        return self.send_webhook(summary, event_type="scraping_summary")
    
    def send_error_notification(self, error_message: str, context: Optional[Dict] = None) -> bool:
        """
        Send error notification to webhook
        
        Args:
            error_message: Error message
            context: Additional context dictionary
            
        Returns:
            True if successful
        """
        error_data = {
            'error': error_message,
            'context': context or {}
        }
        return self.send_webhook(error_data, event_type="error")
    
    def send_product_update(self, products: List[Product], count: int) -> bool:
        """
        Send product update to webhook
        
        Args:
            products: List of Product objects
            count: Number of products
            
        Returns:
            True if successful
        """
        data = {
            'product_count': count,
            'products': [p.to_dict() for p in products[:10]]  # Limit to first 10 for webhook
        }
        return self.send_webhook(data, event_type="product_update")
