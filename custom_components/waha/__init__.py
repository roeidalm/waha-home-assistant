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
    CONF_PHONE_NUMBERS,
    CONF_SESSION_NAME,
    DEFAULT_SESSION_NAME,
    CONF_RATE_LIMIT,
    DEFAULT_RATE_LIMIT,
    CONF_TIMEOUT,
    DEFAULT_TIMEOUT,
    SERVICE_SEND_MESSAGE,
    PLATFORMS,
)
from .helpers import validate_phone_number

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_BASE_URL): cv.url,
        vol.Optional(CONF_API_KEY): cv.string,
        vol.Optional(CONF_PHONE_NUMBERS, default=[]): vol.All(
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

# Service schemas
SERVICE_SCHEMA_SEND_MESSAGE = vol.Schema({
    vol.Required("phone_number"): cv.string,
    vol.Required("message"): cv.string,
})

SERVICE_SCHEMA_SEND_MESSAGE_TO_CONTACT = vol.Schema({
    vol.Required("entity_id"): cv.string,
    vol.Required("message"): cv.string,
})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WAHA component from YAML configuration."""
    hass.data.setdefault(DOMAIN, {})
    
    if DOMAIN not in config:
        return True

    # YAML configuration is deprecated in favor of config entries
    _LOGGER.warning(
        "Configuration of WAHA integration via YAML is deprecated. "
        "Please use the UI configuration instead."
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
        
        # Get phone numbers from config entry
        phone_numbers = entry.data.get(CONF_PHONE_NUMBERS, [])

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
        elif session_status != "WORKING":
            _LOGGER.warning(
                "WhatsApp session is not authenticated. Status: %s", 
                session_status
            )

        # Store client and configuration in hass.data
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "client": client,
            "phone_numbers": phone_numbers,
            "status": session_status or "unknown",
        }

        # Set up platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Register services
        await _async_register_services(hass, entry)

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

async def _async_register_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register WAHA services."""
    
    async def send_message(call: ServiceCall) -> None:
        """Service to send a WhatsApp message to any phone number."""
        phone_number = call.data["phone_number"]
        message = call.data["message"]
        
        # Validate phone number
        valid_phone = validate_phone_number(phone_number)
        if not valid_phone:
            _LOGGER.error("Invalid phone number format: %s", phone_number)
            return
            
        # Get the client for this integration entry
        entry_data = hass.data[DOMAIN].get(entry.entry_id)
        if not entry_data:
            _LOGGER.error("WAHA integration not found")
            return
            
        client: WahaApiClient = entry_data["client"]
        
        try:
            # Format chat ID for WAHA
            chat_id = valid_phone
            if not chat_id.endswith("@c.us"):
                clean_number = valid_phone.lstrip('+')
                chat_id = f"{clean_number}@c.us"
                
            success = await client.send_message(chat_id, message)
            if success:
                _LOGGER.info("Message sent successfully to %s", phone_number)
            else:
                _LOGGER.error("Failed to send message to %s", phone_number)
        except WahaApiError as exc:
            _LOGGER.error("Error sending message to %s: %s", phone_number, exc)

    async def send_message_to_contact(call: ServiceCall) -> None:
        """Service to send a WhatsApp message to a configured contact."""
        entity_id = call.data["entity_id"]
        message = call.data["message"]
        
        # Extract phone number from entity_id
        # Entity ID format: button.waha_send_message_to_1234567890
        try:
            # Get the device ID from the entity
            entity_registry = hass.helpers.entity_registry.async_get(hass)
            entity_entry = entity_registry.async_get(entity_id)
            
            if not entity_entry:
                _LOGGER.error("Entity not found: %s", entity_id)
                return
                
            # Get the device
            device_registry = hass.helpers.device_registry.async_get(hass)
            device = device_registry.async_get(entity_entry.device_id)
            
            if not device:
                _LOGGER.error("Device not found for entity: %s", entity_id)
                return
                
            # Extract phone number from device identifiers
            phone_number = None
            for identifier in device.identifiers:
                if identifier[0] == DOMAIN:
                    # The device ID is the phone number without + and @c.us
                    device_id = identifier[1]
                    # Convert back to phone number format
                    phone_number = f"+{device_id}"
                    break
                    
            if not phone_number:
                _LOGGER.error("Could not extract phone number from device")
                return
                
            # Send the message
            await send_message(ServiceCall(DOMAIN, SERVICE_SEND_MESSAGE, {
                "phone_number": phone_number,
                "message": message
            }))
            
        except Exception as exc:
            _LOGGER.error("Error processing entity %s: %s", entity_id, exc)

    # Register services only once per integration
    service_name = f"{SERVICE_SEND_MESSAGE}_{entry.entry_id}"
    
    if not hass.services.has_service(DOMAIN, SERVICE_SEND_MESSAGE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_MESSAGE,
            send_message,
            schema=SERVICE_SCHEMA_SEND_MESSAGE,
        )
        _LOGGER.info("Registered WAHA service: %s.%s", DOMAIN, SERVICE_SEND_MESSAGE)

    contact_service_name = f"send_message_to_contact"
    if not hass.services.has_service(DOMAIN, contact_service_name):
        hass.services.async_register(
            DOMAIN,
            contact_service_name,
            send_message_to_contact,
            schema=SERVICE_SCHEMA_SEND_MESSAGE_TO_CONTACT,
        )
        _LOGGER.info("Registered WAHA service: %s.%s", DOMAIN, contact_service_name)

def get_connection_status(hass: HomeAssistant, entry_id: str) -> str:
    """Get the connection status for a WAHA integration entry."""
    return hass.data.get(DOMAIN, {}).get(entry_id, {}).get('status', 'unknown')

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        # Unload platforms
        unload_ok = await hass.config_entries.async_forward_entry_unloads(
            entry, PLATFORMS
        )

        # Close API client and remove data
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