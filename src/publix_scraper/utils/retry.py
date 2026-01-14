"""
Retry utilities with exponential backoff
"""
import time
import logging
from typing import Callable, TypeVar, Optional, List, Type
from functools import wraps

from .exceptions import NetworkError, ScrapingError

T = TypeVar('T')
logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called on each retry
                  (exception, attempt_number) -> None
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        if on_retry:
                            on_retry(e, attempt + 1)
                        
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        
                        time.sleep(delay)
                        delay = min(delay * exponential_base, max_delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


def retry_network_request(
    max_retries: int = 3,
    initial_delay: float = 1.0
):
    """
    Specialized retry decorator for network requests
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
    
    Returns:
        Decorated function
    """
    return retry_with_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        exceptions=(NetworkError, ConnectionError, TimeoutError)
    )
