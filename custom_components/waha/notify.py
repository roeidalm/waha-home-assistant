"""WhatsApp notification service using WAHA API."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.notify import (
    ATTR_MESSAGE,
    BaseNotificationService,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN
from .helpers import validate_phone_number

_LOGGER = logging.getLogger(__name__)

async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType = None,
) -> Optional[BaseNotificationService]:
    """Get the WAHA notification service."""
    if discovery_info is None:
        return None

    entry_id = discovery_info["entry_id"]
    phone_number = discovery_info.get("phone_number")
    
    if DOMAIN not in hass.data or entry_id not in hass.data[DOMAIN]:
        _LOGGER.error("WAHA integration not found for entry %s", entry_id)
        return None

    entry_data = hass.data[DOMAIN][entry_id]
    client = entry_data["client"]
    
    if phone_number:
        # Create a service for a specific phone number
        return WahaPhoneNotificationService(hass, client, phone_number)
    else:
        # Create a general service that can send to any number
        return WahaGeneralNotificationService(hass, client)

class WahaGeneralNotificationService(BaseNotificationService):
    """General notification service that can send to any phone number."""

    def __init__(self, hass: HomeAssistant, client):
        """Initialize the service."""
        self.hass = hass
        self.client = client

    async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to specified targets via data."""
        data = kwargs.get("data", {})
        phone_number = data.get("phone_number")
        
        if not phone_number:
            _LOGGER.error("No phone_number specified in data")
            return

        try:
            # Validate phone number
            validated_phone = validate_phone_number(phone_number)
            if not validated_phone:
                _LOGGER.error("Invalid phone number format: %s", phone_number)
                return

            # Format phone number for WAHA API
            chat_id = validated_phone
            if not chat_id.endswith("@c.us"):
                chat_id = f"{validated_phone}@c.us"

            success = await self.client.send_message(chat_id, message)
            if success:
                _LOGGER.info("Message sent successfully to %s", phone_number)
            else:
                _LOGGER.error("Failed to send message to %s", phone_number)
        except Exception as err:
            _LOGGER.error("Error sending message to %s: %s", phone_number, err)

class WahaPhoneNotificationService(BaseNotificationService):
    """Notification service for a specific phone number."""

    def __init__(self, hass: HomeAssistant, client, phone_number: str):
        """Initialize the service."""
        self.hass = hass
        self.client = client
        self.phone_number = phone_number

    async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to the configured phone number."""
        try:
            # Validate phone number
            validated_phone = validate_phone_number(self.phone_number)
            if not validated_phone:
                _LOGGER.error("Invalid phone number format: %s", self.phone_number)
                return

            # Format phone number for WAHA API
            chat_id = validated_phone
            if not chat_id.endswith("@c.us"):
                chat_id = f"{validated_phone}@c.us"

            success = await self.client.send_message(chat_id, message)
            if success:
                _LOGGER.info("Message sent successfully to %s", self.phone_number)
            else:
                _LOGGER.error("Failed to send message to %s", self.phone_number)
        except Exception as err:
            _LOGGER.error("Error sending message to %s: %s", self.phone_number, err) 