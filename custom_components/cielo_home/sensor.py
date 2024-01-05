"""Platform for Sensor integration."""
from typing import cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .cielohomedevice import CieloHomeDevice
from .const import DOMAIN
from .entity import CieloHomeEntity

ENTITY = "sensor"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """None."""

    entities = []
    cw_devices = hass.data[DOMAIN][config_entry.entry_id + "_devices"]
    for device in cw_devices:
        entity = CieloHomeSensorEntity(
            device,
            "Temperature",
            (
                UnitOfTemperature.FAHRENHEIT
                if device.get_is_device_fahrenheit()
                else UnitOfTemperature.CELSIUS
            ),
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            device.get_uniqueid() + "_temperature",
            "mdi:home-thermometer",
            "get_current_temperature",
            int,
            None,
        )
        entities.append(entity)

        entity = CieloHomeSensorEntity(
            device,
            "Target Temperature",
            (
                UnitOfTemperature.FAHRENHEIT
                if device.get_is_device_fahrenheit()
                else UnitOfTemperature.CELSIUS
            ),
            SensorDeviceClass.TEMPERATURE,
            SensorStateClass.MEASUREMENT,
            device.get_uniqueid() + "_target_temperature",
            "mdi:thermometer",
            "get_target_temperature",
            int,
            None,
        )
        entities.append(entity)

        if device.get_humidity() > 0:
            entity = CieloHomeSensorEntity(
                device,
                "Humidity",
                PERCENTAGE,
                SensorDeviceClass.HUMIDITY,
                SensorStateClass.MEASUREMENT,
                device.get_uniqueid() + "_humidity",
                "mdi:water",
                "get_humidity",
                int,
                None,
            )
            entities.append(entity)

    async_add_entities(entities)


class CieloHomeSensorEntity(CieloHomeEntity, SensorEntity):
    """None."""

    _attr_has_entity_name = True

    def __init__(
        self,
        device: CieloHomeDevice,
        name,
        unit,
        device_c,
        state,
        unique_id,
        icon,
        attr_value,
        attr_type: type,
        options,
    ) -> None:
        """None."""
        super().__init__(device, name, unique_id)
        self._device = device
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_c
        self._attr_state_class = state
        self._attr_icon = icon
        self._attr_type = attr_type
        self._attr_value = attr_value
        self._attr_native_value = cast(
            self._attr_type, getattr(self._device, self._attr_value)()
        )
        if options is not None:
            self._attr_options = options
        self._device.add_listener(self)

    def _update_internal_state(self):
        """None."""
        value = cast(self._attr_type, getattr(self._device, self._attr_value)())
        if value != self._attr_native_value:
            self._attr_native_value = value
