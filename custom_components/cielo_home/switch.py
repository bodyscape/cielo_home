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
        if device.get_is_appliance_is_freezepoin_display():
            entities.append(
                CieloHomeSwitchFreezingPoint(
                    device, "Freezing Point", device.get_uniqueid() + "FreezingPoint"
                )
            )

        # if device.get_is_light_mode():
        #     entities.append(
        #         CieloHomeSwitchLight(device, "Light", device.get_uniqueid() + "Light")
        #     )

    async_add_entities(entities)


class CieloHomeSwitchFreezingPoint(CieloHomeEntity, SwitchEntity):
    """Representation of a Bond generic device."""

    def __init__(self, device: CieloHomeDevice, name, unique_id) -> None:
        """c"""
        super().__init__(device, device.get_name() + " " + name, unique_id)
        self._attr_is_on = self.is_freezepoint_on()
        self._attr_icon = "mdi:snowflake-thermometer"
        self._device.add_listener(self)

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the freezepoint on."""
        self._device.send_mode_freezepoint()
        self._update_internal_state()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the freezepoint off."""
        self._device.send_mode_freezepoint()
        self._update_internal_state()

    def is_freezepoint_on(self, **kwargs: Any) -> bool:
        """s"""
        return self._device.get_mode() == "freezepoint"

    def _update_internal_state(self):
        """c"""
        self._attr_is_on = self.is_freezepoint_on()


class CieloHomeSwitchPower(CieloHomeEntity, SwitchEntity):
    """Representation of a Bond generic device."""

    def __init__(self, device: CieloHomeDevice, name, unique_id) -> None:
        """c"""
        super().__init__(device, device.get_name() + " " + name, unique_id)
        self._attr_is_on = self.is_power_on()
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

    def is_power_on(self, **kwargs: Any) -> bool:
        """s"""
        return self._device.get_power() == "on"

    def _update_internal_state(self):
        """c"""
        self._attr_is_on = self.is_power_on()


# i have no idea why, but call to turn on and off the light is inverted on the cielo app
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
