"""Config flow for WAHA WhatsApp integration."""
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
import traceback
import aiohttp

from .const import (
    DOMAIN,
    CONF_BASE_URL,
    CONF_API_KEY,
    CONF_DEFAULT_RECIPIENTS,
    CONF_SESSION_NAME,
    DEFAULT_SESSION_NAME,
)

_LOGGER = logging.getLogger(__name__)

def validate_url(url: str) -> str:
    """Validate URL format."""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise vol.Invalid("Invalid URL format")
    return url.rstrip("/")

def validate_recipients(recipients: str) -> str:
    """Validate recipient phone numbers."""
    # Split and clean the recipients
    numbers = [num.strip() for num in recipients.split(",") if num.strip()]
    if not numbers:
        raise vol.Invalid("At least one recipient is required")
    # Basic format validation for each number
    for num in numbers:
        if not num.replace("+", "").isdigit():
            raise vol.Invalid(f"Invalid phone number format: {num}")
    return ",".join(numbers)

class WahaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WAHA WhatsApp."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._errors: Dict[str, str] = {}

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle a flow initiated by the user."""
        self._errors = {}

        if user_input is not None:
            try:
                # Validate URL and recipients format
                user_input[CONF_BASE_URL] = validate_url(user_input[CONF_BASE_URL])
                user_input[CONF_DEFAULT_RECIPIENTS] = validate_recipients(
                    user_input[CONF_DEFAULT_RECIPIENTS]
                )

                # Test connection
                if await self._test_connection(user_input):
                    return self.async_create_entry(
                        title=f"WAHA WhatsApp ({user_input[CONF_SESSION_NAME]})",
                        data=user_input,
                    )
                self._errors["base"] = "cannot_connect"
            except vol.Invalid as err:
                _LOGGER.error("Validation error: %s", err)
                self._errors["base"] = "invalid_format"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error("Unexpected error: %s", err)
                self._errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_BASE_URL): str,
                vol.Optional(CONF_API_KEY): str,
                vol.Required(CONF_DEFAULT_RECIPIENTS): str,
                vol.Optional(CONF_SESSION_NAME, default=DEFAULT_SESSION_NAME): str,
            }),
            errors=self._errors,
        )

    async def _test_connection(self, data: Dict[str, Any]) -> bool:
        """Test connection to WAHA instance."""
        url = f"{data[CONF_BASE_URL]}/api/server/status"
        headers = {"accept": "application/json"}
        
        if api_key := data.get(CONF_API_KEY):
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        return True
                    _LOGGER.error(
                        "WAHA server returned status %s: %s",
                        resp.status,
                        await resp.text(),
                    )
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to connect to WAHA server: %s", err)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Unexpected error testing WAHA connection: %s", err)
        return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "WahaOptionsFlowHandler":
        """Get the options flow for this handler."""
        return WahaOptionsFlowHandler(config_entry)

    @staticmethod
    @callback
    def async_get_suggested_values():
        return {CONF_API_KEY: {"sensitive": True}}

class WahaOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle WAHA options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._errors: Dict[str, str] = {}

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle options flow."""
        self._errors = {}

        if user_input is not None:
            try:
                # Validate recipients format
                user_input[CONF_DEFAULT_RECIPIENTS] = validate_recipients(
                    user_input[CONF_DEFAULT_RECIPIENTS]
                )
                return self.async_create_entry(title="", data=user_input)
            except vol.Invalid as err:
                _LOGGER.error("Validation error: %s", err)
                self._errors["base"] = "invalid_format"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_DEFAULT_RECIPIENTS,
                    default=self.config_entry.data.get(CONF_DEFAULT_RECIPIENTS, ""),
                ): str,
                vol.Optional(
                    CONF_SESSION_NAME,
                    default=self.config_entry.data.get(CONF_SESSION_NAME, DEFAULT_SESSION_NAME),
                ): str,
            }),
            errors=self._errors,
        ) 