import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_waha_integration_setup(hass: HomeAssistant):
    config = {
        'waha': {
            'base_url': 'http://localhost:3000',
            'default_recipients': ['+1234567890'],
            'session_name': 'default',
        }
    }
    with patch('custom_components.waha.api_client.WahaApiClient.test_connection', AsyncMock(return_value=True)):
        assert await async_setup_component(hass, 'waha', config)

@pytest.mark.asyncio
async def test_notify_service(hass: HomeAssistant):
    with patch('custom_components.waha.api_client.WahaApiClient.send_message', AsyncMock(return_value=True)):
        service = AsyncMock()
        service.send_message = AsyncMock(return_value=True)
        hass.data = {'waha': {'entryid': {'client': service, 'default_recipients': ['+1234567890']}}}
        from custom_components.waha.notify import WahaNotificationService
        notify_service = WahaNotificationService(service, ['+1234567890'])
        await notify_service.async_send_message('Hello!', target=['+1234567890'])
        service.send_message.assert_awaited_with('+1234567890', 'Hello!')

@pytest.mark.asyncio
async def test_webhook_event_firing(hass: HomeAssistant):
    from custom_components.waha.webhook import is_valid_webhook_request
    from aiohttp import web
    request = AsyncMock(spec=web.Request)
    request.json = AsyncMock(return_value={
        'sender': '+1234567890',
        'body': 'Hello!',
        'timestamp': '2023-01-01T12:00:00Z',
        'session': 'default',
        'id': 'msgid123',
    })
    hass.data = {'waha': {'entryid': {}}}
    webhook_id = 'waha_entryid_webhook'
    assert is_valid_webhook_request(hass, webhook_id, request) 