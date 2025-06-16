"""Button entities for WAHA WhatsApp integration."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    CONF_PHONE_NUMBERS,
)
from .device import WahaPhoneDevice
from .api_client import WahaApiClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WAHA button entities."""
    # Get the client and phone numbers from the integration data
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    client = entry_data["client"]
    phone_numbers = entry_data.get("phone_numbers", [])
    
    # Create button entities for each phone number
    entities = []
    for phone_number in phone_numbers:
        device = WahaPhoneDevice(phone_number)
        entities.append(WahaMessageButton(client, device, config_entry.entry_id))
    
    async_add_entities(entities)

class WahaMessageButton(ButtonEntity):
    """Button entity for sending WhatsApp messages."""
    
    def __init__(self, client: WahaApiClient, device: WahaPhoneDevice, entry_id: str):
        """Initialize the message button."""
        self._client = client
        self._device = device
        self._entry_id = entry_id
        self._attr_name = f"Send Message to {device.name}"
        self._attr_unique_id = f"{entry_id}_{device.device_id}_send_message"
        self._attr_icon = "mdi:message-text"
        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self._device.device_info
        
    async def async_press(self) -> None:
        """Handle button press - this will be used by services."""
        # This button doesn't do anything on press by itself
        # It's mainly for UI organization and services will handle the actual sending
        _LOGGER.debug("Message button pressed for %s", self._device.phone_number) 