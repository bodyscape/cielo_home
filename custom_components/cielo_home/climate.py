"""Support for Cielo Home thermostats."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    HVAC_MODES,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .cielohomedevice import CieloHomeDevice
from .const import (
    DOMAIN,
    FAN_AUTO_VALUE,
    FAN_HIGH_VALUE,
    FAN_LOW_VALUE,
    FAN_MEDIUM_VALUE,
    PRESET_NONE,
    PRESET_TURBO,
    SWING_ADJUST_VALUE,
    SWING_AUTO_STOP_VALUE,
    SWING_AUTO_VALUE,
    SWING_POSITION1_VALUE,
    SWING_POSITION2_VALUE,
    SWING_POSITION3_VALUE,
    SWING_POSITION4_VALUE,
    SWING_POSITION5_VALUE,
    SWING_POSITION6_VALUE,
)
from .entity import CieloHomeEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Cielo Home thermostat(s)."""
    cw_devices = hass.data[DOMAIN][config_entry.entry_id + "_devices"]
    for device in cw_devices:
        entity = CieloHomeThermostat(device)
        async_add_entities([entity], True)

    platform = entity_platform.async_get_current_platform()

    list_fan_speed = [FAN_AUTO_VALUE, FAN_LOW_VALUE, FAN_MEDIUM_VALUE, FAN_HIGH_VALUE]
    list_preset_mode = [PRESET_NONE, PRESET_TURBO]
    list_swing = [
        SWING_AUTO_VALUE,
        SWING_ADJUST_VALUE,
        SWING_AUTO_STOP_VALUE,
        SWING_POSITION1_VALUE,
        SWING_POSITION2_VALUE,
        SWING_POSITION3_VALUE,
        SWING_POSITION4_VALUE,
        SWING_POSITION5_VALUE,
        SWING_POSITION6_VALUE,
    ]

    platform.async_register_entity_service(
        "sync_ac_state",
        {
            vol.Required("power", default=False): cv.boolean,
            vol.Optional("temp"): vol.Coerce(int),
            vol.Optional("mode"): vol.All(vol.In(HVAC_MODES)),
            vol.Optional("fan_speed"): vol.All(vol.In(list_fan_speed)),
            vol.Optional("swing"): vol.All(vol.In(list_swing)),
            vol.Optional("preset"): vol.All(vol.In(list_preset_mode)),
        },
        "async_sync_ac_state",
    )


class CieloHomeThermostat(CieloHomeEntity, ClimateEntity):
    """Representation of a Cielo Home thermostat."""

    def __init__(self, device: CieloHomeDevice) -> None:
        """Initialize the thermostat."""
        super().__init__(device, device.get_name(), device.get_uniqueid())
        self._attr_target_temperature_step = int(self._device.get_temp_increment())

        self._attr_supported_features |= ClimateEntityFeature.TURN_OFF
        self._attr_supported_features |= ClimateEntityFeature.TURN_ON

        if self._device.get_supportTargetTemp():
            self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_temperature_unit = self._device.get_unit_of_temperature()

        self._attr_hvac_modes = self._device.get_hvac_modes()
        self._attr_fan_modes = self._device.get_fan_modes()
        self._attr_swing_modes = None
        if self._device.get_is_available_swing_modes():
            self._attr_swing_modes = self._device.get_swing_modes()

        if self._attr_fan_modes:
            self._attr_supported_features |= ClimateEntityFeature.FAN_MODE

        if self._device.get_is_available_swing_modes():
            self._attr_supported_features |= ClimateEntityFeature.SWING_MODE

        self._attr_preset_modes = self._device.get_preset_modes()
        if self._attr_preset_modes is not None:
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE

        self._device.add_listener(self)
        self._update_internal_state()

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the system mode."""
        self._device.send_hvac_mode(hvac_mode)
        self._update_internal_state()

    def turn_off(self) -> None:
        """Set the system mode."""
        self._device.send_hvac_mode(HVACMode.OFF)
        self._update_internal_state()

    def turn_on(self) -> None:
        """Set the system mode."""
        self._device.send_power_on()
        self._update_internal_state()

    def set_preset_mode(self, preset_mode: str) -> None:
        """Update the hold mode of the thermostat."""
        self._device.send_preset_mode(preset_mode)
        self._update_internal_state()

    def set_temperature(self, **kwargs: Any) -> None:
        """Set a new target temperature."""

        if ATTR_HVAC_MODE in kwargs:
            self.set_hvac_mode(HVACMode(kwargs[ATTR_HVAC_MODE]))

        if ATTR_TEMPERATURE in kwargs:
            temp: int = int(
                self._device.get_adjust_temp(
                    self._device.get_unit_of_temperature_appliance(),
                    self._attr_temperature_unit,
                    int(kwargs.get(ATTR_TEMPERATURE)),
                )
            )
            self._device.send_temperature(temp)

        self._update_internal_state()

    async def async_sync_ac_state(
        self,
        power: bool,
        temp: int = 0,
        mode: str = "",
        fan_speed: str = "",
        swing: str = "",
        preset: str = "",
    ) -> None:
        """Sync_ac_state."""
        self._device.sync_ac_state(power, temp, mode, fan_speed, swing, preset)

    def set_swing_mode(self, swing_mode: str) -> None:
        """Set new target swing operation."""
        # Update the new state
        self._device.send_swing_mode(swing_mode)
        self._update_internal_state()

    def set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        self._device.send_fan_mode(fan_mode)
        self._update_internal_state()

    @callback
    def _update_internal_state(self):
        """Update our internal state from the last api response."""
        self._attr_target_temperature = self._device.get_target_temperature()
        self._attr_current_temperature = self._device.get_current_temperature()
        self._attr_current_humidity = self._device.get_humidity()
        if self._attr_fan_modes is not None:
            self._attr_fan_mode = self._device.get_fan_mode()
        if self._device.get_is_available_swing_modes():
            self._attr_swing_mode = self._device.get_swing_mode()
        if self._attr_preset_modes is not None:
            self._attr_preset_mode = self._device.get_preset_mode()
        self._attr_hvac_mode = self._device.get_hvac_mode()

        if self._device.get_supportTargetTemp() and self._device.get_max_temp() > 0:
            self._attr_max_temp = self._device.get_max_temp()
        if self._device.get_supportTargetTemp() and self._device.get_min_temp() > 0:
            self._attr_min_temp = self._device.get_min_temp()
