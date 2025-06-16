"""WAHA notification platform."""
import logging
import voluptuous as vol
from typing import Any, Dict, List, Optional

from homeassistant.components.notify import (
    ATTR_MESSAGE,
    ATTR_TARGET,
    PLATFORM_SCHEMA,
    BaseNotificationService,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_PHONE_NUMBERS
from .api_client import WahaApiClient

_LOGGER = logging.getLogger(__name__)

# Define platform schema for manual configuration (not used with config entries)
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required("phone_number"): cv.string,
})


async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> BaseNotificationService | None:
    """Get the WAHA notification service."""
    if discovery_info is None:
        # Manual configuration - not supported
        return None
    
    # Get the phone number from discovery info
    phone_number = discovery_info.get("phone_number")
    if not phone_number:
        _LOGGER.error("No phone number provided in discovery info")
        return None
    
    # Get the API client from the integration data
    entry_id = discovery_info.get("entry_id")
    if not entry_id or entry_id not in hass.data.get(DOMAIN, {}):
        _LOGGER.error("No WAHA integration entry found")
        return None
    
    api_client = hass.data[DOMAIN][entry_id]["api_client"]
    
    return WAHANotificationService(hass, api_client, phone_number)


class WAHANotificationService(BaseNotificationService):
    """WAHA notification service for a specific phone number."""

    def __init__(self, hass: HomeAssistant, api_client: WahaApiClient, phone_number: str):
        """Initialize the notification service."""
        self.hass = hass
        self._api_client = api_client
        self._phone_number = phone_number
        self._name = f"WAHA {phone_number}"

    @property
    def name(self) -> str:
        """Return the name of the notification service."""
        return self._name

    async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to the predefined phone number."""
        # Get message from ATTR_MESSAGE if available
        if ATTR_MESSAGE in kwargs:
            message = kwargs[ATTR_MESSAGE]
        
        try:
            # Handle template rendering
            if hasattr(message, 'async_render'):
                message = message.async_render()
            
            # Convert to string and ensure it's not empty
            message_text = str(message).strip()
            if not message_text:
                _LOGGER.error("Cannot send empty message to %s", self._phone_number)
                return
            
            _LOGGER.info("Sending message via WAHA to %s: %s", self._phone_number, message_text)
            
            result = await self._api_client.send_message(
                chat_id=self._phone_number,
                message=message_text
            )
            
            if result:
                _LOGGER.info("Message sent successfully to %s", self._phone_number)
            else:
                _LOGGER.error("Failed to send message to %s", self._phone_number)
                
        except Exception as err:
            _LOGGER.error("Error sending message to %s: %s", self._phone_number, err) 