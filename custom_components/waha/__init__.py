"""The WAHA WhatsApp integration."""
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Service schema with field descriptions for Developer Tools UI
SERVICE_SCHEMA_SEND_MESSAGE = vol.Schema({
    vol.Required("phone_number", description="Phone number in international format (e.g., +972547773040)"): cv.string,
    vol.Required("message", description="Message text to send"): cv.template,
})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WAHA integration."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WAHA from a config entry."""
    _LOGGER.info("Setting up WAHA integration")
    
    # Store entry data
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Register the send_message service
    async def send_message(call: ServiceCall) -> None:
        """Service to send a WhatsApp message."""
        phone_number = call.data["phone_number"]
        message = call.data["message"]
        
        _LOGGER.info("WAHA: Sending message to %s: %s", phone_number, message)
        # TODO: Add actual message sending logic here
        
    # Register service
    if not hass.services.has_service(DOMAIN, "send_message"):
        hass.services.async_register(
            DOMAIN, 
            "send_message", 
            send_message, 
            schema=SERVICE_SCHEMA_SEND_MESSAGE
        )
        _LOGGER.info("WAHA: Registered send_message service")
    
    _LOGGER.info("WAHA integration setup completed")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading WAHA integration")
    
    # Remove from hass.data
    hass.data[DOMAIN].pop(entry.entry_id, None)
    
    # Remove service if this was the last entry
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, "send_message")
        _LOGGER.info("WAHA: Removed send_message service")

    return True 