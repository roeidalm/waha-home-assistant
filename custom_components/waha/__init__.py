"""The WAHA WhatsApp integration."""
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    CONF_BASE_URL,
    CONF_API_KEY,
    CONF_SESSION_NAME,
    DEFAULT_SESSION_NAME,
)

_LOGGER = logging.getLogger(__name__)

# Service schema
SERVICE_SCHEMA_SEND_MESSAGE = vol.Schema({
    vol.Required("phone_number"): cv.string,
    vol.Required("message"): cv.template,
})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WAHA integration."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info("WAHA integration async_setup completed")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WAHA from a config entry."""
    _LOGGER.info("Setting up WAHA integration entry")
    
    # Just store the entry data without testing connection
    hass.data[DOMAIN][entry.entry_id] = {
        "entry": entry,
        "base_url": entry.data[CONF_BASE_URL],
        "api_key": entry.data.get(CONF_API_KEY),
        "session_name": entry.data.get(CONF_SESSION_NAME, DEFAULT_SESSION_NAME),
    }

    # Register a simple service
    await _async_register_services(hass, entry)
    
    _LOGGER.info("WAHA integration setup completed successfully")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading WAHA integration")
    
    # Remove from hass.data
    hass.data[DOMAIN].pop(entry.entry_id, None)
    
    # Unregister services if this was the last entry
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, "send_message")

    return True

async def _async_register_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register WAHA services."""
    
    async def send_message(call: ServiceCall) -> None:
        """Service to send a WhatsApp message to any phone number."""
        phone_number = call.data["phone_number"]
        message = call.data["message"]
        
        _LOGGER.info("WAHA send_message called for %s: %s", phone_number, message)
        # For now, just log the message instead of actually sending it
        
    # Register service only if not already registered
    if not hass.services.has_service(DOMAIN, "send_message"):
        hass.services.async_register(
            DOMAIN, "send_message", send_message, schema=SERVICE_SCHEMA_SEND_MESSAGE
        )
        _LOGGER.info("Registered service: %s.send_message", DOMAIN) 