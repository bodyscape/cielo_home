"""None."""
import asyncio
from collections.abc import Awaitable
import contextlib
import copy
from datetime import datetime
import json
import logging
import sys
from threading import Lock, Timer

from aiohttp import ClientSession, ClientWebSocketResponse, WSMsgType

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import URL_API, URL_API_WSS, URL_CIELO, USER_AGENT

_LOGGER = logging.getLogger(__name__)

TIMEOUT_RECONNECT = 10
TIME_REFRESH_TOKEN = 3300
TIMER_PING = 840

# TIME_REFRESH_TOKEN = 20
# TIMER_PING = 10


class CieloHome:
    """Set up Cielo Home api."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Set up Cielo Home api."""
        self._is_running: bool = True
        self._stop_running: bool = False
        self._access_token: str = ""
        self._refresh_token: str = ""
        self._session_id: str = ""
        self._user_id: str = ""
        # self._user_name: str = ""
        # self._password: str = ""
        self._headers: dict[str, str] = {}
        self._websocket: ClientWebSocketResponse
        self.__event_listener: list[object] = []
        self._msg_to_send: list[object] = []
        self._msg_lock = Lock()
        self._timer_refresh: Timer
        self._timer_ping: Timer
        self._timer_connection_lost: Timer = None
        self._last_refresh_token_ts: int
        self._last_ts_msg: int = 0
        self._last_connection_ts: int = 0
        self._x_api_key: str = ""
        self._reconnect_now = False
        self._hass: HomeAssistant = hass
        self._entry: ConfigEntry = entry
        self._appliance_id = None
        self._headers = {
            "content-type": "application/json; charset=UTF-8",
            "referer": URL_CIELO,
            "origin": URL_CIELO,
            "user-agent": USER_AGENT,
        }

    async def close(self):
        """None."""
        self._stop_running = True
        self._is_running = False
        await asyncio.sleep(0.5)

    def add_listener(self, listener: object):
        """None."""
        self.__event_listener.append(listener)

    async def set_x_api_key(self) -> bool:
        """Get the x_api_key."""
        login_url = URL_CIELO
        main_js_url = ""
        async with ClientSession() as session:
            session.headers.add("Cache-Control", "no-cache, no-store, must-revalidate")
            session.headers.add("Pragma", "no-cache")
            session.headers.add("Expires", "0")
            async with session.get(
                login_url + "auth/login?t=" + str(self.get_ts())
            ) as resp:
                html_text = await resp.text()
                index = html_text.find('src="main.')
                index2 = html_text.find('"', index + 5)
                main_js_url = html_text[index + 5 : index2].replace('"', "")

        if main_js_url != "":
            async with ClientSession() as session:  # noqa: SIM117
                async with session.get(
                    login_url + main_js_url + "?t=" + str(self.get_ts())
                ) as resp:
                    html_text = await resp.text()
                    index = html_text.find(",'onChange',") + 12
                    index = html_text.find(",", index) + 1
                    self._x_api_key = html_text[
                        index : html_text.find(",", index)
                    ].replace("'", "")
                    self._headers["x-api-key"] = self._x_api_key

        return self._x_api_key != ""

    async def async_auth(
        self, access_token: str, refresh_token: str, session_id: str, user_id: str
    ) -> bool:
        """Set up Cielo Home auth."""

        if not await self.set_x_api_key():
            return False

        self._access_token = access_token
        self._refresh_token = refresh_token
        self._session_id = session_id
        self._user_id = user_id

        if self._access_token != "":
            create_task_log_exception(self.async_connect_wss())

        self._last_refresh_token_ts = self.get_ts()
        self.start_timer_refreshtoken()

        return True

    def start_timer_refreshtoken(self):
        """None."""
        self._timer_refresh = Timer(60, self.refresh_token)
        self._timer_refresh.start()  # Here run is called

    def refresh_token(self):
        """None."""

        self.start_timer_refreshtoken()
        if (self.get_ts() - self._last_refresh_token_ts) > TIME_REFRESH_TOKEN:
            self._reconnect_now = True
            asyncio.run_coroutine_threadsafe(
                self.async_refresh_token(), self._hass.loop
            ).result()

    async def async_refresh_token(
        self,
        access_token: str = "",
        refresh_token: str = "",
        session_id: str = "",
        user_id: str = "",
        test: bool = False,
    ) -> bool:
        """Set up Cielo Home refresh."""
        _LOGGER.debug("Call refreshToken")

        await self.set_x_api_key()

        # Opening JSON file
        # fullpath: str = str(pathlib.Path(__file__).parent.resolve()) + "/login.json"
        # file = open(fullpath)

        # # returns JSON object as
        # # a dictionary
        # data = json.load(file)

        # # Iterating through the json
        # # list
        # access_token = data["data"]["user"]["accessToken"]
        # refresh_token = data["data"]["user"]["refreshToken"]
        # self._session_id = data["data"]["user"]["sessionId"]
        # file.close()

        if access_token != "":
            self._access_token = access_token
            self._refresh_token = refresh_token
            self._session_id = session_id
            self._user_id = user_id

        self._headers["authorization"] = self._access_token
        async with ClientSession() as session:  # noqa: SIM117
            async with session.get(
                "https://"
                + URL_API
                + "/web/token/refresh?refreshToken="
                + self._refresh_token,
                headers=self._headers,
            ) as response:
                if response.status == 200:
                    repjson = await response.json()
                    if repjson["status"] == 200 and repjson["message"] == "SUCCESS":
                        # print("repJson:", repjson)
                        self._access_token = repjson["data"]["accessToken"]
                        self._refresh_token = repjson["data"]["refreshToken"]
                        if not test:
                            if self._entry is not None:
                                config_data = self._entry.data.copy()
                                config_data["access_token"] = self._access_token
                                config_data["refresh_token"] = self._refresh_token
                                self._hass.config_entries.async_update_entry(
                                    self._entry, data=config_data
                                )
                            _LOGGER.debug("Call refreshToken success")
                            await self._websocket.close()
                            self._last_refresh_token_ts = self.get_ts()
                        else:
                            _LOGGER.debug("Call test refreshToken success")
                        return True
        return False

    async def async_connect_wss(self, update_state: bool = False):
        """None."""
        headers_wss = {
            "Host": URL_API_WSS,
            "Cache-control": "no-cache",
            "Pragma": "no-cache",
            "User-agent": USER_AGENT,
        }

        self._reconnect_now = False
        wss_uri = "wss://" + URL_API_WSS + "/websocket/"

        self._is_running = True
        self._stop_running = False

        try:
            async with ClientSession() as ws_session:  # noqa: SIM117
                async with ws_session.ws_connect(
                    wss_uri,
                    headers=headers_wss,
                    params={"sessionId": self._session_id, "token": self._access_token},
                    origin=URL_CIELO[:-1],
                    compress=15,
                ) as websocket:
                    self._websocket = websocket
                    _LOGGER.info("Connected success")
                    self._last_connection_ts = self.get_ts()
                    self.stop_timer_connection_lost()

                    if update_state:
                        create_task_log_exception(self.update_state_device())
                    self.start_timer_ping()
                    while self._is_running:
                        try:
                            msg = await self._websocket.receive(timeout=0.1)
                            if msg.type in (
                                WSMsgType.CLOSE,
                                WSMsgType.CLOSED,
                                WSMsgType.CLOSING,
                                WSMsgType.ERROR,
                            ):
                                self._timer_ping.cancel()
                                _LOGGER.debug("Websocket closed : %s", msg.type)
                                if (
                                    self.get_ts() - self._last_connection_ts
                                ) > TIMEOUT_RECONNECT:
                                    self._reconnect_now = True
                                break

                            try:
                                js_data = json.loads(msg.data)
                                if _LOGGER.isEnabledFor(logging.DEBUG):
                                    debug_data = copy.copy(js_data)
                                    debug_data["accessToken"] = "*****"
                                    debug_data["refreshToken"] = "*****"
                                    _LOGGER.debug(
                                        "Receive Json : %s", json.dumps(debug_data)
                                    )
                            except ValueError:
                                pass

                            with contextlib.suppress(Exception):
                                if js_data["message_type"] == "StateUpdate":
                                    for listener in self.__event_listener:
                                        listener.data_receive(js_data)

                        except asyncio.exceptions.TimeoutError:
                            pass
                        except asyncio.exceptions.CancelledError:
                            pass

                        msg_sent: bool = False
                        msg: object = None

                        if len(self._msg_to_send) > 0:
                            self._msg_lock.acquire()
                            msg_sent = True
                        try:
                            while len(self._msg_to_send) > 0:
                                msg = self._msg_to_send.pop(0)
                                if msg == "ping":
                                    await self._websocket.send_str(msg)
                                else:
                                    if _LOGGER.isEnabledFor(logging.DEBUG):
                                        debug_data = copy.copy(msg)
                                        debug_data["token"] = "*****"
                                        _LOGGER.debug(
                                            "Send Json : %s", json.dumps(debug_data)
                                        )

                                    await self._websocket.send_json(msg)

                                msg = None
                        except Exception:
                            _LOGGER.error("Failed to send Json")
                            if msg is not None:
                                self._msg_to_send.insert(0, msg)
                        finally:
                            if msg_sent:
                                self._msg_lock.release()

                        await asyncio.sleep(0.1)
        except Exception:
            _LOGGER.error(sys.exc_info()[1])

        if hasattr(self, "_websocket") and not self._websocket.closed:
            self._timer_ping.cancel()
            await self._websocket.close()

        if not self._stop_running:
            # for listener in self.__event_listener:
            #    listener.lost_connection()
            self.start_timer_connection_lost()
            if not self._reconnect_now:
                _LOGGER.debug(
                    "Try reconnection in " + str(TIMEOUT_RECONNECT) + " secondes"
                )
                await asyncio.sleep(TIMEOUT_RECONNECT)
            else:
                _LOGGER.debug("Reconnection")
            create_task_log_exception(self.async_connect_wss(True))

    def send_action(self, msg) -> None:
        """None."""
        msg["token"] = self._access_token
        msg["mid"] = self._session_id
        msg["ts"] = self.get_ts()

        # to be sure each msg have different ts, when 2 msg are send quickly
        if msg["ts"] == self._last_ts_msg:
            msg["ts"] = msg["ts"] + 1

        self._last_ts_msg = msg["ts"]

        self.send_json(msg)

    def start_timer_ping(self):
        """None."""
        self._timer_ping = Timer(TIMER_PING, self.send_ping)
        self._timer_ping.start()  # Here run is called

    def start_timer_connection_lost(self):
        """None."""
        self._timer_connection_lost = Timer(
            TIMEOUT_RECONNECT + 2, self.dispatch_connection_lost
        )
        self._timer_connection_lost.start()  # Here run is called

    def stop_timer_connection_lost(self):
        """None."""
        if self._timer_connection_lost:
            self._timer_connection_lost.cancel()
            self._timer_connection_lost = None

    def dispatch_connection_lost(self):
        """None."""
        for listener in self.__event_listener:
            listener.lost_connection()

    def send_ping(self):
        """None."""
        # data = {"message": "Ping Connection Reset", "token": self._access_token}
        self.start_timer_ping()
        _LOGGER.debug("Send Ping Connection Reset")
        self.send_json("ping")

    def send_json(self, data):
        """None."""
        self._msg_lock.acquire()
        try:
            self._msg_to_send.append(data)
        finally:
            self._msg_lock.release()

    def get_ts(self) -> int:
        """None."""
        return int((datetime.utcnow() - datetime.fromtimestamp(0)).total_seconds())  # noqa: DTZ003

    async def async_get_devices(self):
        """None."""
        devices = await self.async_get_thermostats()

        appliance_ids = ""
        if devices is not None:
            for device in devices:
                appliance_id: str = str(device["applianceId"])
                if appliance_id in appliance_ids:
                    continue

                if appliance_ids != "":
                    appliance_ids = appliance_ids + ","

                appliance_ids = appliance_ids + str(appliance_id)

            appliances = await self.async_get_thermostat_info(appliance_ids)
            appliance_ids = ""

            for device in devices:
                for appliance in appliances:
                    if appliance["applianceId"] == device["applianceId"]:
                        device["appliance"] = appliance

            return devices

        return []

    async def update_state_device(self):
        """None."""
        devices = await self.async_get_thermostats()
        for listener in self.__event_listener:
            for device in devices:
                if device["macAddress"] == listener.get_mac_address():
                    listener.state_device_receive(device)

    async def async_get_thermostats(self):
        """Get de the list Devices/Thermostats."""

        # Opening JSON file
        # fullpath: str = str(pathlib.Path(__file__).parent.resolve()) + "/devices.json"
        # file = open(fullpath)

        # # returns JSON object as
        # # a dictionary
        # data = json.load(file)

        # # Iterating through the json
        # # list
        # devices = data["data"]["listDevices"]

        # file.close()

        self._headers["authorization"] = self._access_token
        devices = None
        async with ClientSession() as session:  # noqa: SIM117
            async with session.get(
                "https://" + URL_API + "/web/devices?limit=420",
                headers=self._headers,
            ) as response:
                if response.status == 200:
                    repjson = await response.json()
                    if repjson["status"] == 200 and repjson["message"] == "SUCCESS":
                        devices = repjson["data"]["listDevices"]
                        if _LOGGER.isEnabledFor(logging.DEBUG):
                            _LOGGER.debug("devices : %s", json.dumps(devices))
                else:
                    pass

        devices_supported: list = []

        if devices is not None:
            for device in devices:
                try:
                    self._appliance_id: str = str(device["applianceId"])
                    devices_supported.append(device)
                except Exception:
                    continue

        return devices_supported

    async def async_get_thermostat_info(self, appliance_ids):
        """Get de the list Devices/Thermostats."""
        # https://api.smartcielo.com/web/sync/appliances/1?applianceIdList=[785]&
        self._headers["authorization"] = self._access_token
        async with ClientSession() as session:  # noqa: SIM117
            async with session.get(
                "https://"
                + URL_API
                + "/web/sync/appliances/1?applianceIdList=["
                + appliance_ids
                + "]",
                headers=self._headers,
            ) as response:
                if response.status == 200:
                    repjson = await response.json()
                    if repjson["status"] == 200 and repjson["message"] == "SUCCESS":
                        appliances = repjson["data"]["listAppliances"]
                        if _LOGGER.isEnabledFor(logging.DEBUG):
                            _LOGGER.debug("appliances : %s", json.dumps(appliances))
                        return appliances
                else:
                    pass
        return []


def create_task_log_exception(awaitable: Awaitable) -> asyncio.Task:
    """None."""

    async def _log_exception(awaitable):
        try:
            return await awaitable
        except Exception as e:
            _LOGGER.exception(e)

    return asyncio.create_task(_log_exception(awaitable))
