"""The Cielo Home integration."""

from __future__ import annotations

import logging
from types import MappingProxyType, MethodType  # noqa: F401

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from .cielohome import CieloHome
from .cielohomedevice import CieloHomeDevice
from .const import DOMAIN

# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.BUTTON,
]


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cielo Home from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    # conf = entry.data
    api = CieloHome(hass, entry)
    # setattr(entry.data, "user_id", "gfdgdfg")

    if not await api.async_auth(
        entry.data["access_token"],
        entry.data["refresh_token"],
        entry.data["session_id"],
        entry.data["user_id"],
        entry.data["x_api_key"],
    ):
        # Stored token could not be refreshed (expired/revoked). Trigger the
        # re-auth flow so the user can log in again instead of silently ending
        # up with all entities unavailable (see issue #109).
        raise ConfigEntryAuthFailed(
            "Cielo Home token refresh failed; please re-authenticate"
        )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = api

    list_devices = await api.async_get_devices()
    cw_devices: list[CieloHomeDevice] = []

    force_connection_source = False
    connection_source = False
    try:
        force_connection_source = entry.data["force_connection_source"]
        connection_source = entry.data["connection_source"]
    except KeyError:
        pass

    for device in list_devices:
        cw_device = CieloHomeDevice(
            device,
            api,
            force_connection_source,
            connection_source,
            entry.data["user_id"],
        )
        cw_devices.append(cw_device)

    hass.data[DOMAIN][entry.entry_id + "_devices"] = cw_devices
    entry.async_on_unload(entry.add_update_listener(update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await hass.data[DOMAIN][entry.entry_id].close()
        hass.data[DOMAIN].pop(entry.entry_id)
        hass.data[DOMAIN].pop(entry.entry_id + "_devices")

    return unload_ok


# Entry-data keys the integration rewrites itself during normal operation
# (token rotation). Changes limited to these must NOT trigger a reload,
# otherwise every ~hourly (or, on WSS failure, every reconnect) token
# refresh reloads the whole integration -- destroying the connection and
# any reconnect backoff, producing a reload storm that keeps the WSS
# endpoint rate-limited (HTTP 429) and the devices permanently offline.
_TOKEN_KEYS = frozenset({"access_token", "refresh_token", "session_id"})


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle entry update; skip reloads caused by our own token writes."""

    api: CieloHome = hass.data[DOMAIN][config_entry.entry_id]

    # Detect whether anything other than the self-managed token fields
    # changed. Only a genuine config/options change should reload.
    changed = {
        k
        for k in set(config_entry.data) | set(api.last_entry_data)
        if config_entry.data.get(k) != api.last_entry_data.get(k)
    }
    api.last_entry_data = dict(config_entry.data)
    non_token_change = bool(changed - _TOKEN_KEYS)

    if api.can_reload and non_token_change:
        _LOGGER.info("Reload integration")
        hass.config_entries.async_schedule_reload(config_entry.entry_id)
    else:
        api.can_reload = True
