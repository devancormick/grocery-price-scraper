"""
Integration modules for external services
"""

try:
    from .google_sheets import GoogleSheetsHandler
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    GoogleSheetsHandler = None

try:
    from .email import EmailHandler
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    EmailHandler = None

try:
    from .webhook import WebhookHandler
    WEBHOOK_AVAILABLE = True
except ImportError:
    WEBHOOK_AVAILABLE = False
    WebhookHandler = None

try:
    from .database import DatabaseHandler
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    DatabaseHandler = None

__all__ = [
    'GoogleSheetsHandler',
    'EmailHandler',
    'WebhookHandler',
    'DatabaseHandler',
    'GOOGLE_SHEETS_AVAILABLE',
    'EMAIL_AVAILABLE',
    'WEBHOOK_AVAILABLE',
    'DATABASE_AVAILABLE'
]
