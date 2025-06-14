"""The WAHA WhatsApp integration."""
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    CONF_BASE_URL,
    CONF_API_KEY,
    CONF_DEFAULT_RECIPIENTS,
    CONF_SESSION_NAME,
    DEFAULT_SESSION_NAME,
)
# from .api_client import WahaApiClient  # To be implemented
# from .webhook import async_setup_webhook  # To be implemented

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_BASE_URL): cv.url,
        vol.Optional(CONF_API_KEY): cv.string,
        vol.Optional(CONF_DEFAULT_RECIPIENTS, default=[]): vol.All(
            cv.ensure_list, [cv.string]
        ),
        vol.Optional(CONF_SESSION_NAME, default=DEFAULT_SESSION_NAME): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)

SERVICE_SCHEMA_SEND_MESSAGE = vol.Schema({
    vol.Required("phone"): cv.string,
    vol.Required("message"): cv.string,
})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WAHA component from YAML configuration."""
    hass.data.setdefault(DOMAIN, {})
    if DOMAIN not in config:
        return True
    # Register services
    async def send_message(call: ServiceCall) -> None:
        """Service to send a WhatsApp message."""
        for entry_id, entry_data in hass.data[DOMAIN].items():
            if "client" in entry_data:
                client = entry_data["client"]
                phone = call.data["phone"]
                message = call.data["message"]
                await client.send_message(phone, message)
                return
        _LOGGER.error("No configured WAHA integration found")
    hass.services.async_register(
        DOMAIN, "send_message", send_message, schema=SERVICE_SCHEMA_SEND_MESSAGE
    )
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WAHA from a config entry."""
    # Get configuration
    base_url = entry.data[CONF_BASE_URL]
    api_key = entry.data.get(CONF_API_KEY)
    session_name = entry.data.get(CONF_SESSION_NAME, DEFAULT_SESSION_NAME)
    # Get default recipients from options or data
    default_recipients = entry.options.get(
        CONF_DEFAULT_RECIPIENTS,
        entry.data.get(CONF_DEFAULT_RECIPIENTS, [])
    )
    # Create API client (placeholder, to be implemented)
    client = None  # WahaApiClient(hass, base_url, api_key, session_name)
    # Test connection (placeholder)
    status = 'unknown'
    # if client is not None:
    #     status = 'connected' if await client.test_connection() else 'disconnected'
    # Store client and status in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "default_recipients": default_recipients,
        "status": status,
    }
    # Set up webhook (placeholder)
    # if not await async_setup_webhook(hass, entry, client):
    #     _LOGGER.warning("Failed to set up webhook, but continuing with setup")
    # Set up notify platform
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "notify")
    )
    return True

def get_connection_status(hass: HomeAssistant, entry_id: str) -> str:
    """Get the connection status for a WAHA integration entry."""
    return hass.data.get(DOMAIN, {}).get(entry_id, {}).get('status', 'unknown')

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload notify platform
    unload_ok = await hass.async_forward_entry_unload(entry, "notify")
    # Remove entry data
    if unload_ok and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry) 