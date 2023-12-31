"""None."""
from homeassistant.components.fan import FanEntity, FanEntityFeature
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
    """None."""
    # entities = []
    # cw_devices = hass.data[DOMAIN][config_entry.entry_id + "_devices"]
    # for device in cw_devices:
    #     entity = CieloHomeFanEntity(device, "Fan", device.get_uniqueid() + "_fan")
    #     entities.append(entity)

    # async_add_entities(entities)


class CieloHomeFanEntity(CieloHomeEntity, FanEntity):
    """An CieloHome fan entity."""

    def __init__(self, device: CieloHomeDevice, name, unique_id) -> None:
        """None."""
        super().__init__(device, device.get_name() + " " + name, unique_id)
        self._attr_icon = "mdi:fan"
        self._attr_preset_modes = self._device.get_fan_modes()
        self._attr_preset_mode = self._device.get_fan_mode()
        self._attr_supported_features = FanEntityFeature.PRESET_MODE
        self._device.add_listener(self)

    def set_preset_mode(self, preset_mode: str) -> None:
        """None."""
        self._device.send_fan_mode(preset_mode)

    def _update_internal_state(self):
        """None."""
        self._attr_preset_mode = self._device.get_fan_mode()
