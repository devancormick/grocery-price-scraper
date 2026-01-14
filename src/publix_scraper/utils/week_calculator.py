"""
Utility functions for calculating week of month
"""
from datetime import date, datetime
from calendar import monthrange


def get_week_of_month(target_date: date = None) -> int:
    """
    Calculate which week of the month it is (1-4)
    
    Weeks are calculated as:
    - Week 1: Days 1-7
    - Week 2: Days 8-14
    - Week 3: Days 15-21
    - Week 4: Days 22-end of month
    
    Args:
        target_date: Date to calculate week for (default: today)
    
    Returns:
        Week number (1-4)
    """
    if target_date is None:
        target_date = date.today()
    
    day = target_date.day
    
    if day <= 7:
        return 1
    elif day <= 14:
        return 2
    elif day <= 21:
        return 3
    else:
        return 4


def get_month_year_string(target_date: date = None) -> str:
    """
    Get month-year string for sheet naming (e.g., "2024-01")
    
    Args:
        target_date: Date to use (default: today)
    
    Returns:
        String in format "YYYY-MM"
    """
    if target_date is None:
        target_date = date.today()
    
    return target_date.strftime("%Y-%m")


def is_last_week_of_month(target_date: date = None) -> bool:
    """
    Check if the current date is in the last week of the month
    
    Args:
        target_date: Date to check (default: today)
    
    Returns:
        True if it's the last week of the month
    """
    if target_date is None:
        target_date = date.today()
    
    week = get_week_of_month(target_date)
    return week == 4
