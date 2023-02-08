"""c"""

from homeassistant.helpers.entity import DeviceInfo, Entity

from .cielohomedevice import CieloHomeDevice
from .const import DOMAIN


class CieloHomeEntity(Entity):
    """c"""

    def __init__(self, device: CieloHomeDevice, name: str, unique_id: str) -> None:
        """Initialize a CieloHomeEntity."""
        super().__init__()
        self._device = device
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_available = device.get_status()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.get_uniqueid())},
            manufacturer="CIELO HOME",
            model=self._device.get_device_type()
            + " ("
            + self._device.get_device_type_version()
            + ")",
            name=self._device.get_name(),
            sw_version=self._device.get_version(),
        )

    def _update_internal_state(self):
        self._attr_available = self._device.get_status()

    def state_updated(self, data) -> None:
        """c"""
        self._update_internal_state()
        self.schedule_update_ha_state(False)
