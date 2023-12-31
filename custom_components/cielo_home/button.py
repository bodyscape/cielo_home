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
            entity = CieloHomeButton(device)
            entities.append(entity)

    async_add_entities(entities)


class CieloHomeButton(CieloHomeEntity, ButtonEntity):
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
