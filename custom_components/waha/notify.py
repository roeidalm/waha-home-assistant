"""WhatsApp notification service using WAHA API."""
import logging
from homeassistant.components.notify import (
    ATTR_TARGET,
    BaseNotificationService,
)
from homeassistant.const import CONF_NAME
from .const import (
    DOMAIN,
    CONF_DEFAULT_RECIPIENTS,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .helpers import validate_phone_number

_LOGGER = logging.getLogger(__name__)

async def async_get_service(hass: HomeAssistant, config: dict, discovery_info: dict = None):
    """Get the WAHA notification service."""
    if discovery_info is None:
        return None
    
    entry_id = discovery_info["entry_id"]
    if DOMAIN not in hass.data or entry_id not in hass.data[DOMAIN]:
        _LOGGER.error("WAHA integration data not found for entry %s", entry_id)
        return None
        
    client = hass.data[DOMAIN][entry_id]["client"]
    default_recipients = hass.data[DOMAIN][entry_id].get("default_recipients", [])
    
    return WahaNotificationService(hass, client, default_recipients, entry_id)

class WahaNotificationService(BaseNotificationService):
    """Implementation of the WAHA notification service."""
    
    def __init__(self, hass: HomeAssistant, client, default_recipients: list, entry_id: str):
        """Initialize the WAHA notification service."""
        self.hass = hass
        self.client = client
        self.default_recipients = default_recipients
        self.entry_id = entry_id
        self._name = f"WAHA WhatsApp ({entry_id[:8]})"

    @property
    def name(self):
        """Return the name of the notification service."""
        return self._name

    async def async_send_message(self, message="", **kwargs):
        """Send a WhatsApp message."""
        # Get targets from the notification call or use defaults
        targets = kwargs.get(ATTR_TARGET)
        
        # If no targets specified, use default recipients
        if not targets:
            targets = self.default_recipients
            
        # If still no targets, log error
        if not targets:
            _LOGGER.error("No recipients provided and no default recipients configured for WAHA notification service")
            return False
            
        # Ensure targets is a list
        if isinstance(targets, str):
            targets = [targets]
            
        success = True
        for target in targets:
            # Validate and format phone number
            valid_number = validate_phone_number(target)
            if not valid_number:
                _LOGGER.error("Invalid phone number format: %s", target)
                success = False
                continue
                
            _LOGGER.debug("Sending WhatsApp message to %s via WAHA", valid_number)
            
            # Format the phone number for WAHA API (needs @c.us suffix)
            chat_id = valid_number
            if not chat_id.endswith("@c.us"):
                # Remove + and add @c.us for WhatsApp chat ID format
                clean_number = valid_number.lstrip('+')
                chat_id = f"{clean_number}@c.us"
            
            result = await self.client.send_message(chat_id, message)
            if not result:
                _LOGGER.error("Failed to send WhatsApp message to %s", valid_number)
                success = False
            else:
                _LOGGER.info("Successfully sent WhatsApp message to %s", valid_number)
                
        return success

async def async_setup_entry(
    hass: HomeAssistant, 
    config_entry: ConfigEntry, 
    async_add_entities = None
) -> None:
    """Set up the WAHA notification platform from config entry."""
    # This function is called by Home Assistant's notify component
    # We need to register our notification service
    
    entry_data = hass.data.get(DOMAIN, {}).get(config_entry.entry_id)
    if not entry_data:
        _LOGGER.error("WAHA integration data not found for config entry %s", config_entry.entry_id)
        return False
        
    client = entry_data["client"]
    default_recipients = entry_data.get("default_recipients", [])

    # Create the notification service
    service = WahaNotificationService(hass, client, default_recipients, config_entry.entry_id)
    
    # Register the notification service with Home Assistant
    # This creates a service like notify.waha_whatsapp_12345678
    service_name = f"waha_whatsapp_{config_entry.entry_id[:8]}"
    
    hass.services.async_register(
        "notify",
        service_name,
        service.async_send_message,
        schema=None,
    )
    
    _LOGGER.info("Registered WAHA notification service: notify.%s", service_name)
    return True 