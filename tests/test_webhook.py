import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiohttp import web
from custom_components.waha.webhook import is_valid_webhook_request
from homeassistant.core import HomeAssistant

@pytest.fixture
def hass():
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {'waha': {'entryid123': {}}}
    return hass

@pytest.mark.asyncio
async def test_is_valid_webhook_request_valid(hass):
    request = MagicMock(spec=web.Request)
    webhook_id = 'waha_entryid123_webhook'
    assert is_valid_webhook_request(hass, webhook_id, request) is True

@pytest.mark.asyncio
async def test_is_valid_webhook_request_invalid_prefix(hass):
    request = MagicMock(spec=web.Request)
    webhook_id = 'invalid_entryid123_webhook'
    assert is_valid_webhook_request(hass, webhook_id, request) is False

@pytest.mark.asyncio
async def test_is_valid_webhook_request_invalid_entry(hass):
    request = MagicMock(spec=web.Request)
    webhook_id = 'waha_nonexistent_webhook'
    assert is_valid_webhook_request(hass, webhook_id, request) is False 