"""
Email notification handler for Publix price scraper
Supports daily and weekly reports with CSV attachments
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Optional
from pathlib import Path

from ..core.config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class EmailHandler:
    """Handles email notifications"""
    
    def __init__(self):
        """Initialize email handler"""
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.smtp_username = SMTP_USERNAME
        self.smtp_password = SMTP_PASSWORD
        self.email_from = EMAIL_FROM or SMTP_USERNAME
        self.email_to = EMAIL_TO
    
    def send_weekly_report(self, week: int, product_count: int, store_count: int,
                          sheet_url: str, csv_path: Optional[str] = None,
                          new_count: int = None, month_year: str = None) -> bool:
        """
        Send weekly report email with Google Sheet link and CSV attachment
        
        Args:
            week: Week number (1-4)
            product_count: Number of products scraped
            store_count: Number of stores scraped
            sheet_url: URL to the Google Sheet
            csv_path: Path to CSV file to attach
            new_count: Number of new products (optional)
            month_year: Month-year string like "2024-01" (optional)
        
        Returns:
            True if email sent successfully
        """
        if not self.email_to:
            logger.warning("No email recipients configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = ', '.join(self.email_to)
            
            subject = f"Publix Price Scraper - Week {week} Report"
            if month_year:
                subject += f" ({month_year})"
            subject += f" - {product_count} products"
            msg['Subject'] = subject
            
            # Create email body
            body = f"""
Publix Grocery Store Price Scraping - Weekly Report

Week: {week}
"""
            if month_year:
                body += f"Month: {month_year}\n"
            body += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            body += f"Summary:\n"
            body += f"- Products scraped: {product_count}\n"
            # if new_count is not None:
            #     body += f"- New products: {new_count}\n"
            #     body += f"- Duplicate products: {product_count - new_count}\n"
            body += f"- Stores covered: {store_count}\n"
            body += f"- Week: {week}\n\n"
            body += f"[SUCCESS] Data has been successfully collected and uploaded to Google Sheets.\n\n"
            body += f"Google Sheet Link:\n{sheet_url}\n\n"
            
            if csv_path:
                body += f"""
A CSV backup file is attached to this email.
"""
            
            body += f"""
---
This is an automated message from the Publix Price Scraper system.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach CSV file if provided
            if csv_path:
                try:
                    with open(csv_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(csv_path)}'
                    )
                    msg.attach(part)
                    logger.info(f"Attached CSV file: {csv_path}")
                except Exception as e:
                    logger.warning(f"Could not attach CSV file: {str(e)}")
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Weekly report email sent successfully to {', '.join(self.email_to)}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            raise
    
    def send_error_notification(self, error_message: str) -> bool:
        """
        Send error notification email
        
        Args:
            error_message: Error message to send
        
        Returns:
            True if email sent successfully
        """
        if not self.email_to:
            logger.warning("No email recipients configured for error notifications")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = ', '.join(self.email_to)
            msg['Subject'] = "ERROR: Publix Price Scraper Failed"
            
            body = f"""
The Publix Price Scraper job has failed.

Error Details:
{error_message}

Please check the logs and system status.

---
This is an automated error notification from the Publix Price Scraper system.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Error notification email sent to {', '.join(self.email_to)}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending error notification email: {str(e)}")
            return False
    
    def send_progress_update(
        self,
        week: int,
        stores_completed: int,
        stores_total: int,
        stores_remaining: int,
        progress_percent: float,
        products_found: int,
        estimated_remaining: str,
        sheet_url: str,
        month_year: str = None
    ) -> bool:
        """
        Send progress update email during scraping
        
        Args:
            week: Week number (1-4)
            stores_completed: Number of stores completed
            stores_total: Total number of stores
            stores_remaining: Number of stores remaining
            progress_percent: Progress percentage
            products_found: Number of products found so far
            estimated_remaining: Estimated time remaining (formatted string)
            sheet_url: URL to the Google Sheet
            month_year: Month-year string like "2024-01" (optional)
        
        Returns:
            True if email sent successfully
        """
        if not self.email_to:
            logger.warning("No email recipients configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = ', '.join(self.email_to)
            
            subject = f"Publix Scraper Progress - Week {week}"
            if month_year:
                subject += f" ({month_year})"
            subject += f" - {progress_percent:.1f}% Complete"
            msg['Subject'] = subject
            
            # Create email body
            body = f"""
Publix Grocery Store Price Scraping - Progress Update

Week: {week}
"""
            if month_year:
                body += f"Month: {month_year}\n"
            body += f"Update Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            body += f"Progress Summary:\n"
            body += f"- Stores Completed: {stores_completed:,} / {stores_total:,}\n"
            body += f"- Stores Remaining: {stores_remaining:,}\n"
            body += f"- Progress: {progress_percent:.1f}%\n"
            body += f"- Products Found So Far: {products_found:,}\n"
            body += f"- Estimated Time Remaining: {estimated_remaining}\n\n"
            
            body += f"Current Status:\n"
            body += f"[OK] CSV file is being updated every 20 stores\n"
            body += f"[OK] Google Sheets is being updated every 20 stores\n"
            body += f"[OK] You can view the latest data in the Google Sheet\n\n"
            
            body += f"Google Sheet Link:\n{sheet_url}\n\n"
            
            body += f"""
The scraping process is running smoothly. You will receive another update after {stores_remaining} more stores are processed, or when the scraping completes.

---
This is an automated progress update from the Publix Price Scraper system.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Progress update email sent successfully to {', '.join(self.email_to)}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending progress update email: {str(e)}")
            return False
    
    def send_daily_report(
        self,
        date: str,
        product_count: int,
        new_count: int,
        store_count: int,
        sheet_url: str,
        csv_path: Optional[str] = None
    ) -> bool:
        """
        Send daily report email with Google Sheet link and CSV attachment
        
        Args:
            date: Date string (YYYY-MM-DD)
            product_count: Total number of products scraped
            new_count: Number of new products
            store_count: Number of stores scraped
            sheet_url: URL to the Google Sheet
            csv_path: Path to CSV file to attach
        
        Returns:
            True if email sent successfully
        """
        if not self.email_to:
            logger.warning("No email recipients configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = ', '.join(self.email_to)
            msg['Subject'] = f"Publix Price Scraper - Daily Report ({date}) - {product_count} products"
            
            # Create email body
            body = f"""
Publix Grocery Store Price Scraping - Daily Report

Date: {date}
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Summary:
- Total products scraped: {product_count}
- New products: {new_count}
- Duplicate products: {product_count - new_count}
- Stores covered: {store_count}

[SUCCESS] Data has been successfully collected and uploaded to Google Sheets.

Google Sheet Link:
{sheet_url}

"""
            
            if csv_path:
                body += f"""
[ATTACHMENT] A CSV backup file is attached to this email.
   File: {os.path.basename(csv_path)}
"""
            
            body += f"""
---
This is an automated daily message from the Publix Price Scraper system.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach CSV file if provided
            if csv_path and Path(csv_path).exists():
                try:
                    with open(csv_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(csv_path)}'
                    )
                    msg.attach(part)
                    logger.info(f"Attached CSV file: {csv_path}")
                except Exception as e:
                    logger.warning(f"Could not attach CSV file: {str(e)}")
            elif csv_path:
                logger.warning(f"CSV file not found: {csv_path}")
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Daily report email sent successfully to {', '.join(self.email_to)}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending daily email: {str(e)}")
            raise
