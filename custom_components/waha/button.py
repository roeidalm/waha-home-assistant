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
from .device import WahaPhoneDevice, WahaDevice
from .api_client import WahaApiClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WAHA button entities."""
    # Get the API client from the integration data
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    api_client = entry_data["api_client"]
    phone_numbers = entry_data.get("phone_numbers", [])
    
    # Create button entities for each phone number
    entities = []
    for phone_number in phone_numbers:
        device = WahaPhoneDevice(phone_number)
        entities.append(WahaMessageButton(api_client, device, config_entry.entry_id))
    
    # Create main device and test button
    device = WahaDevice(config_entry)
    
    buttons = [
        WahaTestConnectionButton(api_client, device, config_entry),
    ]
    
    async_add_entities(entities + buttons)

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

class WahaTestConnectionButton(ButtonEntity):
    """Button to test WAHA connection."""

    def __init__(self, api_client, device, config_entry):
        """Initialize the button."""
        self._api_client = api_client
        self._device = device
        self._config_entry = config_entry
        self._attr_name = "Test WAHA Connection"
        self._attr_unique_id = f"{config_entry.entry_id}_test_connection"
        self._attr_icon = "mdi:connection"

    @property
    def device_info(self):
        """Return device information."""
        return self._device.device_info

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            _LOGGER.info("Testing WAHA connection...")
            status = await self._api_client.get_session_status()
            if status:
                _LOGGER.info("WAHA connection test successful: %s", status)
            else:
                _LOGGER.warning("WAHA connection test failed - no status returned")
        except Exception as err:
            _LOGGER.error("WAHA connection test failed: %s", err) 