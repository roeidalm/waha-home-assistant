"""Device entities for WAHA WhatsApp integration."""
import logging
from typing import Any, Dict, Optional

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
)

_LOGGER = logging.getLogger(__name__)

class WahaPhoneDevice:
    """Represents a WhatsApp phone number device."""
    
    def __init__(self, phone_number: str, name: Optional[str] = None):
        """Initialize the phone device."""
        self.phone_number = phone_number
        self.name = name or f"WhatsApp {phone_number}"
        self._id = phone_number.replace("+", "").replace("@c.us", "")
        
    @property
    def device_id(self) -> str:
        """Return the device ID."""
        return self._id
        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._id)},
            name=self.name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version="1.0",
        ) 