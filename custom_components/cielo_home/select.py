"""None."""
from homeassistant.components.climate import HVACMode
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .cielohomedevice import CieloHomeDevice
from .const import (
    DEVICE_BREEZ_MAX,
    DOMAIN
)
from .entity import CieloHomeEntity


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
            entity_fan = CieloHomeFanSelect(device)
            entities.append(entity_fan)

        if device.get_is_available_swing_modes():
            entity_swing = CieloHomeSwingSelect(device)
            entities.append(entity_swing)

        if device.get_preset_modes() is not None:
            entity_preset = CieloHomePresetSelect(device)
            entities.append(entity_preset)

        if device.get_hvac_modes() is not None:
            entity_hvac = CieloHomeHvacSelect(device)
            entities.append(entity_hvac)

    async_add_entities(entities)


class CieloHomeFanSelect(CieloHomeEntity, SelectEntity):
    """Representation of a select entity."""

    def __init__(self, device: CieloHomeDevice) -> None:
        """None."""
        super().__init__(
            device,
            device.get_name() + " " + "Fan",
            device.get_uniqueid() + "_fan",
        )
        self._attr_options = self._device.get_fan_modes()
        self._attr_icon = "mdi:fan"
        self._attr_current_option = self._device.get_fan_mode()
        self._device.add_listener(self)

    def _update_internal_state(self):
        """None."""
        self._attr_current_option = self._device.get_fan_mode()

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        self._device.send_fan_mode(option)


class CieloHomeSwingSelect(CieloHomeEntity, SelectEntity):
    """Representation of a select entity."""

    def __init__(self, device: CieloHomeDevice) -> None:
        """None."""
        super().__init__(
            device, device.get_name() + " " + "Swing", device.get_uniqueid() + "_swing"
        )
        self._attr_options = self._device.get_swing_modes()
        self._attr_icon = "mdi:angle-acute"
        self._attr_current_option = self._device.get_swing_mode()
        self._device.add_listener(self)

    def _update_internal_state(self):
        """None."""
        self._attr_current_option = self._device.get_swing_mode()

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        self._device.send_swing_mode(option)


class CieloHomePresetSelect(CieloHomeEntity, SelectEntity):
    """Representation of a select entity."""

    def __init__(self, device: CieloHomeDevice) -> None:
        """None."""
        super().__init__(
            device,
            device.get_name() + " " + "Preset",
            device.get_uniqueid() + "_preset",
        )
        self._attr_options = self._device.get_preset_modes()
        self._attr_icon = "mdi:cog-outline"
        self._attr_current_option = self._device.get_preset_mode()
        self._device.add_listener(self)

    def _update_internal_state(self):
        """None."""
        self._attr_current_option = self._device.get_preset_mode()
        if self._device.get_device_type() == DEVICE_BREEZ_MAX:
            self._attr_available = self._device.get_status()
        else:
            self._attr_available = self._device.get_status() and (
                self._device.get_hvac_mode() == HVACMode.HEAT
                or self._device.get_hvac_mode() == HVACMode.COOL
            )

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        self._device.send_preset_mode(option)


class CieloHomeHvacSelect(CieloHomeEntity, SelectEntity):
    """Representation of a select entity."""

    def __init__(self, device: CieloHomeDevice) -> None:
        """None."""
        super().__init__(
            device,
            device.get_name() + " " + "Hvac",
            device.get_uniqueid() + "_hvac",
        )
        self._attr_options = self._device.get_hvac_modes()
        self._attr_icon = "mdi:thermostat"
        self._attr_current_option = self._device.get_hvac_mode()
        self._device.add_listener(self)

    def _update_internal_state(self):
        """None."""
        self._attr_current_option = self._device.get_hvac_mode()

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        self._device.send_hvac_mode(option)
