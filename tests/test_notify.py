import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from custom_components.waha.notify import WahaNotificationService

@pytest.mark.asyncio
async def test_send_message_valid_number():
    client = AsyncMock()
    service = WahaNotificationService(client, ['+1234567890'])
    await service.async_send_message('Hello!', target=['+1234567890'])
    client.send_message.assert_awaited_with('+1234567890', 'Hello!')

@pytest.mark.asyncio
async def test_send_message_invalid_number():
    client = AsyncMock()
    service = WahaNotificationService(client, ['invalid'])
    with patch('custom_components.waha.notify._LOGGER') as mock_logger:
        await service.async_send_message('Hello!', target=['invalid'])
        client.send_message.assert_not_awaited()
        mock_logger.error.assert_any_call('Invalid phone number format: invalid')

@pytest.mark.asyncio
async def test_send_message_no_targets():
    client = AsyncMock()
    service = WahaNotificationService(client, [])
    with patch('custom_components.waha.notify._LOGGER') as mock_logger:
        await service.async_send_message('Hello!')
        client.send_message.assert_not_awaited()
        mock_logger.error.assert_any_call('No recipients provided and no default recipients configured') 