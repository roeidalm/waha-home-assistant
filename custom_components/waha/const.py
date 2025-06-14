DOMAIN = "waha"
CONF_BASE_URL = "base_url"
CONF_API_KEY = "api_key"
CONF_DEFAULT_RECIPIENTS = "default_recipients"
CONF_SESSION_NAME = "session_name"

# Configuration keys for Home Assistant
ATTR_SENDER = "sender"
ATTR_MESSAGE = "message"
ATTR_TIMESTAMP = "timestamp"
ATTR_SESSION = "session"
ATTR_MESSAGE_ID = "message_id"

# Default values
DEFAULT_SESSION_NAME = "default"

# Service name
SERVICE_NOTIFY = "waha_whatsapp"

# Event name
EVENT_WAHA_MESSAGE_RECEIVED = "waha_message_received"

# Configuration schema (for YAML)
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

WAHA_SCHEMA = vol.Schema({
    vol.Required(CONF_BASE_URL): cv.url,
    vol.Optional(CONF_API_KEY): cv.string,
    vol.Required(CONF_DEFAULT_RECIPIENTS): [cv.string],
    vol.Optional(CONF_SESSION_NAME, default=DEFAULT_SESSION_NAME): cv.string,
}) 