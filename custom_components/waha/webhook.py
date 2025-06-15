import logging
from homeassistant.components.webhook import (
    async_register as async_register_webhook,
    async_unregister as async_unregister_webhook,
    async_generate_url
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN, EVENT_WAHA_MESSAGE_RECEIVED
from aiohttp import web

_LOGGER = logging.getLogger(__name__)

WEBHOOK_ID_TEMPLATE = "waha_{entry_id}_webhook"

def is_valid_webhook_request(hass: HomeAssistant, webhook_id: str, request: web.Request) -> bool:
    # Basic validation: check if the config entry exists for this webhook
    if not webhook_id.startswith("waha_"):
        return False
    config_entry_id = webhook_id.replace("waha_", "").replace("_webhook", "")
    if config_entry_id not in hass.data.get(DOMAIN, {}):
        return False
    # Additional security checks can be added here
    return True

async def async_setup_webhook(hass: HomeAssistant, entry: ConfigEntry, client) -> bool:
    """Set up the webhook endpoint for incoming WhatsApp messages."""
    webhook_id = WEBHOOK_ID_TEMPLATE.format(entry_id=entry.entry_id)
    url = async_generate_url(hass, webhook_id)

    async def handle_webhook(hass, webhook_id, request):
        # Security validation
        if not is_valid_webhook_request(hass, webhook_id, request):
            _LOGGER.warning(f"Rejected unauthorized webhook request from {getattr(request, 'remote', 'unknown')}")
            return web.Response(status=403)
        try:
            data = await request.json()
        except Exception as exc:
            _LOGGER.error("Failed to parse webhook payload: %s", exc)
            return web.Response(status=400)
        # Validate required fields
        if not all(key in data for key in ["sender", "body"]):
            _LOGGER.warning("Received webhook data missing required fields")
            return web.Response(status=400)
        # Parse message data
        event_data = {
            "sender": data.get("sender"),
            "message": data.get("body"),
            "timestamp": data.get("timestamp"),
            "session": data.get("session"),
            "message_id": data.get("id"),
        }
        _LOGGER.debug("Received WhatsApp webhook: %s", event_data)
        hass.bus.async_fire(EVENT_WAHA_MESSAGE_RECEIVED, event_data)
        return web.Response(status=200)

    async_register_webhook(hass, DOMAIN, "WAHA WhatsApp Webhook", webhook_id, handle_webhook)
    _LOGGER.info("Registered WAHA webhook at %s", url)

    # Register webhook with WAHA API
    if hasattr(client, "register_webhook"):
        await client.register_webhook(url)
    return True

async def async_remove_webhook(hass: HomeAssistant, entry: ConfigEntry) -> None:
    webhook_id = WEBHOOK_ID_TEMPLATE.format(entry_id=entry.entry_id)
    async_unregister_webhook(hass, webhook_id)
    _LOGGER.info("Unregistered WAHA webhook for entry %s", entry.entry_id)