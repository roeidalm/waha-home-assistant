import logging
from typing import Optional, Dict, Any, Union, List
import aiohttp
from aiohttp import ClientSession, ClientTimeout
import json
from .helpers import async_retry
import time
from collections import deque
import asyncio
import traceback
from datetime import datetime, timedelta
from urllib.parse import urljoin

_LOGGER = logging.getLogger(__name__)

class WahaApiError(Exception):
    """Base exception for WAHA API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text

class WahaConnectionError(WahaApiError):
    """Exception for connection errors."""
    pass

class WahaAuthenticationError(WahaApiError):
    """Exception for authentication errors."""
    pass

class WahaRateLimitError(WahaApiError):
    """Exception for rate limit errors."""
    pass

class WahaApiClient:
    """API client for WAHA (WhatsApp Home Assistant) API."""

    def __init__(
        self, 
        hass: Any,
        base_url: str, 
        api_key: Optional[str], 
        session_name: str, 
        rate_limit: int = 10,
        timeout: int = 30
    ) -> None:
        """Initialize the WAHA API client.
        
        Args:
            hass: Home Assistant instance
            base_url: Base URL of the WAHA API
            api_key: Optional API key for authentication
            session_name: WhatsApp session name
            rate_limit: Maximum number of messages per minute
            timeout: Request timeout in seconds
        """
        self.hass = hass
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session_name = session_name
        self.timeout = ClientTimeout(total=timeout)
        self._session: Optional[ClientSession] = None
        
        # Rate limiting
        self.rate_limit = rate_limit
        self.message_timestamps: deque = deque(maxlen=rate_limit)
        self._rate_limit_lock = asyncio.Lock()

    async def _get_session(self) -> ClientSession:
        """Get or create an aiohttp ClientSession."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def close(self) -> None:
        """Close the API client session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Any:
        """Make an API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without leading slash)
            data: Request body data
            params: URL parameters
            timeout: Request timeout in seconds
            
        Returns:
            Any: Response data
            
        Raises:
            WahaConnectionError: On connection errors
            WahaAuthenticationError: On authentication failure
            WahaRateLimitError: On rate limit exceeded
            WahaApiError: On other API errors
        """
        # Remove any leading slashes but keep the 'api/' prefix
        endpoint = endpoint.lstrip('/')
        url = urljoin(self.base_url + '/', endpoint)
        
        session = await self._get_session()
        
        if timeout and timeout != self.timeout.total:
            timeout_obj = ClientTimeout(total=timeout)
        else:
            timeout_obj = self.timeout

        try:
            async with session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=self._get_headers(),
                timeout=timeout_obj
            ) as resp:
                if resp.status == 401:
                    raise WahaAuthenticationError("Authentication failed", resp.status)
                elif resp.status == 429:
                    raise WahaRateLimitError("Rate limit exceeded", resp.status)
                elif resp.status != 200:
                    text = await resp.text()
                    raise WahaApiError(
                        f"API request failed: {resp.status}",
                        resp.status,
                        text
                    )
                
                try:
                    return await resp.json()
                except json.JSONDecodeError as exc:
                    text = await resp.text()
                    raise WahaApiError(
                        f"Invalid JSON response: {exc}",
                        resp.status,
                        text
                    )
                    
        except asyncio.TimeoutError as exc:
            raise WahaConnectionError(f"Request timed out: {exc}")
        except aiohttp.ClientError as exc:
            raise WahaConnectionError(f"Connection error: {exc}")

    async def _wait_for_rate_limit(self) -> None:
        """Wait if necessary to respect the rate limit."""
        async with self._rate_limit_lock:
            now = time.time()
            # Remove timestamps older than 60 seconds
            while self.message_timestamps and now - self.message_timestamps[0] > 60:
                self.message_timestamps.popleft()
            
            # If we've reached the rate limit, wait until we can send again
            if len(self.message_timestamps) >= self.rate_limit:
                wait_time = 60 - (now - self.message_timestamps[0])
                if wait_time > 0:
                    _LOGGER.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                    await asyncio.sleep(wait_time)
            
            # Add current timestamp
            self.message_timestamps.append(time.time())

    async def test_connection(self) -> bool:
        """Test the connection to the WAHA server.
        
        Returns:
            bool: True if connection is successful
        """
        try:
            # Use the /api/version endpoint which is available in WAHA CORE
            response = await self._make_request("GET", "api/version", timeout=10)
            # Verify we get a valid response with version info
            if isinstance(response, dict) and "version" in response:
                _LOGGER.debug("WAHA connection test successful. Version: %s", response.get("version"))
                return True
            else:
                _LOGGER.error("WAHA connection test failed: Invalid response format")
                return False
        except Exception as exc:
            _LOGGER.error("WAHA connection test failed: %s\n%s", exc, traceback.format_exc())
            return False

    async def send_message(
        self, 
        phone: str, 
        message: str,
        retry_attempts: int = 3,
        retry_delay: float = 1.0
    ) -> bool:
        """Send a WhatsApp message.
        
        Args:
            phone: Recipient's phone number
            message: Message text
            retry_attempts: Number of retry attempts
            retry_delay: Delay between retries in seconds
        
        Returns:
            bool: True if message was sent successfully
        """
        await self._wait_for_rate_limit()
        
        async def _send() -> bool:
            payload = {
                "session": self.session_name,
                "chatId": phone,
                "text": message,
            }
            try:
                # Use the correct WAHA endpoint format: /api/sendText
                await self._make_request("POST", "api/sendText", data=payload, timeout=15)
                _LOGGER.debug("Message sent to %s", phone)
                return True
            except WahaApiError as exc:
                raise Exception(f"Failed to send message to {phone}: {exc}")

        try:
            return await async_retry(_send, attempts=retry_attempts, delay=retry_delay)
        except Exception as exc:
            _LOGGER.error("Error sending message to %s: %s", phone, exc)
            return False



    async def get_qr_code(self) -> Optional[str]:
        """Get the QR code for WhatsApp Web authentication.
        
        Returns:
            Optional[str]: QR code data or None if not available
        """
        try:
            # Use the correct WAHA endpoint format: /api/sessions/qr with session parameter
            response = await self._make_request(
                "GET", 
                "api/sessions/qr",
                params={"session": self.session_name}
            )
            return response.get("qr")
        except WahaApiError as exc:
            _LOGGER.error("Failed to get QR code: %s", exc)
            return None

    async def get_session_status(self) -> Optional[str]:
        """Get the current WhatsApp session status.
        
        Returns:
            Optional[str]: Session status or None if request failed
        """
        try:
            # Use the correct WAHA endpoint format: /api/sessions/{session}
            endpoint = f"api/sessions/{self.session_name}"
            response = await self._make_request("GET", endpoint)
            return response.get("status")
        except WahaApiError as exc:
            _LOGGER.error("Failed to get session status: %s", exc)
            return None

    async def logout(self) -> bool:
        """Logout from the WhatsApp session.
        
        Returns:
            bool: True if logout was successful
        """
        try:
            # Use the correct WAHA endpoint format: /api/sessions/logout
            await self._make_request(
                "POST", 
                "api/sessions/logout",
                data={"session": self.session_name}
            )
            return True
        except WahaApiError as exc:
            _LOGGER.error("Failed to logout: %s", exc)
            return False 