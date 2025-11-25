"""Config flow for Cielo Home integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .cielohome import CieloHome
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("access_token"): str,
        vol.Required("refresh_token"): str,
        vol.Required("session_id"): str,
        vol.Required("user_id"): str,
        vol.Required("x_api_key"): str,
        vol.Required("force_connection_source"): bool,
        vol.Required("connection_source"): bool,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    api = CieloHome(hass, None)

    if not await api.async_refresh_token(
        data["access_token"],
        data["refresh_token"],
        data["session_id"],
        data["user_id"],
        data["x_api_key"],
        True,
    ):
        _LOGGER.error("Failed to login to Cielo Home")
        raise InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Cielo Home"}


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cielo Home."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class OptionsFlowHandler(OptionsFlow):
    """Handle Omnilogic client options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage options."""

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "access_token", default=self.config_entry.data["access_token"]
                    ): str,
                    vol.Required(
                        "refresh_token", default=self.config_entry.data["refresh_token"]
                    ): str,
                    vol.Required(
                        "session_id", default=self.config_entry.data["session_id"]
                    ): str,
                    vol.Required(
                        "user_id", default=self.config_entry.data["user_id"]
                    ): str,
                    vol.Required(
                        "x_api_key", default=self.config_entry.data["x_api_key"]
                    ): str,
                    vol.Required(
                        "force_connection_source",
                        default=self.config_entry.data["force_connection_source"],
                    ): bool,
                    vol.Required(
                        "connection_source",
                        default=self.config_entry.data["connection_source"],
                    ): bool,
                }
            ),
        )
