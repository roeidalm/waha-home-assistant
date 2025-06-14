import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
import traceback

from .const import (
    DOMAIN,
    CONF_BASE_URL,
    CONF_API_KEY,
    CONF_DEFAULT_RECIPIENTS,
    CONF_SESSION_NAME,
    DEFAULT_SESSION_NAME,
)

_LOGGER = logging.getLogger(__name__)

class WahaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WAHA."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        errors = {}
        if user_input is not None:
            # Validate connection to WAHA instance
            valid = await self._test_connection(user_input)
            if valid:
                return self.async_create_entry(title="WAHA WhatsApp", data=user_input)
            else:
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema({
            vol.Required(CONF_BASE_URL): str,
            vol.Optional(CONF_API_KEY): str,
            vol.Required(CONF_DEFAULT_RECIPIENTS): str,  # Comma-separated string
            vol.Optional(CONF_SESSION_NAME, default=DEFAULT_SESSION_NAME): str,
        })
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def _test_connection(self, data: Dict[str, Any]) -> bool:
        """Test connection to the WAHA instance using aiohttp."""
        import aiohttp

        url = f"{data[CONF_BASE_URL].rstrip('/')}/api/server/status"
        headers = {"accept": "application/json"}
        if data.get(CONF_API_KEY):
            headers["Authorization"] = f"Bearer {data[CONF_API_KEY]}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        return True
        except Exception as exc:
            _LOGGER.error("WAHA connection test failed for URL %s: %s\n%s", url, exc, traceback.format_exc())
        return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return WahaOptionsFlowHandler(config_entry)

    @staticmethod
    @callback
    def async_get_suggested_values():
        return {CONF_API_KEY: {"sensitive": True}}

class WahaOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_DEFAULT_RECIPIENTS, default=",").split(","): str,
            vol.Optional(CONF_SESSION_NAME, default=self.config_entry.data.get(CONF_SESSION_NAME, DEFAULT_SESSION_NAME)): str,
        })
        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        ) 