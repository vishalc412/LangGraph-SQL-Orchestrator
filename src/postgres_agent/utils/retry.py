"""
Retry utilities for handling transient failures.
"""

import time
from functools import wraps
from typing import Callable, TypeVar, Any
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        backoff_factor: Multiplier for delay after each retry
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorated function

    Example:
        >>> @retry_with_backoff(max_retries=3, exceptions=(ConnectionError,))
        ... def connect_to_database():
        ...     ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries + 1} attempts"
                        )
                        raise

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class RetryContext:
    """
    Context manager for retry logic.

    Example:
        >>> with RetryContext(max_retries=3) as retry:
        ...     while retry.should_retry():
        ...         try:
        ...             result = risky_operation()
        ...             break
        ...         except Exception as e:
        ...             retry.record_failure(e)
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 30.0
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.attempt = 0
        self.delay = initial_delay
        self.last_exception = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def should_retry(self) -> bool:
        """Check if another retry attempt should be made."""
        return self.attempt <= self.max_retries

    def record_failure(self, exception: Exception):
        """Record a failed attempt and sleep before next retry."""
        self.last_exception = exception
        self.attempt += 1

        if self.attempt <= self.max_retries:
            logger.warning(
                f"Attempt {self.attempt}/{self.max_retries + 1} failed: {exception}. "
                f"Retrying in {self.delay:.1f}s..."
            )
            time.sleep(self.delay)
            self.delay = min(self.delay * self.backoff_factor, self.max_delay)
        else:
            logger.error(f"All {self.max_retries + 1} attempts failed")
            raise exception
