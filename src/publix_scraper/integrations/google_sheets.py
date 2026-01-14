"""
Google Sheets integration for Publix price data
Supports daily tabs and weekly tabs based on project requirements
"""
from datetime import datetime, date
from typing import List, Tuple, Optional
import gspread
from google.oauth2.service_account import Credentials
from ..core.config import GOOGLE_SHEETS_CREDENTIALS_PATH, GOOGLE_SHEET_ID, DATE_FORMAT
from ..core.models import Product
from ..utils.logging_config import get_logger
from ..utils.week_calculator import get_month_year_string, get_week_of_month

logger = get_logger(__name__)


class GoogleSheetsHandler:
    """Handles Google Sheets operations for price data"""
    
    def __init__(self):
        """Initialize Google Sheets client"""
        try:
            # Authenticate using service account
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            credentials = Credentials.from_service_account_file(
                GOOGLE_SHEETS_CREDENTIALS_PATH,
                scopes=scope
            )
            self.client = gspread.authorize(credentials)
            self.sheet_id = GOOGLE_SHEET_ID
            self.sheet = None
            
            if self.sheet_id:
                self.sheet = self.client.open_by_key(self.sheet_id)
                logger.info(f"Connected to Google Sheet: {self.sheet.title}")
            else:
                logger.warning("No Google Sheet ID configured")
                
        except FileNotFoundError:
            logger.error(f"Service account credentials not found at: {GOOGLE_SHEETS_CREDENTIALS_PATH}")
            raise
        except Exception as e:
            logger.error(f"Error initializing Google Sheets client: {str(e)}")
            raise
    
    def format_products_for_sheet(self, products: List[Product]) -> List[List]:
        """
        Format products for Google Sheets output
        
        Args:
            products: List of Product objects
            
        Returns:
            List of rows (each row is a list of values)
        """
        rows = []
        # Header row
        rows.append([
            "Product Name",
            "Product Description",
            "Product Identifier",
            "Date",
            "Price",
            "Ounces",
            "Price Per Ounce",
            "Price Promotion",
            "Week",
            "Store"
        ])
        
        # Data rows
        for product in products:
            rows.append([
                product.product_name,
                product.product_description,
                product.product_identifier,
                product.date.isoformat(),
                product.price,
                product.ounces,
                product.price_per_ounce,
                product.price_promotion or "",
                product.week,
                product.store
            ])
        
        return rows
    
    def create_weekly_tab(self, week: int, products: List[Product]) -> tuple:
        """
        Create or update a tab for the given week and add products
        
        Args:
            week: Week number (1-4)
            products: List of Product objects for this week
            
        Returns:
            Tuple of (URL to the sheet tab, new_records_count, total_records_count)
        """
        if not self.sheet:
            raise ValueError("Google Sheet not initialized")
        
        tab_name = f"Week {week}"
        
        try:
            # Check if tab already exists
            try:
                worksheet = self.sheet.worksheet(tab_name)
                logger.info(f"Tab '{tab_name}' already exists")
                
                # Get existing data to check for duplicates
                existing_data = worksheet.get_all_values()
                existing_count = len(existing_data) - 1 if len(existing_data) > 1 else 0
                
                # Format new products
                new_rows = self.format_products_for_sheet(products)
                # Remove header row since we're appending
                new_rows = new_rows[1:]
                
                # Append new records
                if new_rows:
                    worksheet.append_rows(new_rows)
                    logger.info(f"Added {len(new_rows)} new records to existing tab")
                
                new_records_count = len(new_rows)
                total_records_count = existing_count + new_records_count
                
            except gspread.exceptions.WorksheetNotFound:
                # Create new worksheet
                worksheet = self.sheet.add_worksheet(
                    title=tab_name,
                    rows=len(products) + 100,
                    cols=10
                )
                logger.info(f"Created new tab: {tab_name}")
                
                # Format data for output
                rows = self.format_products_for_sheet(products)
                
                # Write data to sheet
                worksheet.update('A1', rows)
                
                new_records_count = len(products)
                total_records_count = len(products)
                logger.info(f"Populated new tab '{tab_name}' with {len(products)} records")
            
            # Format header row (bold)
            worksheet.format('A1:J1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
            
            # Auto-resize columns
            worksheet.columns_auto_resize(0, 9)
            
            # Return URL to the worksheet
            sheet_url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit#gid={worksheet.id}"
            return sheet_url, new_records_count, total_records_count
            
        except Exception as e:
            logger.error(f"Error creating/updating tab '{tab_name}': {str(e)}")
            raise
    
    def create_daily_tab(self, date_str: str, products: List[Product]) -> Tuple[str, int, int]:
        """
        Create or update a daily tab labeled with the date
        
        Args:
            date_str: Date string in format 'YYYY-MM-DD'
            products: List of Product objects for this day
            
        Returns:
            Tuple of (URL to the sheet tab, new_records_count, total_records_count)
        """
        if not self.sheet:
            raise ValueError("Google Sheet not initialized")
        
        # Tab name format: YYYY-MM-DD (e.g., "2024-01-15")
        tab_name = date_str
        
        try:
            # Check if tab already exists
            try:
                worksheet = self.sheet.worksheet(tab_name)
                logger.info(f"Tab '{tab_name}' already exists, appending new data")
                
                # Get existing data to check for duplicates
                existing_data = worksheet.get_all_values()
                existing_count = len(existing_data) - 1 if len(existing_data) > 1 else 0
                
                # Format new products
                new_rows = self.format_products_for_sheet(products)
                # Remove header row since we're appending
                new_rows = new_rows[1:]
                
                # Append new records
                if new_rows:
                    worksheet.append_rows(new_rows)
                    logger.info(f"Added {len(new_rows)} new records to existing tab")
                
                new_records_count = len(new_rows)
                total_records_count = existing_count + new_records_count
                
            except gspread.exceptions.WorksheetNotFound:
                # Create new worksheet
                worksheet = self.sheet.add_worksheet(
                    title=tab_name,
                    rows=len(products) + 100,
                    cols=10
                )
                logger.info(f"Created new daily tab: {tab_name}")
                
                # Format data for output
                rows = self.format_products_for_sheet(products)
                
                # Write data to sheet
                worksheet.update('A1', rows)
                
                new_records_count = len(products)
                total_records_count = len(products)
                logger.info(f"Populated new tab '{tab_name}' with {len(products)} records")
            
            # Format header row (bold)
            worksheet.format('A1:J1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
            
            # Auto-resize columns
            worksheet.columns_auto_resize(0, 9)
            
            # Return URL to the worksheet
            sheet_url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit#gid={worksheet.id}"
            return sheet_url, new_records_count, total_records_count
            
        except Exception as e:
            logger.error(f"Error creating/updating daily tab '{tab_name}': {str(e)}")
            raise
    
    def get_sheet_url(self) -> str:
        """Get the base URL of the Google Sheet"""
        return f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit"
    
    def get_or_create_monthly_sheet(self, month_year: str = None) -> Tuple[gspread.Spreadsheet, str]:
        """
        Get or use the configured Google Sheet (use existing sheet instead of creating new ones)
        
        Args:
            month_year: Month-year string in format "YYYY-MM" (default: current month)
        
        Returns:
            Tuple of (spreadsheet object, sheet_id)
        """
        if month_year is None:
            month_year = get_month_year_string()
        
        # Use the configured sheet instead of creating new ones
        if self.sheet and self.sheet_id:
            logger.info(f"Using configured Google Sheet: {self.sheet.title} (ID: {self.sheet_id})")
            logger.info(f"Will add weekly tab for {month_year}")
            return self.sheet, self.sheet_id
        
        # Fallback: Try to find or create monthly sheet (only if no configured sheet)
        sheet_title = f"Publix Soda Prices - {month_year}"
        
        try:
            # Try to find existing sheet by title
            try:
                all_sheets = self.client.openall()
                for sheet in all_sheets:
                    if sheet.title == sheet_title:
                        logger.info(f"Found existing monthly sheet: {sheet_title}")
                        return sheet, sheet.id
                
                # Not found, create new monthly sheet
                logger.info(f"Monthly sheet '{sheet_title}' not found, creating new one...")
                sheet = self.client.create(sheet_title)
                logger.info(f"Created new monthly sheet: {sheet_title} (ID: {sheet.id})")
                return sheet, sheet.id
                
            except Exception as search_error:
                logger.warning(f"Error searching for sheet: {search_error}, creating new one...")
                sheet = self.client.create(sheet_title)
                logger.info(f"Created new monthly sheet: {sheet_title} (ID: {sheet.id})")
                return sheet, sheet.id
                
        except Exception as e:
            logger.error(f"Error getting/creating monthly sheet: {str(e)}")
            raise
    
    def create_weekly_tab_in_monthly_sheet(self, week: int, products: List[Product], month_year: str = None) -> Tuple[str, int, int, str]:
        """
        Create or update a weekly tab in the monthly sheet
        
        Args:
            week: Week number (1-4)
            products: List of Product objects for this week
            month_year: Month-year string in format "YYYY-MM" (default: current month)
        
        Returns:
            Tuple of (URL to the sheet tab, new_records_count, total_records_count, sheet_id)
        """
        if month_year is None:
            month_year = get_month_year_string()
        
        # Get or use the configured sheet
        monthly_sheet, sheet_id = self.get_or_create_monthly_sheet(month_year)
        
        # Tab name format: "YYYY-MM Week N" (e.g., "2026-01 Week 2")
        tab_name = f"{month_year} Week {week}"
        
        try:
            # Check if tab already exists
            try:
                worksheet = monthly_sheet.worksheet(tab_name)
                logger.info(f"Tab '{tab_name}' already exists - overwriting with fresh data")
                
                # Clear existing data and write fresh
                worksheet.clear()
                
                # Format data for output
                rows = self.format_products_for_sheet(products)
                
                # Write fresh data from scratch
                worksheet.update('A1', rows)
                
                new_records_count = len(products)
                total_records_count = len(products)
                logger.info(f"Overwrote tab '{tab_name}' with {len(products)} fresh records")
                
            except gspread.exceptions.WorksheetNotFound:
                # Create new worksheet
                worksheet = monthly_sheet.add_worksheet(
                    title=tab_name,
                    rows=len(products) + 100,
                    cols=10
                )
                logger.info(f"Created new tab: {tab_name} in monthly sheet")
                
                # Format data for output
                rows = self.format_products_for_sheet(products)
                
                # Write data to sheet
                worksheet.update('A1', rows)
                
                new_records_count = len(products)
                total_records_count = len(products)
                logger.info(f"Populated new tab '{tab_name}' with {len(products)} records")
            
            # Format header row (bold)
            worksheet.format('A1:J1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
            
            # Auto-resize columns
            worksheet.columns_auto_resize(0, 9)
            
            # Return URL to the worksheet
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={worksheet.id}"
            return sheet_url, new_records_count, total_records_count, sheet_id
            
        except Exception as e:
            logger.error(f"Error creating/updating weekly tab '{tab_name}': {str(e)}")
            raise
    
    def create_monthly_tab(self, month_year: str, products: List[Product]) -> Tuple[str, int, int, str]:
        """
        Create or update a monthly tab in the monthly sheet and add all monthly products
        
        Args:
            month_year: Month-year string (e.g., "2026-01")
            products: List of Product objects for the entire month
            
        Returns:
            Tuple of (URL to the sheet tab, new_records_count, total_records_count, sheet_id)
        """
        try:
            monthly_sheet, sheet_id = self.get_or_create_monthly_sheet(month_year)
            
            # Create tab name for monthly report
            tab_name = f"Monthly Report - {month_year}"
            
            # Check if tab already exists
            try:
                worksheet = monthly_sheet.worksheet(tab_name)
                logger.info(f"Monthly tab '{tab_name}' already exists, updating...")
                
                # Clear existing data
                worksheet.clear()
                
                # Format data for output
                rows = self.format_products_for_sheet(products)
                
                # Write data to sheet
                worksheet.update('A1', rows)
                
                new_records_count = len(products)
                total_records_count = len(products)
                logger.info(f"Updated monthly tab '{tab_name}' with {len(products)} records")
            except gspread.WorksheetNotFound:
                # Create new monthly tab
                worksheet = monthly_sheet.add_worksheet(
                    title=tab_name,
                    rows=len(products) + 1,
                    cols=10
                )
                logger.info(f"Created new monthly tab: {tab_name} in monthly sheet")
                
                # Format data for output
                rows = self.format_products_for_sheet(products)
                
                # Write data to sheet
                worksheet.update('A1', rows)
                
                new_records_count = len(products)
                total_records_count = len(products)
                logger.info(f"Populated new monthly tab '{tab_name}' with {len(products)} records")
            
            # Format header row (bold)
            worksheet.format('A1:J1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
            
            # Auto-resize columns
            worksheet.columns_auto_resize(0, 9)
            
            # Return URL to the worksheet
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={worksheet.id}"
            return sheet_url, new_records_count, total_records_count, sheet_id
            
        except Exception as e:
            logger.error(f"Error creating/updating monthly tab '{tab_name}': {str(e)}")
            raise