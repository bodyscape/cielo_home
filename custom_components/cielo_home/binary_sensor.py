"""None."""
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
        entity = CieloHomeStatusBinarySensor(device)
        entities.append(entity)

    async_add_entities(entities)


class CieloHomeStatusBinarySensor(CieloHomeEntity, BinarySensorEntity):
    """Representation of ADS binary sensors."""

    def __init__(self, device: CieloHomeDevice) -> None:
        """None."""
        super().__init__(
            device,
            device.get_name() + " " + "Status",
            device.get_uniqueid() + "_status",
        )
        self._attr_is_on = self._device.get_status()
        self._attr_icon = "mdi:lan-connect"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._device.add_listener(self)

    def _update_internal_state(self):
        """None."""
        self._attr_is_on = self._device.get_status()
