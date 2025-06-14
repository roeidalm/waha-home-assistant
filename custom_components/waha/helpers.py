import asyncio
import logging
import re
from typing import Any, Callable, Coroutine, Optional, TypeVar

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")

async def async_retry(
    func: Callable[..., Coroutine[Any, Any, T]],
    attempts: int = 3,
    delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
) -> T:
    """Retry an async function with exponential backoff."""
    last_exception = None
    current_delay = delay

    for attempt in range(1, attempts + 1):
        try:
            return await func()
        except exceptions as ex:
            last_exception = ex
            if attempt == attempts:
                break

            _LOGGER.debug(
                f"Attempt {attempt} failed with error: {ex}. Retrying in {current_delay} seconds..."
            )
            await asyncio.sleep(current_delay)
            current_delay = min(current_delay * backoff_factor, max_delay)

    raise last_exception

def validate_phone_number(phone_number: str) -> Optional[str]:
    """Validate and format a phone number for WhatsApp.
    Returns formatted number or None if invalid.
    """
    cleaned = re.sub(r'[^0-9+]', '', phone_number)
    if re.match(r'^\+[0-9]{10,15}$', cleaned):
        return cleaned
    if re.match(r'^[0-9]{10,15}$', cleaned):
        return f"+{cleaned}"
    return None

def format_phone_number(phone_number: str) -> str:
    """Format a phone number to WhatsApp's required format (+<countrycode><number>)."""
    cleaned = re.sub(r'[^0-9]', '', phone_number)
    if phone_number.startswith('+'):
        return f'+{cleaned}'
    # If no +, assume international format is required
    return f'+{cleaned}' 