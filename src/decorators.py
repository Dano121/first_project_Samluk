"""Cross-cutting behaviour that does not belong to any single layer.

"""

import functools
import logging
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)


def log_step(func: Callable) -> Callable:
    """Log the name of the step and how long it took."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        started = time.perf_counter()
        logger.info("start  %s", func.__name__)
        try:
            return func(*args, **kwargs)
        finally:
            # `finally` on purpose: a step that blew up is exactly the one whose
            # duration you want in the log.
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.info("done   %s in %.0f ms", func.__name__, elapsed_ms)

    return wrapper


def retry(
    max_attempts: int = 3,
    delay: float = 0.5,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable:
    """Retry the wrapped function, but only on the exception types listed.

    Retrying blindly hides real problems: a wrong password will not fix itself on the
    third attempt, it will only take three times as long to find out.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as error:
                    if attempt == max_attempts:
                        logger.error(
                            "%s: attempt %d/%d failed, giving up",
                            func.__name__,
                            attempt,
                            max_attempts,
                        )
                        raise
                    logger.warning(
                        "%s: attempt %d/%d failed (%s), retrying in %.1f s",
                        func.__name__,
                        attempt,
                        max_attempts,
                        type(error).__name__,
                        delay,
                    )
                    time.sleep(delay)

        return wrapper

    return decorator
