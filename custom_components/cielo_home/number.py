"""None."""
from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .cielohomedevice import CieloHomeDevice
from .const import DOMAIN
from .entity import CieloHomeEntity

Any = object()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """None."""
    entities = []
    cw_devices = hass.data[DOMAIN][config_entry.entry_id + "_devices"]
    for device in cw_devices:
        if device.get_fan_modes() is not None:
            entity = CieloHomeTargetTempNumber(device)
            entities.append(entity)

    async_add_entities(entities)


class CieloHomeTargetTempNumber(CieloHomeEntity, NumberEntity):
    """None."""

    def __init__(self, device: CieloHomeDevice) -> None:
        """None."""
        super().__init__(
            device,
            device.get_name() + " " + "Target Temperature",
            device.get_uniqueid() + "_target_temperature",
        )
        self._attr_icon = "mdi:home-thermometer"
        self._attr_device_class = NumberDeviceClass.TEMPERATURE

        self._attr_mode: NumberMode = NumberMode.AUTO
        self._attr_native_unit_of_measurement = self._device.get_unit_of_temperature()
        self._attr_native_step = self._device.get_temp_increment()
        self._device.add_listener(self)
        self._update_internal_state()

    def _update_internal_state(self):
        """None."""
        self._attr_native_value = self._device.get_target_temperature()

        if self._device.get_supportTargetTemp() and self._device.get_max_temp() > 0:
            self._attr_native_max_value = self._device.get_max_temp()
        if self._device.get_supportTargetTemp() and self._device.get_min_temp() > 0:
            self._attr_native_min_value = self._device.get_min_temp()

    def set_native_value(self, value: float) -> None:
        """Set new value."""
        temp: int = int(
            self._device.get_adjust_temp(
                self._device.get_unit_of_temperature_appliance(),
                self._device.get_unit_of_temperature(),
                int(value),
            )
        )
        self._device.send_temperature(temp)
