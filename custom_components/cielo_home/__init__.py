"""The Cielo Home integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
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

    # username = conf[CONF_USERNAME]
    # password = conf[CONF_PASSWORD]

    api = CieloHome()

    if not await api.async_auth(
        entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], True
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
