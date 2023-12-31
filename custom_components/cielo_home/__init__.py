"""The Cielo Home integration."""
from __future__ import annotations

import logging
from types import MappingProxyType, MethodType  # noqa: F401

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

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
    ):
        _LOGGER.error("Failed to login to Cielo Home")

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
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await hass.data[DOMAIN][entry.entry_id].close()
        hass.data[DOMAIN].pop(entry.entry_id)
        hass.data[DOMAIN].pop(entry.entry_id + "_devices")

    return unload_ok
