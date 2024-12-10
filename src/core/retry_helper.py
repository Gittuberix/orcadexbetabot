from functools import wraps
import asyncio
import logging

logger = logging.getLogger(__name__)

def async_retry(retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < retries - 1:
                        await asyncio.sleep(delay * (2 ** attempt))
            logger.error(f"All {retries} attempts failed")
            raise last_exception
        return wrapper
    return decorator 