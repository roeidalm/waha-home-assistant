"""WhatsApp notification service using WAHA API."""
import logging
from homeassistant.components.notify import (
    ATTR_TARGET,
    PLATFORM_SCHEMA,
    BaseNotificationService,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME
from .const import (
    DOMAIN,
    CONF_DEFAULT_RECIPIENTS,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from .helpers import validate_phone_number

_LOGGER = logging.getLogger(__name__)

async def async_get_service(hass, config, discovery_info=None):
    """Get the WAHA notification service."""
    if discovery_info is None:
        return None
    entry_id = discovery_info["entry_id"]
    client = hass.data[DOMAIN][entry_id]["client"]
    default_recipients = hass.data[DOMAIN][entry_id]["default_recipients"]
    return WahaNotificationService(client, default_recipients)

class WahaNotificationService(BaseNotificationService):
    """Implementation of the WAHA notification service."""
    def __init__(self, client, default_recipients):
        self.client = client
        self.default_recipients = default_recipients

    async def async_send_message(self, message="", **kwargs):
        """Send a WhatsApp message."""
        targets = kwargs.get(ATTR_TARGET, self.default_recipients)
        if not targets:
            _LOGGER.error("No recipients provided and no default recipients configured")
            return
        for target in targets:
            # Validate phone number
            valid_number = validate_phone_number(target)
            if not valid_number:
                _LOGGER.error(f"Invalid phone number format: {target}")
                continue
            _LOGGER.debug("Sending WhatsApp message to %s", valid_number)
            result = await self.client.send_message(valid_number, message)
            if not result:
                _LOGGER.error("Failed to send WhatsApp message to %s", valid_number)

async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the WAHA notification platform from config entry."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    client = entry_data["client"]
    default_recipients = entry_data.get("default_recipients", [])

    discovery_info = {
        "entry_id": config_entry.entry_id,
        CONF_DEFAULT_RECIPIENTS: default_recipients,
    }

    notification_service = await async_get_service(hass, {}, discovery_info)

    if notification_service:
        hass.data.setdefault(DOMAIN, {}).setdefault("services", {})
        service_name = f"{DOMAIN}_{config_entry.entry_id}"
        hass.data[DOMAIN]["services"][service_name] = notification_service
        hass.components.notify.async_register_notification_service(notification_service) 