"""The WAHA WhatsApp integration."""
import logging
import voluptuous as vol
from typing import Any, Dict, List, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant, ServiceCall
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
    SERVICE_SEND_MESSAGE,
)
from .helpers import validate_phone_number

_LOGGER = logging.getLogger(__name__)

# Platforms to set up
PLATFORMS: list[Platform] = []

# Service schemas with descriptions for Developer Tools
SERVICE_SEND_MESSAGE_SCHEMA = vol.Schema({
    vol.Required("phone_number", description="Phone number in international format (e.g., +1234567890)"): cv.string,
    vol.Required("message", description="Message text to send"): cv.template,
})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WAHA component from YAML configuration."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WAHA from a config entry."""
    try:
        # Get configuration
        base_url = entry.data[CONF_BASE_URL]
        api_key = entry.data.get(CONF_API_KEY)
        session_name = entry.data.get(CONF_SESSION_NAME, DEFAULT_SESSION_NAME)
        
        # Get phone numbers from config entry  
        phone_numbers = entry.data.get(CONF_PHONE_NUMBERS, [])

        # Create API client
        client = WahaApiClient(
            hass=hass,
            base_url=base_url,
            api_key=api_key,
            session_name=session_name,
        )

        # Test connection
        if not await client.test_connection():
            raise ConfigEntryNotReady(f"Failed to connect to WAHA server at {base_url}")

        # Store client and configuration in hass.data
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "client": client,
            "phone_numbers": phone_numbers,
        }

        # Register services
        await _register_services(hass, entry)

        return True

    except Exception as exc:
        _LOGGER.exception("Error setting up WAHA")
        raise ConfigEntryNotReady(f"Error setting up WAHA: {exc}") from exc

async def _register_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register WAHA services."""
    
    async def send_message_service(call: ServiceCall) -> None:
        """Service to send a WhatsApp message."""
        phone_number = call.data["phone_number"]
        message = call.data["message"]
        
        # Render template if needed
        if hasattr(message, 'async_render'):
            message = message.async_render()
        
        # Validate phone number
        valid_phone = validate_phone_number(phone_number)
        if not valid_phone:
            raise HomeAssistantError(f"Invalid phone number format: {phone_number}")
            
        # Get the client
        entry_data = hass.data[DOMAIN].get(entry.entry_id)
        if not entry_data:
            raise HomeAssistantError("WAHA integration not found")
            
        client: WahaApiClient = entry_data["client"]
        
        try:
            # Format chat ID for WAHA (ensure @c.us suffix)
            chat_id = valid_phone
            if not chat_id.endswith("@c.us"):
                clean_number = valid_phone.lstrip('+')
                chat_id = f"{clean_number}@c.us"
                
            success = await client.send_message(chat_id, message)
            if success:
                _LOGGER.info("Message sent successfully to %s", phone_number)
            else:
                raise HomeAssistantError(f"Failed to send message to {phone_number}")
                
        except WahaApiError as exc:
            raise HomeAssistantError(f"Error sending message to {phone_number}: {exc}")

    # Register the main send message service
    if not hass.services.has_service(DOMAIN, SERVICE_SEND_MESSAGE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_MESSAGE,
            send_message_service,
            schema=SERVICE_SEND_MESSAGE_SCHEMA,
        )
        _LOGGER.info("Registered service: %s.%s", DOMAIN, SERVICE_SEND_MESSAGE)

    # Register individual notification services for each phone number
    await _register_phone_notification_services(hass, entry)

async def _register_phone_notification_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register individual notification services for each phone number."""
    phone_numbers = entry.data.get(CONF_PHONE_NUMBERS, [])
    
    for phone_number in phone_numbers:
        # Create service name from phone number
        # +972547773040 -> waha_972547773040  
        clean_number = phone_number.replace("+", "").replace("-", "").replace(" ", "")
        service_name = f"waha_{clean_number}"
        
        # Skip if service already exists
        if hass.services.has_service("notify", service_name):
            continue
            
        async def create_notification_service(phone: str):
            """Create a notification service for a specific phone number."""
            async def notify_phone(call: ServiceCall) -> None:
                """Send notification to specific phone."""
                message = call.data.get("message", "")
                
                # Render template if needed
                if hasattr(message, 'async_render'):
                    message = message.async_render()
                
                # Use the main send_message service
                await send_message_service(ServiceCall(DOMAIN, SERVICE_SEND_MESSAGE, {
                    "phone_number": phone,
                    "message": message
                }))
            return notify_phone
        
        # Register the notification service
        notification_handler = await create_notification_service(phone_number)
        hass.services.async_register(
            "notify",
            service_name,
            notification_handler,
            schema=vol.Schema({
                vol.Required("message", description="Message to send"): cv.template,
            })
        )
        
        _LOGGER.info("Registered notification service: notify.%s for phone %s", service_name, phone_number)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Remove from hass.data
    hass.data[DOMAIN].pop(entry.entry_id, None)
    
    # Remove services if this was the last entry
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, SERVICE_SEND_MESSAGE)
        
        # Remove phone notification services
        phone_numbers = entry.data.get(CONF_PHONE_NUMBERS, [])
        for phone_number in phone_numbers:
            clean_number = phone_number.replace("+", "").replace("-", "").replace(" ", "")
            service_name = f"waha_{clean_number}"
            if hass.services.has_service("notify", service_name):
                hass.services.async_remove("notify", service_name)
    
    return True

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry) 