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

# Defaults
DEFAULT_SESSION_NAME = "home-assistant"
DEFAULT_RATE_LIMIT = 10  # messages per minute
DEFAULT_TIMEOUT = 30  # seconds

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
PLATFORMS = ["notify"] 