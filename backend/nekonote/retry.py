"""Retry decorator and error handling utilities for nekonote scripts.

Usage::

    from nekonote import retry

    @retry.retry(max_attempts=3, delay=1)
    def flaky_operation():
        browser.click("#submit")
"""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Retry a function on failure.

    Args:
        max_attempts: Maximum number of attempts (including the first).
        delay: Initial delay between retries in seconds.
        backoff: Multiplier applied to delay after each retry.
        exceptions: Tuple of exception types to catch.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]

    return decorator
