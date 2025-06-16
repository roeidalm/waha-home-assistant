"""Sensor entities for WAHA WhatsApp integration."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .api_client import WahaApiClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WAHA sensor entities."""
    # Get the client from the integration data
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    client = entry_data["client"]
    
    # Create sensor entities
    entities = [
        WahaConnectionSensor(client, config_entry.entry_id),
        WahaSessionSensor(client, config_entry.entry_id),
    ]
    
    async_add_entities(entities)

class WahaConnectionSensor(SensorEntity):
    """Sensor for WAHA connection status."""
    
    def __init__(self, client: WahaApiClient, entry_id: str):
        """Initialize the connection sensor."""
        self._client = client
        self._entry_id = entry_id
        self._attr_name = "WAHA Connection Status"
        self._attr_unique_id = f"{entry_id}_connection_status"
        self._attr_icon = "mdi:connection"
        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry_id}_main")},
            name="WAHA WhatsApp Server",
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version="1.0",
        )
        
    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            connected = await self._client.test_connection()
            self._attr_native_value = "Connected" if connected else "Disconnected"
            self._attr_icon = "mdi:connection" if connected else "mdi:connection-off"
        except Exception as exc:
            _LOGGER.error("Failed to update connection status: %s", exc)
            self._attr_native_value = "Unknown"
            self._attr_icon = "mdi:help-circle"

class WahaSessionSensor(SensorEntity):
    """Sensor for WAHA session status."""
    
    def __init__(self, client: WahaApiClient, entry_id: str):
        """Initialize the session sensor."""
        self._client = client
        self._entry_id = entry_id
        self._attr_name = "WAHA Session Status"
        self._attr_unique_id = f"{entry_id}_session_status"
        self._attr_icon = "mdi:whatsapp"
        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry_id}_main")},
            name="WAHA WhatsApp Server",
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version="1.0",
        )
        
    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            status = await self._client.get_session_status()
            self._attr_native_value = status or "Unknown"
            
            # Set icon based on status
            if status == "WORKING":
                self._attr_icon = "mdi:whatsapp"
            elif status == "DISCONNECTED":
                self._attr_icon = "mdi:cellphone-off"
            else:
                self._attr_icon = "mdi:help-circle"
                
        except Exception as exc:
            _LOGGER.error("Failed to update session status: %s", exc)
            self._attr_native_value = "Unknown"
            self._attr_icon = "mdi:help-circle" 