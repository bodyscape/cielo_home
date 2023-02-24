"""The Cielo Home integration."""
import logging

from homeassistant.components.climate import HVACMode
from homeassistant.const import UnitOfTemperature

from .cielohome import CieloHome
from .const import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    PRESET_MODES,
    PRESET_NONE,
    PRESET_TURBO,
    SWING_ADJUST,
    SWING_AUTO,
    SWING_AUTO_STOP,
    SWING_POSITION1,
    SWING_POSITION2,
    SWING_POSITION3,
    SWING_POSITION4,
    SWING_POSITION5,
    SWING_POSITION6,
)

_LOGGER = logging.getLogger(__name__)


class CieloHomeDevice:
    """Set up Cielo Home api."""

    def __init__(self, device, api: CieloHome) -> None:
        """Set up Cielo Home device."""
        self._api = api
        self._device = device
        self.__event_listener: list[object] = []
        self._api.add_listener(self)

    def add_listener(self, listener: object) -> None:
        """c"""
        self.__event_listener.append(listener)

    def send_power_on(self) -> None:
        """c"""
        self._send_power("on")

    def send_power_off(self) -> None:
        """c"""
        self._send_power("off")

    def _send_power(self, value) -> None:
        """c"""
        if self._device["latestAction"]["power"] == value:
            return

        action = self._get_action()
        action["power"] = value
        self._device["latestAction"]["power"] = value
        self._send_msg(action, "power", action["power"])

    def send_turbo_on(self) -> None:
        """c"""
        self._send_turbo("on")

    def send_turbo_off(self) -> None:
        """c"""
        self._send_turbo("off")

    def _send_turbo(self, value) -> None:
        """c"""
        if self._device["latestAction"]["turbo"] == value:
            return

        action = self._get_action()
        action["turbo"] = value
        self._device["latestAction"]["turbo"] = value
        self._send_msg(action, "turbo", "on/off")

    def _send_msg(self, action, action_type, action_value) -> None:
        msg = {
            "action": "actionControl",
            "macAddress": self.get_mac_address(),
            "deviceTypeVersion": self.get_device_type_version(),
            "fwVersion": self.get_fw_version(),
            "actionSource": "WEB",
            "applianceType": self.get_appliance_type(),
            "applianceId": self.get_appliance_id(),
            "actionType": action_type,
            "actionValue": action_value,
            "connection_source": (1 if self.get_device_type_version() == "BL02" else 0),
            "token": "",
            "mid": "",
            "application_version": "1.0.0",
            "ts": 0,
            "actions": action,
        }

        self._api.send_action(msg)
        # self._api.send_action(msg)

    def send_mode_heat(self) -> None:
        """c"""
        self._send_mode("heat")

    def send_mode_cool(self) -> None:
        """c"""
        self._send_mode("cool")

    def send_mode_dry(self) -> None:
        """c"""
        self._send_mode("dry")

    def send_mode_auto(self) -> None:
        """c"""
        self._send_mode("auto")

    def send_mode_fan(self) -> None:
        """c"""
        self._send_mode("fan")

    def _send_mode(self, value) -> None:
        """c"""
        if self.get_power() == "off":
            self.send_power_on()

        if self._device["latestAction"]["mode"] == value:
            return

        action = self._get_action()

        action["mode"] = value
        self._device["latestAction"]["mode"] = value
        self._send_msg(action, "mode", action["mode"])

    def send_fan_speed_medium(self) -> None:
        """c"""
        self._send_fan_speed("medium")

    def send_fan_speed_high(self) -> None:
        """c"""
        self._send_fan_speed("high")

    def send_fan_speed_low(self) -> None:
        """c"""
        self._send_fan_speed("low")

    def send_fan_speed_auto(self) -> None:
        """c"""
        self._send_fan_speed("auto")

    def _send_fan_speed(self, value) -> None:
        """c"""
        if self._device["latestAction"]["fanspeed"] == value:
            return

        action = self._get_action()
        action["fanspeed"] = value
        self._device["latestAction"]["fanspeed"] = value
        self._send_msg(action, "fanspeed", action["fanspeed"])

    def send_swing_adjust(self) -> None:
        """c"""
        self._send_swing("adjust")

    def send_swing_auto(self) -> None:
        """c"""
        self._send_swing("auto")

    def send_swing_auto_stop(self) -> None:
        """c"""
        self._send_swing("auto/stop")

    def send_swing_pos1(self) -> None:
        """c"""
        self._send_swing("pos1")

    def send_swing_pos2(self) -> None:
        """c"""
        self._send_swing("pos2")

    def send_swing_pos3(self) -> None:
        """c"""
        self._send_swing("pos3")

    def send_swing_pos4(self) -> None:
        """c"""
        self._send_swing("pos4")

    def send_swing_pos5(self) -> None:
        """c"""
        self._send_swing("pos5")

    def send_swing_pos6(self) -> None:
        """c"""
        self._send_swing("pos6")

    def _send_swing(self, value) -> None:
        """c"""
        if self._device["latestAction"]["swing"] == value:
            return

        action = self._get_action()
        action["swing"] = value
        self._device["latestAction"]["swing"] = value
        self._send_msg(action, "swing", action["swing"])

    def send_temperature(self, value) -> None:
        """c"""
        if int(self._device["latestAction"]["temp"]) == int(value):
            return

        action = self._get_action()
        action["temp"] = str(value)
        self._device["latestAction"]["temp"] = action["temp"]
        self._send_msg(action, "temp", value)

    def get_current_temperature(self) -> float:
        """c"""
        return float(self._device["latEnv"]["temp"])

    def get_humidity(self) -> float:
        """c"""
        return self._device["latEnv"]["humidity"]

    def get_is_device_fahrenheit(self) -> bool:
        """c"""
        return self._device["isFaren"] == 1

    def get_is_appliance_fahrenheit(self) -> bool:
        """c"""
        return self._device["appliance"]["isFaren"] == 1

    def get_temp_increment(self) -> float:
        """c"""
        return self._device["appliance"]["tempIncrement"]

    def get_available_modes(self) -> str:
        """c"""
        return self._device["appliance"]["mode"]

    def get_available_fan_modes(self) -> str:
        """c"""
        return self._device["appliance"]["fan"]

    def get_available_swing_modes(self) -> str:
        """c"""
        return self._device["appliance"]["swing"]

    def get_is_turbo_mode(self) -> bool:
        """c"""
        try:
            return self._device["appliance"]["turbo"] != ""
        except KeyError:
            pass

        return False

    def get_is_followme_mode(self) -> bool:
        """c"""
        return self._device["appliance"]["followme"] != ""

    def get_range_temp(self) -> str:
        """c"""
        return self._device["appliance"]["temp"]

    def get_uniqueid(self):
        """c"""
        return self.get_mac_address()

    def get_mac_address(self) -> str:
        """c"""
        return self._device["macAddress"]

    def get_name(self) -> str:
        """c"""
        return self._device["deviceName"]

    def get_version(self) -> str:
        """c"""
        return self._device["fwVersion"]

    def get_device_type_version(self) -> str:
        """c"""
        return self._device["deviceTypeVersion"]

    def get_device_type(self) -> str:
        """c"""
        return self._device["deviceType"]

    def get_fw_version(self) -> str:
        """c"""
        return self._device["fwVersion"]

    def get_appliance_id(self) -> int:
        """c"""
        return self._device["applianceId"]

    def get_appliance_type(self) -> str:
        """c"""
        return self._device["applianceType"]

    def get_device(self):
        """c"""
        return self._device

    def get_mode(self) -> str:
        """c"""
        return self._device["latestAction"]["mode"]

    def get_power(self) -> str:
        """c"""
        return self._device["latestAction"]["power"]

    def get_target_temperature(self) -> float:
        """c"""
        return float(self._device["latestAction"]["temp"])

    def get_turbo(self) -> str:
        """c"""
        try:
            return self._device["latestAction"]["turbo"]
        except KeyError:
            pass

        return "off"

    def get_fanspeed(self) -> str:
        """c"""
        return self._device["latestAction"]["fanspeed"]

    def get_swing(self) -> str:
        """c"""
        return self._device["latestAction"]["swing"]

    def get_status(self) -> bool:
        """c"""
        return self._device["deviceStatus"] == 1

    def get_status_str(self) -> str:
        """c"""
        return "on" if self.get_status() else "off"

    def _get_action(self) -> object:
        """c"""
        action = {
            "power": self._device["latestAction"]["power"],
            "mode": self._device["latestAction"]["mode"],
            "fanspeed": self._device["latestAction"]["fanspeed"],
            "temp": self._device["latestAction"]["temp"],
            "swing": self._device["latestAction"]["swing"],
            "oldPower": self._device["latestAction"]["power"],
        }

        try:
            action["turbo"] = self._device["latestAction"]["turbo"]
        except KeyError:
            pass

        try:
            action["light"] = (
                "off"
                if self._device["latestAction"]["light"] == "on/off"
                else self._device["latestAction"]["light"]
            )
        except KeyError:
            pass

        return action

    def get_fan_modes(self) -> list[str]:
        """c"""
        modes = self.get_available_fan_modes()
        modes_list = modes.split(":")
        fan_modes: list = []
        for mode in modes_list:
            if mode == "auto":
                fan_modes.append(FAN_AUTO)
            elif mode == "low":
                fan_modes.append(FAN_LOW)
            elif mode == "medium":
                fan_modes.append(FAN_MEDIUM)
            elif mode == "high":
                fan_modes.append(FAN_HIGH)

        if len(fan_modes) > 0:
            return fan_modes

        return None

    def get_max_temp(self) -> float:
        """c"""
        range_temp: str = self.get_range_temp()
        device_unit: str = self.get_unit_of_temperature_appliance()

        range_temps: list = range_temp.split(":")

        return self.get_adjust_temp(
            self.get_unit_of_temperature(), device_unit, int(range_temps[1])
        )

    def get_min_temp(self) -> float:
        """c"""
        range_temp: str = self.get_range_temp()
        device_unit: str = self.get_unit_of_temperature_appliance()

        range_temps: list = range_temp.split(":")

        return self.get_adjust_temp(
            self.get_unit_of_temperature(), device_unit, int(range_temps[0])
        )

    def get_adjust_temp(
        self, target_unit_temp: str, current_unit_temp: str, temp: int
    ) -> float:
        """Set the system mode."""
        if (
            current_unit_temp == UnitOfTemperature.CELSIUS
            and target_unit_temp == UnitOfTemperature.FAHRENHEIT
        ):
            return int((temp * 18) + 32)
        elif (
            current_unit_temp == UnitOfTemperature.FAHRENHEIT
            and target_unit_temp == UnitOfTemperature.CELSIUS
        ):
            return int((temp - 32) / 1.8)
        else:
            return temp

    def get_fan_mode(self) -> str:
        """c"""
        if self.get_fanspeed() == "auto":
            return FAN_AUTO
        elif self.get_fanspeed() == "low":
            return FAN_LOW
        elif self.get_fanspeed() == "medium":
            return FAN_MEDIUM
        elif self.get_fanspeed() == "high":
            return FAN_HIGH
        else:
            return FAN_AUTO

    def get_hvac_mode(self) -> str:
        """c"""
        if self.get_power() == "off":
            return HVACMode.OFF
        elif self.get_mode() == "auto":
            return HVACMode.AUTO
        elif self.get_mode() == "heat":
            return HVACMode.HEAT
        elif self.get_mode() == "cool":
            return HVACMode.COOL
        elif self.get_mode() == "dry":
            return HVACMode.DRY
        elif self.get_mode() == "fan":
            return HVACMode.FAN_ONLY
        else:
            return HVACMode.OFF

    def get_hvac_modes(self) -> list[str]:
        """c"""
        modes: str = self.get_available_modes()
        modes_list: list = modes.split(":")
        hvac_modes: list = [HVACMode.OFF]
        for mode in modes_list:
            if mode == "auto":
                hvac_modes.append(HVACMode.AUTO)
            elif mode == "cool":
                hvac_modes.append(HVACMode.COOL)
            elif mode == "dry":
                hvac_modes.append(HVACMode.DRY)
            elif mode == "fan":
                hvac_modes.append(HVACMode.FAN_ONLY)
            elif mode == "heat":
                hvac_modes.append(HVACMode.HEAT)
            else:
                pass

        if len(hvac_modes) > 0:
            return hvac_modes

        return None

    def get_swing_mode(self) -> str:
        """c"""
        if self.get_swing() == "auto":
            return SWING_AUTO
        elif self.get_swing() == "adjust":
            return SWING_ADJUST
        elif self.get_swing() == "auto/stop":
            return SWING_AUTO_STOP
        elif self.get_swing() == "pos1":
            return SWING_POSITION1
        elif self.get_swing() == "pos2":
            return SWING_POSITION2
        elif self.get_swing() == "pos3":
            return SWING_POSITION3
        elif self.get_swing() == "pos4":
            return SWING_POSITION4
        elif self.get_swing() == "pos5":
            return SWING_POSITION5
        elif self.get_swing() == "pos6":
            return SWING_POSITION6
        else:
            pass

    def get_swing_modes(self) -> list[str]:
        """c"""
        modes = self.get_available_swing_modes()
        modes_list = modes.split(":")
        swing_modes: list = []
        for mode in modes_list:
            if mode == "auto/stop":
                swing_modes.append(SWING_AUTO_STOP)
            elif mode == "auto":
                swing_modes.append(SWING_AUTO)
            elif mode == "adjust":
                swing_modes.append(SWING_ADJUST)
            elif mode == "pos1":
                swing_modes.append(SWING_POSITION1)
            elif mode == "pos2":
                swing_modes.append(SWING_POSITION2)
            elif mode == "pos3":
                swing_modes.append(SWING_POSITION3)
            elif mode == "pos4":
                swing_modes.append(SWING_POSITION4)
            elif mode == "pos5":
                swing_modes.append(SWING_POSITION5)
            elif mode == "pos6":
                swing_modes.append(SWING_POSITION6)
            else:
                pass

        if len(swing_modes) > 0:
            return swing_modes

        return None

    def get_preset_mode(self) -> str:
        """c"""
        if self.get_turbo() == "on":
            return PRESET_TURBO
        else:
            return PRESET_NONE

    def get_preset_modes(self) -> list[str]:
        """c"""
        if self.get_is_turbo_mode():
            return PRESET_MODES
        else:
            return None

    def get_unit_of_temperature(self) -> str:
        """c"""
        return (
            UnitOfTemperature.FAHRENHEIT
            if self.get_is_device_fahrenheit()
            else UnitOfTemperature.CELSIUS
        )

    def get_unit_of_temperature_appliance(self) -> str:
        """c"""
        return (
            UnitOfTemperature.FAHRENHEIT
            if self.get_is_appliance_fahrenheit()
            else UnitOfTemperature.CELSIUS
        )

    def send_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """c"""
        if hvac_mode == HVACMode.OFF:
            self.send_power_off()
        elif hvac_mode == HVACMode.AUTO:
            self.send_mode_auto()
        elif hvac_mode == HVACMode.HEAT:
            self.send_mode_heat()
        elif hvac_mode == HVACMode.DRY:
            self.send_mode_dry()
        elif hvac_mode == HVACMode.COOL:
            self.send_mode_cool()
        elif hvac_mode == HVACMode.FAN_ONLY:
            self.send_mode_fan()
        else:
            pass

    def send_preset_mode(self, preset_mode: str) -> None:
        """c"""
        if PRESET_TURBO == preset_mode:
            self.send_turbo_on()
        else:
            self.send_turbo_off()

    def send_swing_mode(self, swing_mode: str) -> None:
        """c"""
        if swing_mode == SWING_AUTO:
            self.send_swing_auto()
        elif swing_mode == SWING_AUTO_STOP:
            self.send_swing_auto_stop()
        elif swing_mode == SWING_ADJUST:
            self.send_swing_adjust()
        elif swing_mode == SWING_POSITION1:
            self.send_swing_pos1()
        elif swing_mode == SWING_POSITION2:
            self.send_swing_pos2()
        elif swing_mode == SWING_POSITION3:
            self.send_swing_pos3()
        elif swing_mode == SWING_POSITION4:
            self.send_swing_pos4()
        elif swing_mode == SWING_POSITION5:
            self.send_swing_pos5()
        elif swing_mode == SWING_POSITION6:
            self.send_swing_pos6()
        else:
            pass

    def send_fan_mode(self, fan_mode: str) -> None:
        """c"""
        if fan_mode == FAN_AUTO:
            self.send_fan_speed_auto()
        elif fan_mode == FAN_HIGH:
            self.send_fan_speed_high()
        elif fan_mode == FAN_MEDIUM:
            self.send_fan_speed_medium()
        elif fan_mode == FAN_LOW:
            self.send_fan_speed_low()
        else:
            pass

    def data_receive(self, data) -> None:
        """c"""
        if data["mac_address"] == self.get_mac_address():
            self._device["latEnv"]["temp"] = data["lat_env_var"]["temperature"]
            self._device["latEnv"]["humidity"] = data["lat_env_var"]["humidity"]
            self._device["deviceStatus"] = data["device_status"]
            self._device["latestAction"]["temp"] = data["action"]["temp"]
            self._device["latestAction"]["fanspeed"] = data["action"]["fanspeed"]
            self._device["latestAction"]["mode"] = data["action"]["mode"]
            self._device["latestAction"]["swing"] = data["action"]["swing"]
            self._device["latestAction"]["power"] = data["action"]["power"]

        try:
            self._device["latestAction"]["turbo"] = data["action"]["turbo"]
        except KeyError:
            pass

        try:
            self._device["latestAction"]["light"] = data["action"]["light"]
        except KeyError:
            pass

        self.dispatch_state_updated()

    def state_device_receive(self, device_state):
        """c"""
        device_state["appliance"] = self._device["appliance"]
        self._device = device_state
        self.dispatch_state_updated()

    def dispatch_state_updated(self):
        """c"""
        for listener in self.__event_listener:
            listener.state_updated()

    def lost_connection(self):
        """c"""
        self._device["deviceStatus"] = 0
        self.dispatch_state_updated()
