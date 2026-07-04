"""Config flow for Cielo Home integration."""

from __future__ import annotations

from collections.abc import Mapping
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
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Optional("force_connection_source", default=False): bool,
        vol.Optional("connection_source", default=False): bool,
    }
)

# Re-auth only needs the credentials; the connection-source toggles are kept
# from the existing entry.
STEP_REAUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Log in with email/password and return the config-entry data to store."""

    api = CieloHome(hass, None)

    tokens = await api.async_login(data["username"], data["password"])
    if tokens is None:
        _LOGGER.error("Failed to login to Cielo Home")
        raise InvalidAuth

    # Confirm the obtained tokens actually work against the /web/* API.
    if not await api.async_refresh_token(
        tokens["access_token"],
        tokens["refresh_token"],
        tokens["session_id"],
        tokens["user_id"],
        tokens["x_api_key"],
        True,
    ):
        _LOGGER.error("Cielo tokens failed validation")
        raise InvalidAuth

    entry_data = {
        **tokens,
        "force_connection_source": data.get("force_connection_source", False),
        "connection_source": data.get("connection_source", False),
    }
    return {"title": "Cielo Home", "data": entry_data}


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
            return self.async_create_entry(title=info["title"], data=info["data"])

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication when the stored token can no longer refresh."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm re-authentication with email + password."""
        errors: dict[str, str] = {}

        if user_input is not None:
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
                entry = self._get_reauth_entry()
                # Keep the user's existing connection-source toggles.
                data = {
                    **info["data"],
                    "force_connection_source": entry.data.get(
                        "force_connection_source", False
                    ),
                    "connection_source": entry.data.get("connection_source", False),
                }
                return self.async_update_reload_and_abort(entry, data=data)

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Re-authenticate on demand from the entry's menu (no delete needed)."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
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
                return self.async_update_reload_and_abort(entry, data=info["data"])

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA,
                {
                    "force_connection_source": entry.data.get(
                        "force_connection_source", False
                    ),
                    "connection_source": entry.data.get("connection_source", False),
                },
            ),
            errors=errors,
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
            # Persist the toggles into entry.data (where __init__ reads them)
            # and trigger a reload via the update listener.
            new_data = {
                **self.config_entry.data,
                "force_connection_source": user_input["force_connection_source"],
                "connection_source": user_input["connection_source"],
            }
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "force_connection_source",
                        default=self.config_entry.data.get(
                            "force_connection_source", False
                        ),
                    ): bool,
                    vol.Required(
                        "connection_source",
                        default=self.config_entry.data.get(
                            "connection_source", False
                        ),
                    ): bool,
                }
            ),
        )
