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
CONF_ADMIN_ONLY = "admin_only"
CONF_ALLOW_UNKNOWN = "allow_unknown"
CONF_CONVERSATION_ID = "conversation_id"
CONF_PHONE_ID = "phone_id"
CONF_PHONE_STORE = "phone_store"
CONF_PROXY_MODE = "proxy_mode"
CONF_RECEIVE_PRESENCE = "receive_presence"
CONF_RECEIVE_MESSAGES = "receive_messages"
CONF_URL = "url"
CONF_USER_ID = "user_id"

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
DEFAULT_ADMIN_ONLY = True
DEFAULT_ALLOW_UNKNOWN = False
DEFAULT_PROXY_MODE = False
DEFAULT_RECEIVE_PRESENCE = False
DEFAULT_RECEIVE_MESSAGES = True

# Event types
EVENT_WAHA_MESSAGE_RECEIVED = "waha_message_received"
EVENT_MESSAGE_RECEIVED = EVENT_WAHA_MESSAGE_RECEIVED
EVENT_STATUS_CHANGED = f"{DOMAIN}_status_changed"
EVENT_QR_CHANGED = f"{DOMAIN}_qr_changed"
EVENT_PRESENCE_CHANGED = "presence_changed"
EVENT_STATE_CHANGED = "state_changed"

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

# Platforms
PLATFORMS = ["notify", "sensor"] 