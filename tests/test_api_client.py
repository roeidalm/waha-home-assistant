import pytest
import aiohttp
from unittest.mock import AsyncMock, patch
from custom_components.waha.api_client import WahaApiClient

@pytest.mark.asyncio
async def test_test_connection_success():
    client = WahaApiClient(None, 'http://localhost:3000', None, 'default')
    with patch('aiohttp.ClientSession.get', new_callable=AsyncMock) as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_get.return_value.__aenter__.return_value = mock_resp
        assert await client.test_connection() is True

@pytest.mark.asyncio
async def test_test_connection_failure():
    client = WahaApiClient(None, 'http://localhost:3000', None, 'default')
    with patch('aiohttp.ClientSession.get', new_callable=AsyncMock) as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status = 500
        mock_get.return_value.__aenter__.return_value = mock_resp
        assert await client.test_connection() is False

@pytest.mark.asyncio
async def test_send_message_success():
    client = WahaApiClient(None, 'http://localhost:3000', None, 'default')
    with patch('aiohttp.ClientSession.post', new_callable=AsyncMock) as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_post.return_value.__aenter__.return_value = mock_resp
        assert await client.send_message('+1234567890', 'Hello!') is True

@pytest.mark.asyncio
async def test_send_message_failure():
    client = WahaApiClient(None, 'http://localhost:3000', None, 'default')
    with patch('aiohttp.ClientSession.post', new_callable=AsyncMock) as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 500
        mock_resp.text = AsyncMock(return_value='error')
        mock_post.return_value.__aenter__.return_value = mock_resp
        assert await client.send_message('+1234567890', 'Hello!') is False

@pytest.mark.asyncio
async def test_register_webhook_success():
    client = WahaApiClient(None, 'http://localhost:3000', None, 'default')
    with patch('aiohttp.ClientSession.post', new_callable=AsyncMock) as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_post.return_value.__aenter__.return_value = mock_resp
        assert await client.register_webhook('http://ha/webhook') is True

@pytest.mark.asyncio
async def test_register_webhook_failure():
    client = WahaApiClient(None, 'http://localhost:3000', None, 'default')
    with patch('aiohttp.ClientSession.post', new_callable=AsyncMock) as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 500
        mock_resp.text = AsyncMock(return_value='error')
        mock_post.return_value.__aenter__.return_value = mock_resp
        assert await client.register_webhook('http://ha/webhook') is False 