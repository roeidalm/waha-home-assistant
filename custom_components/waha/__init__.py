"""The WAHA WhatsApp integration."""
import logging
import voluptuous as vol
from typing import Any, Dict, List, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_URL,
    CONF_API_KEY,
    CONF_NAME,
    Platform,
)
from homeassistant.core import HomeAssistant, ServiceCall, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError

from .api_client import WahaApiClient, WahaApiError, WahaConnectionError
from .const import (
    DOMAIN,
    CONF_BASE_URL,
    CONF_API_KEY,
    CONF_DEFAULT_RECIPIENTS,
    CONF_SESSION_NAME,
    DEFAULT_SESSION_NAME,
    CONF_RATE_LIMIT,
    DEFAULT_RATE_LIMIT,
    CONF_TIMEOUT,
    DEFAULT_TIMEOUT,
)
from .webhook import async_setup_webhook

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.NOTIFY]

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_BASE_URL): cv.url,
        vol.Optional(CONF_API_KEY): cv.string,
        vol.Optional(CONF_DEFAULT_RECIPIENTS, default=[]): vol.All(
            cv.ensure_list, [cv.string]
        ),
        vol.Optional(CONF_SESSION_NAME, default=DEFAULT_SESSION_NAME): cv.string,
        vol.Optional(CONF_RATE_LIMIT, default=DEFAULT_RATE_LIMIT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=60)
        ),
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.All(
            vol.Coerce(int), vol.Range(min=5, max=300)
        ),
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
        phone = call.data["phone"]
        message = call.data["message"]
        
        for entry_id, entry_data in hass.data[DOMAIN].items():
            if "client" in entry_data:
                client: WahaApiClient = entry_data["client"]
                try:
                    if await client.send_message(phone, message):
                        _LOGGER.debug("Message sent successfully to %s", phone)
                        return
                    _LOGGER.error("Failed to send message to %s", phone)
                except WahaApiError as exc:
                    _LOGGER.error("Error sending message to %s: %s", phone, exc)
                return
        
        _LOGGER.error("No configured WAHA integration found")

    hass.services.async_register(
        DOMAIN, "send_message", send_message, schema=SERVICE_SCHEMA_SEND_MESSAGE
    )
    
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WAHA from a config entry."""
    try:
        # Get configuration
        base_url = entry.data[CONF_BASE_URL]
        api_key = entry.data.get(CONF_API_KEY)
        session_name = entry.data.get(CONF_SESSION_NAME, DEFAULT_SESSION_NAME)
        rate_limit = entry.data.get(CONF_RATE_LIMIT, DEFAULT_RATE_LIMIT)
        timeout = entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        
        # Get default recipients from options or data
        default_recipients = entry.options.get(
            CONF_DEFAULT_RECIPIENTS,
            entry.data.get(CONF_DEFAULT_RECIPIENTS, [])
        )

        # Create API client
        client = WahaApiClient(
            hass=hass,
            base_url=base_url,
            api_key=api_key,
            session_name=session_name,
            rate_limit=rate_limit,
            timeout=timeout
        )

        # Test connection
        if not await client.test_connection():
            raise ConfigEntryNotReady(
                f"Failed to connect to WAHA server at {base_url}"
            )

        # Get session status
        session_status = await client.get_session_status()
        if session_status is None:
            _LOGGER.warning("Could not get WhatsApp session status")
        elif session_status != "authenticated":
            _LOGGER.warning(
                "WhatsApp session is not authenticated. Status: %s", 
                session_status
            )

        # Store client and configuration in hass.data
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "client": client,
            "default_recipients": default_recipients,
            "status": session_status or "unknown",
        }

        # Set up webhook
        if not await async_setup_webhook(hass, entry, client):
            _LOGGER.warning(
                "Failed to set up webhook, but continuing with setup"
            )

        # Set up notify platform
        await hass.config_entries.async_forward_entry_setup(entry, "notify")

        # Register update listener for config entry changes
        entry.async_on_unload(entry.add_update_listener(async_reload_entry))

        return True

    except WahaConnectionError as exc:
        raise ConfigEntryNotReady(
            f"Connection error while setting up WAHA: {exc}"
        ) from exc
    except WahaApiError as exc:
        raise ConfigEntryNotReady(
            f"API error while setting up WAHA: {exc}"
        ) from exc
    except Exception as exc:
        _LOGGER.exception("Unexpected error setting up WAHA")
        raise ConfigEntryNotReady(
            f"Unexpected error setting up WAHA: {exc}"
        ) from exc

def get_connection_status(hass: HomeAssistant, entry_id: str) -> str:
    """Get the connection status for a WAHA integration entry."""
    return hass.data.get(DOMAIN, {}).get(entry_id, {}).get('status', 'unknown')

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        # Unload notify platform
        unload_ok = await hass.config_entries.async_forward_entry_unload(
            entry, "notify"
        )

        # Close API client
        if unload_ok and entry.entry_id in hass.data[DOMAIN]:
            entry_data = hass.data[DOMAIN][entry.entry_id]
            if "client" in entry_data:
                client: WahaApiClient = entry_data["client"]
                await client.close()
            hass.data[DOMAIN].pop(entry.entry_id)

        return unload_ok

    except Exception as exc:
        _LOGGER.exception("Error unloading WAHA entry")
        return False

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry) 