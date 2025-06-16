"""The WAHA WhatsApp integration."""
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import Platform

from .const import (
    DOMAIN,
    CONF_BASE_URL,
    CONF_API_KEY,
    CONF_PHONE_NUMBERS,
    CONF_SESSION_NAME,
    DEFAULT_SESSION_NAME,
)
from .api_client import WahaApiClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

# Service schemas
SEND_MESSAGE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("phone_number"): cv.string,
        vol.Required("message"): cv.template,
    },
    extra=vol.ALLOW_EXTRA,
)

SERVICE_SCHEMAS = {
    "send_message": SEND_MESSAGE_SERVICE_SCHEMA,
}

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WAHA integration."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WAHA from a config entry."""
    _LOGGER.info("Setting up WAHA integration")
    
    # Initialize API client
    api_client = WahaApiClient(
        hass=hass,
        base_url=entry.data[CONF_BASE_URL],
        api_key=entry.data.get(CONF_API_KEY),
        session_name=entry.data.get(CONF_SESSION_NAME, DEFAULT_SESSION_NAME),
    )
    
    # Store entry data and API client
    hass.data[DOMAIN][entry.entry_id] = {
        "entry": entry,
        "api_client": api_client,
        "base_url": entry.data[CONF_BASE_URL],
        "api_key": entry.data.get(CONF_API_KEY),
        "session_name": entry.data.get(CONF_SESSION_NAME, DEFAULT_SESSION_NAME),
        "phone_numbers": entry.data.get(CONF_PHONE_NUMBERS, []),
    }

    # Register services
    async def handle_send_message(call: ServiceCall) -> None:
        """Handle the send_message service call."""
        phone_number = call.data.get("phone_number")
        message = call.data.get("message")
        
        if not phone_number or not message:
            raise HomeAssistantError("Both phone_number and message are required")
        
        # Render template if needed
        if hasattr(message, 'async_render'):
            message = message.async_render()
        
        _LOGGER.info("WAHA: Sending message to %s: %s", phone_number, message)
        
        try:
            result = await api_client.send_message(phone_number, str(message))
            _LOGGER.info("WAHA: Message sent successfully: %s", result)
        except Exception as err:
            _LOGGER.error("WAHA: Failed to send message: %s", err)
            raise HomeAssistantError(f"Failed to send message: {err}") from err
    
    # Register service
    if not hass.services.has_service(DOMAIN, "send_message"):
        hass.services.async_register(
            DOMAIN,
            "send_message",
            handle_send_message,
            schema=SEND_MESSAGE_SERVICE_SCHEMA,
        )
        _LOGGER.info("WAHA: Service registered: waha.send_message")
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("WAHA integration setup completed")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading WAHA integration")
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Remove from hass.data
        hass.data[DOMAIN].pop(entry.entry_id, None)
        
        # Remove service if this was the last entry
        if not hass.data[DOMAIN]:
            if hass.services.has_service(DOMAIN, "send_message"):
                hass.services.async_remove(DOMAIN, "send_message")
                _LOGGER.info("WAHA: Removed send_message service")

    return unload_ok 