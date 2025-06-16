"""The WAHA WhatsApp integration."""
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.const import Platform

from .const import (
    DOMAIN,
    CONF_BASE_URL,
    CONF_API_KEY,
    CONF_PHONE_NUMBERS,
    CONF_SESSION_NAME,
    DEFAULT_SESSION_NAME,
)

_LOGGER = logging.getLogger(__name__)

# Service schema with proper field descriptions for Developer Tools UI
SERVICE_SCHEMA_SEND_MESSAGE = vol.Schema({
    vol.Required("phone_number", description="Phone number in international format (e.g., +1234567890)"): cv.string,
    vol.Required("message", description="Message text to send"): cv.template,
})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WAHA integration."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info("WAHA integration async_setup completed")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WAHA from a config entry."""
    _LOGGER.info("Setting up WAHA integration entry")
    
    # Store the entry data
    hass.data[DOMAIN][entry.entry_id] = {
        "entry": entry,
        "base_url": entry.data[CONF_BASE_URL],
        "api_key": entry.data.get(CONF_API_KEY),
        "session_name": entry.data.get(CONF_SESSION_NAME, DEFAULT_SESSION_NAME),
    }

    # Register services
    await _async_register_services(hass, entry)
    
    # Set up notification services
    await _async_setup_notification_services(hass, entry)
    
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
        # For now, just log the message - you can add actual sending logic here later
        
    # Register service only if not already registered
    if not hass.services.has_service(DOMAIN, "send_message"):
        hass.services.async_register(
            DOMAIN, "send_message", send_message, schema=SERVICE_SCHEMA_SEND_MESSAGE
        )
        _LOGGER.info("Registered service: %s.send_message", DOMAIN)

async def _async_setup_notification_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up notification services."""
    phone_numbers = entry.data.get(CONF_PHONE_NUMBERS, [])
    
    _LOGGER.info("Setting up notification services for %d phone numbers", len(phone_numbers))
    
    # Set up individual notification services for each phone number
    for phone_number in phone_numbers:
        # Create a clean service name from phone number
        # +972547773040 -> waha_972547773040
        clean_number = phone_number.replace("+", "").replace("-", "").replace(" ", "")
        service_name = f"waha_{clean_number}"
        
        try:
            await async_load_platform(
                hass,
                Platform.NOTIFY,
                DOMAIN,
                {
                    "entry_id": entry.entry_id,
                    "name": service_name,
                    "phone_number": phone_number,
                },
                {},
            )
            _LOGGER.info("Registered notification service: notify.%s for %s", service_name, phone_number)
        except Exception as err:
            _LOGGER.error("Failed to register notification service for %s: %s", phone_number, err)
    
    # Also set up a general notification service
    try:
        await async_load_platform(
            hass,
            Platform.NOTIFY,
            DOMAIN,
            {
                "entry_id": entry.entry_id,
                "name": "waha_general",
            },
            {},
        )
        _LOGGER.info("Registered general notification service: notify.waha_general")
    except Exception as err:
        _LOGGER.error("Failed to register general notification service: %s", err) 