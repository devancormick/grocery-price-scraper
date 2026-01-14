"""
Run summary generator for comprehensive logging and reporting
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import json
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class RunSummary:
    """Generates comprehensive run summaries"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.products_scraped = 0
        self.products_valid = 0
        self.products_invalid = 0
        self.products_new = 0
        self.products_duplicate = 0
        self.stores_processed = 0
        self.weeks_processed = []
        self.errors: List[Dict] = []
        self.warnings: List[str] = []
        self.validation_errors: List[Dict] = []
        self.files_created: List[str] = []
        self.google_sheets_uploaded = False
        self.email_sent = False
        self.webhook_sent = False
    
    def finish(self):
        """Mark run as finished"""
        self.end_time = datetime.now()
    
    def get_duration(self) -> timedelta:
        """Get run duration"""
        if self.end_time:
            return self.end_time - self.start_time
        return datetime.now() - self.start_time
    
    def to_dict(self) -> Dict:
        """Convert summary to dictionary"""
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.get_duration().total_seconds(),
            'products': {
                'scraped': self.products_scraped,
                'valid': self.products_valid,
                'invalid': self.products_invalid,
                'new': self.products_new,
                'duplicate': self.products_duplicate
            },
            'stores_processed': self.stores_processed,
            'weeks_processed': self.weeks_processed,
            'errors': self.errors,
            'warnings': self.warnings,
            'validation_errors_count': len(self.validation_errors),
            'files_created': self.files_created,
            'integrations': {
                'google_sheets': self.google_sheets_uploaded,
                'email': self.email_sent,
                'webhook': self.webhook_sent
            }
        }
    
    def generate_report(self) -> str:
        """Generate human-readable report"""
        duration = self.get_duration()
        
        report = f"""
{'=' * 80}
PUBLIX PRICE SCRAPER - RUN SUMMARY
{'=' * 80}

Execution Time:
  Start: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
  End:   {self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else 'Running...'}
  Duration: {duration}

Products:
  Scraped: {self.products_scraped}
  Valid: {self.products_valid}
  Invalid: {self.products_invalid}
  New: {self.products_new}
  Duplicate: {self.products_duplicate}

Processing:
  Stores Processed: {self.stores_processed}
  Weeks Processed: {', '.join(map(str, self.weeks_processed))}

Files Created:
{chr(10).join(f'  - {f}' for f in self.files_created) if self.files_created else '  None'}

Integrations:
  Google Sheets: {'✅' if self.google_sheets_uploaded else '❌'}
  Email: {'✅' if self.email_sent else '❌'}
  Webhook: {'✅' if self.webhook_sent else '❌'}

Errors: {len(self.errors)}
Warnings: {len(self.warnings)}
Validation Errors: {len(self.validation_errors)}

{'=' * 80}
"""
        
        if self.errors:
            report += "\nErrors:\n"
            for error in self.errors[:10]:  # Show first 10
                report += f"  - {error.get('message', 'Unknown error')}\n"
        
        if self.warnings:
            report += "\nWarnings:\n"
            for warning in self.warnings[:10]:  # Show first 10
                report += f"  - {warning}\n"
        
        return report
    
    def save_to_file(self, filepath: Path):
        """Save summary to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Run summary saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving run summary: {e}")
    
    def log_summary(self):
        """Log summary to logger"""
        logger.info(self.generate_report())
