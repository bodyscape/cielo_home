"""None."""
from homeassistant.components.button import ButtonEntity
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
        if device.get_light() != "":
            entity = CieloHomeButtonLight(device)
            entities.append(entity)

        if device.get_is_fan_mode_cycle():
            entity = CieloHomeButtonFan(device)
            entities.append(entity)

        if not device.get_supportTargetTemp():
            entity = CieloHomeButtonTempUp(device)
            entities.append(entity)
            entity = CieloHomeButtonTempDown(device)
            entities.append(entity)

    async_add_entities(entities)


class CieloHomeButtonTempUp(CieloHomeEntity, ButtonEntity):
    """Set up CieloHomeButton."""

    def __init__(self, device: CieloHomeDevice) -> None:
        """None."""
        super().__init__(
            device,
            device.get_name() + " " + "Temp Up",
            device.get_uniqueid() + "_tempup",
        )
        self._attr_icon = "mdi:thermometer-chevron-up"
        # self._device.add_listener(self)

    def press(self) -> None:
        """Handle the button press."""
        self._device.send_temperatureUp()


class CieloHomeButtonTempDown(CieloHomeEntity, ButtonEntity):
    """Set up CieloHomeButton."""

    def __init__(self, device: CieloHomeDevice) -> None:
        """None."""
        super().__init__(
            device,
            device.get_name() + " " + "Temp Down",
            device.get_uniqueid() + "_tempdown",
        )
        self._attr_icon = "mdi:thermometer-chevron-down"
        # self._device.add_listener(self)

    def press(self) -> None:
        """Handle the button press."""
        self._device.send_temperatureDown()


class CieloHomeButtonFan(CieloHomeEntity, ButtonEntity):
    """Set up CieloHomeButton."""

    def __init__(self, device: CieloHomeDevice) -> None:
        """None."""
        super().__init__(
            device,
            device.get_name() + " " + "Fan",
            device.get_uniqueid() + "_fan",
        )
        self._attr_icon = "mdi:fan"
        # self._device.add_listener(self)

    def press(self) -> None:
        """Handle the button press."""
        self._device.send_fan_speed_rotate()


class CieloHomeButtonLight(CieloHomeEntity, ButtonEntity):
    """Set up CieloHomeButton."""

    def __init__(self, device: CieloHomeDevice) -> None:
        """None."""
        super().__init__(
            device,
            device.get_name() + " " + "Light",
            device.get_uniqueid() + "_light",
        )
        self._attr_icon = "mdi:lightbulb"
        # self._device.add_listener(self)

    def press(self) -> None:
        """Handle the button press."""
        self._device.send_light_on()
