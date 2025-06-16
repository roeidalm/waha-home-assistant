"""WAHA sensors."""
import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .device import WahaDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WAHA sensors from a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    api_client = data["api_client"]
    
    # Create device
    device = WahaDevice(config_entry)
    
    sensors = [
        WAHAStatusSensor(api_client, device, config_entry),
        WAHASessionSensor(api_client, device, config_entry),
    ]
    
    async_add_entities(sensors, True)


class WAHAStatusSensor(SensorEntity):
    """WAHA status sensor."""

    def __init__(self, api_client, device, config_entry):
        """Initialize the sensor."""
        self._api_client = api_client
        self._device = device
        self._config_entry = config_entry
        self._attr_name = "WAHA Status"
        self._attr_unique_id = f"{config_entry.entry_id}_status"
        self._attr_icon = "mdi:whatsapp"
        self._state = "Unknown"

    @property
    def device_info(self):
        """Return device information."""
        return self._device.device_info

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        data = self.hass.data[DOMAIN][self._config_entry.entry_id]
        return {
            "base_url": data.get("base_url"),
            "session_name": data.get("session_name"),
            "phone_numbers": len(data.get("phone_numbers", [])),
            "last_updated": datetime.now().isoformat(),
        }

    async def async_update(self):
        """Update the sensor."""
        try:
            # Try to get session status
            status = await self._api_client.get_session_status()
            if status:
                self._state = "Connected"
            else:
                self._state = "Disconnected"
        except Exception as err:
            _LOGGER.debug("Could not update WAHA status: %s", err)
            self._state = "Error"


class WAHASessionSensor(SensorEntity):
    """WAHA session information sensor."""

    def __init__(self, api_client, device, config_entry):
        """Initialize the sensor."""
        self._api_client = api_client
        self._device = device
        self._config_entry = config_entry
        self._attr_name = "WAHA Session Info"
        self._attr_unique_id = f"{config_entry.entry_id}_session"
        self._attr_icon = "mdi:information"
        self._state = "Unknown"

    @property
    def device_info(self):
        """Return device information."""
        return self._device.device_info

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        data = self.hass.data[DOMAIN][self._config_entry.entry_id]
        return {
            "session_name": data.get("session_name"),
            "configured_phones": data.get("phone_numbers", []),
            "api_configured": bool(data.get("api_key")),
        }

    async def async_update(self):
        """Update the sensor."""
        data = self.hass.data[DOMAIN][self._config_entry.entry_id]
        session_name = data.get("session_name", "default")
        self._state = f"Session: {session_name}" 