"""Constants for the WAHA WhatsApp integration."""
from typing import Final

DOMAIN: Final = "waha"

# Configuration
CONF_BASE_URL = "base_url"
CONF_API_KEY = "api_key"
CONF_DEFAULT_RECIPIENTS = "default_recipients"
CONF_SESSION_NAME = "session_name"
CONF_RATE_LIMIT = "rate_limit"
CONF_TIMEOUT = "timeout"

# Configuration keys for Home Assistant
ATTR_SENDER = "sender"
ATTR_MESSAGE = "message"
ATTR_TIMESTAMP = "timestamp"
ATTR_SESSION = "session"
ATTR_MESSAGE_ID = "message_id"

# Defaults
DEFAULT_SESSION_NAME = "home-assistant"
DEFAULT_RATE_LIMIT = 10  # messages per minute
DEFAULT_TIMEOUT = 30  # seconds

# Event types
EVENT_MESSAGE_RECEIVED = f"{DOMAIN}_message_received"
EVENT_STATUS_CHANGED = f"{DOMAIN}_status_changed"
EVENT_QR_CHANGED = f"{DOMAIN}_qr_changed"

# Status types
STATUS_AUTHENTICATED = "authenticated"
STATUS_CONNECTING = "connecting"
STATUS_DISCONNECTED = "disconnected"
STATUS_UNKNOWN = "unknown"

# Error messages
ERROR_INVALID_URL = "Invalid URL"
ERROR_INVALID_PHONE = "Invalid phone number format"
ERROR_CONNECTION_FAILED = "Failed to connect to WAHA server"
ERROR_AUTHENTICATION_FAILED = "Authentication failed"
ERROR_RATE_LIMIT = "Rate limit exceeded"
ERROR_TIMEOUT = "Request timed out"
ERROR_INVALID_SESSION = "Invalid session name"
ERROR_WEBHOOK_FAILED = "Failed to register webhook"

# Configuration schema (for YAML)
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

WAHA_SCHEMA = vol.Schema({
    vol.Required(CONF_BASE_URL): cv.url,
    vol.Optional(CONF_API_KEY): cv.string,
    vol.Required(CONF_DEFAULT_RECIPIENTS): [cv.string],
    vol.Optional(CONF_SESSION_NAME, default=DEFAULT_SESSION_NAME): cv.string,
})

# Service name
SERVICE_NOTIFY = "waha_whatsapp" 