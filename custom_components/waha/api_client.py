import logging
from typing import Optional
import aiohttp
from .helpers import async_retry
import time
from collections import deque
import asyncio
import traceback
_LOGGER = logging.getLogger(__name__)

class WahaApiClient:
    def __init__(self, hass, base_url: str, api_key: Optional[str], session_name: str, rate_limit: int = 10):
        self.hass = hass
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session_name = session_name
        # Rate limiting
        self.rate_limit = rate_limit  # Max messages per minute
        self.message_timestamps = deque(maxlen=rate_limit)
        self._rate_limit_lock = asyncio.Lock()

    async def _wait_for_rate_limit(self):
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
        url = f"{self.base_url}/api/server/status"
        headers = self._get_headers()
        headers["accept"] = "application/json"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        return True
                    _LOGGER.error("WAHA status check failed: %s", resp.status)
        except Exception as exc:
            _LOGGER.error("WAHA connection test failed for URL %s: %s\n%s", url, exc, traceback.format_exc())
        return False

    async def send_message(self, phone: str, message: str) -> bool:
        await self._wait_for_rate_limit()
        async def _send():
            url = f"{self.base_url}/api/sendText"
            headers = self._get_headers()
            payload = {
                "chatId": phone,
                "body": message,
                "session": self.session_name,
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=15) as resp:
                    if resp.status == 200:
                        _LOGGER.debug("Message sent to %s", phone)
                        return True
                    response_text = await resp.text()
                    raise Exception(f"Failed to send message to {phone}: {resp.status} {response_text}")
        try:
            return await async_retry(_send, attempts=3, delay=1.0)
        except Exception as exc:
            _LOGGER.error("Error sending message to %s: %s", phone, exc)
            return False

    async def register_webhook(self, webhook_url: str) -> bool:
        async def _register():
            url = f"{self.base_url}/api/setWebhook"
            headers = self._get_headers()
            payload = {
                "webhook": webhook_url,
                "session": self.session_name,
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=15) as resp:
                    if resp.status == 200:
                        _LOGGER.info("Webhook registered: %s", webhook_url)
                        return True
                    response_text = await resp.text()
                    raise Exception(f"Failed to register webhook: {resp.status} {response_text}")
        try:
            return await async_retry(_register, attempts=3, delay=1.0)
        except Exception as exc:
            _LOGGER.error("Error registering webhook: %s", exc)
            return False

    def _get_headers(self):
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers 