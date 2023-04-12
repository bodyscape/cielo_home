"""c"""
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .cielohomedevice import CieloHomeDevice
from .const import DOMAIN
from .entity import CieloHomeEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """c"""
    entities = []
    cw_devices = hass.data[DOMAIN][config_entry.entry_id + "_devices"]
    for device in cw_devices:
        entities.append(
            CieloHomeSwitchPower(device, "Power", device.get_uniqueid() + "_power")
        )
        # if device.get_is_light_mode():
        #     entities.append(
        #         CieloHomeSwitchLight(device, "Light", device.get_uniqueid() + "Light")
        #     )

    async_add_entities(entities)


# i have no idea why, but call to turn on and off the light is inverted on the cielo app
class CieloHomeSwitchPower(CieloHomeEntity, SwitchEntity):
    """Representation of a Bond generic device."""

    def __init__(self, device: CieloHomeDevice, name, unique_id) -> None:
        """c"""
        super().__init__(device, device.get_name() + " " + name, unique_id)
        self._attr_is_on = self._device.get_power() == "on"
        self._attr_icon = "mdi:power"
        self._device.add_listener(self)

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        self._device.send_power_on()
        self._update_internal_state()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        self._device.send_power_off()
        self._update_internal_state()

    def _update_internal_state(self):
        """c"""
        self._attr_is_on = self._device.get_power() == "on"


# class CieloHomeSwitchLight(CieloHomeEntity, SwitchEntity):
#     """Representation of a Bond generic device."""

#     def __init__(self, device: CieloHomeDevice, name, unique_id) -> None:
#         """c"""
#         super().__init__(device, device.get_name() + " " + name, unique_id)
#         self._attr_is_on = self._device.get_light() == "on"
#         self._attr_icon = "mdi:lightbulb"
#         self._device.add_listener(self)

#     def turn_on(self, **kwargs: Any) -> None:
#         """Turn the device on."""
#         self._device.send_light_on()
#         self._update_internal_state()

#     def turn_off(self, **kwargs: Any) -> None:
#         """Turn the device off."""
#         self._device.send_light_off()
#         self._update_internal_state()

#     def _update_internal_state(self):
#         """c"""
#         self._attr_is_on = self._device.get_light() == "on"
