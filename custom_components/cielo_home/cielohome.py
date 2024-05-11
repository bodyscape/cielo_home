"""None."""
import asyncio
from collections.abc import Awaitable
import contextlib
import copy
from datetime import datetime
import json
import logging
import re
import sys
from threading import Lock, Timer

from aiohttp import ClientSession, ClientWebSocketResponse, WSMsgType

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import URL_API, URL_API_WSS, URL_CIELO, USER_AGENT

_LOGGER = logging.getLogger(__name__)

TIMEOUT_RECONNECT = 10
TIME_REFRESH_TOKEN = 3300
TIMER_PING = 540
TIMER_PONG = 60

# TIME_REFRESH_TOKEN = 20
# TIMER_PING = 100


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
        self._ws_session: ClientSession
        self.__event_listener: list[object] = []
        self._msg_to_send: list[object] = []
        self._msg_lock = Lock()
        self._timer_connection_lost: Timer = None
        self._last_refresh_token_ts: int
        self._token_expire_in_ts: int
        self._last_ts_msg: int = 0
        self._last_ts_ping: int = 0
        self._last_ts_pong: int = 0
        self._last_connection_ts: int = 0
        self._x_api_keys: list = None
        self._last_x_api_key: str = None
        self._reconnect_now = False
        self.hass: HomeAssistant = hass
        self._entry: ConfigEntry = entry
        self._appliance_id = None
        self.background_tasks_wss = set()
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
                    x = re.compile(
                        r"['][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9]{36}[']"
                    )
                    keys: list = x.findall(html_text)
                    if len(keys) > 0:
                        for x in range(len(keys)):
                            keys[x] = keys[x].replace("'", "")
                        self._x_api_keys = keys

        return self._x_api_keys is not None

    async def async_auth(
        self, access_token: str, refresh_token: str, session_id: str, user_id: str
    ) -> bool:
        """Set up Cielo Home auth."""

        self._access_token = access_token
        self._refresh_token = refresh_token
        self._session_id = session_id
        self._user_id = user_id

        self._last_refresh_token_ts = self.get_ts()
        self._token_expire_in_ts = self.get_ts() + TIME_REFRESH_TOKEN

        with contextlib.suppress(KeyError):
            if self._entry is not None:
                self._last_x_api_key = self._entry.data["x_api_key"]
        await self.try_async_refresh_token(test=True)

        if self._access_token != "":
            self.create_websocket_log_exception(False)

        return True

    async def try_async_refresh_token(
        self,
        access_token: str = "",
        refresh_token: str = "",
        session_id: str = "",
        user_id: str = "",
        test: bool = False,
    ) -> bool:
        """Set up Cielo Home auth."""
        if self._last_x_api_key is not None:
            self._headers["x-api-key"] = self._last_x_api_key
            res = await self.async_refresh_token(
                access_token, refresh_token, session_id, user_id, test
            )
            if res:
                return True

        try:
            await self.set_x_api_key()
        except Exception:
            _LOGGER.error(sys.exc_info()[1])

        for key in self._x_api_keys:
            if self._last_x_api_key is not None:
                if self._last_x_api_key == key:
                    continue

            self._headers["x-api-key"] = key
            res = await self.async_refresh_token(
                access_token, refresh_token, session_id, user_id, test, False
            )
            if res:
                self._last_x_api_key = key
                if self._entry is not None:
                    config_data = self._entry.data.copy()
                    config_data["x_api_key"] = key
                    self.hass.config_entries.async_update_entry(
                        self._entry, data=config_data
                    )
                return True

        return False

    async def async_refresh_token(
        self,
        access_token: str = "",
        refresh_token: str = "",
        session_id: str = "",
        user_id: str = "",
        test: bool = False,
        refreshKey: bool = True,
    ) -> bool:
        """Set up Cielo Home refresh."""
        _LOGGER.debug("Call refreshToken %s", self._headers["x-api-key"])

        if refreshKey:
            try:
                await self.set_x_api_key()
            except Exception:
                _LOGGER.error(sys.exc_info()[1])

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
        try:
            if test:
                self._last_refresh_token_ts = self.get_ts()
                self._token_expire_in_ts = self.get_ts() + TIME_REFRESH_TOKEN

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
                            self._access_token = repjson["data"]["accessToken"]
                            self._refresh_token = repjson["data"]["refreshToken"]
                            expire: int = int(repjson["data"]["expiresIn"]) - 300
                            if (
                                expire < self._token_expire_in_ts
                                or expire < self.get_ts()
                            ):
                                self._token_expire_in_ts = (
                                    self.get_ts() + TIME_REFRESH_TOKEN
                                )
                            else:
                                self._token_expire_in_ts = expire

                            if not test:
                                if self._entry is not None:
                                    config_data = self._entry.data.copy()
                                    config_data["access_token"] = self._access_token
                                    config_data["refresh_token"] = self._refresh_token
                                    self.hass.config_entries.async_update_entry(
                                        self._entry, data=config_data
                                    )
                                _LOGGER.debug("Call refreshToken success")
                                await self._ws_session.close()
                                self._last_refresh_token_ts = self.get_ts()
                            else:
                                _LOGGER.debug("Call test refreshToken success")
                            return True
        except Exception:
            _LOGGER.error(sys.exc_info()[1])

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
                self._ws_session = ws_session
                async with ws_session.ws_connect(
                    wss_uri,
                    headers=headers_wss,
                    params={
                        "sessionId": self._session_id,
                        "token": self._access_token,
                    },
                    origin=URL_CIELO[:-1],
                    compress=15,
                    autoping=False,
                ) as websocket:
                    self._websocket = websocket
                    if self._last_ts_ping == 0:
                        self._last_ts_ping = self.get_ts()
                        self._last_ts_pong = self._last_ts_ping + TIMER_PONG

                    _LOGGER.info("Connected success")
                    self._last_connection_ts = self.get_ts()
                    self.stop_timer_connection_lost()

                    if update_state:
                        self.create_task_log_exception(
                            self.update_state_device(), False
                        )
                    # self.start_timer_ping()
                    while self._is_running:
                        now: int = self.get_ts()

                        try:
                            msg = await self._websocket.receive(timeout=0.1)
                            if msg.type in (
                                WSMsgType.CLOSE,
                                WSMsgType.CLOSED,
                                WSMsgType.CLOSING,
                                WSMsgType.ERROR,
                            ):
                                # self._timer_ping.cancel()
                                _LOGGER.debug("Websocket closed : %s", msg.type)
                                if (now - self._last_connection_ts) > TIMEOUT_RECONNECT:
                                    self._reconnect_now = True
                                break

                            try:
                                js_data = json.loads(msg.data)
                                if _LOGGER.isEnabledFor(logging.DEBUG):
                                    debug_data = copy.copy(js_data)
                                    if hasattr(debug_data, "accessToken"):
                                        debug_data["accessToken"] = "*****"
                                    if hasattr(debug_data, "refreshToken"):
                                        debug_data["refreshToken"] = "*****"
                                    _LOGGER.debug(
                                        "Receive Json : %s", json.dumps(debug_data)
                                    )

                                with contextlib.suppress(Exception):
                                    if js_data["message"] == "Internal server error":
                                        self._last_ts_pong = self.get_ts() + 1

                                with contextlib.suppress(Exception):
                                    if js_data["message_type"] == "StateUpdate":
                                        for listener in self.__event_listener:
                                            listener.data_receive(js_data)

                            except ValueError:
                                pass

                        except asyncio.exceptions.TimeoutError:
                            pass
                        except asyncio.exceptions.CancelledError:
                            pass

                        if now > (self._token_expire_in_ts):
                            self._reconnect_now = True
                            self._token_expire_in_ts = now + 60
                            self.create_task_log_exception(
                                self.try_async_refresh_token()
                            )
                        elif now - self._last_ts_ping >= TIMER_PING:
                            self._last_ts_ping = now
                            self._last_ts_pong = now
                            self.send_json("ping")
                        elif (
                            now > (self._last_ts_pong + TIMER_PONG)
                        ) and self._last_ts_pong == self._last_ts_ping:
                            self._reconnect_now = True
                            self._is_running = False

                        msg: object = None
                        if len(self._msg_to_send) > 0:
                            with self._msg_lock:
                                try:
                                    while len(self._msg_to_send) > 0:
                                        msg = self._msg_to_send.pop(0)
                                        if msg == "ping":
                                            _LOGGER.debug("Send text : ping")
                                            await self._websocket.send_str(msg)
                                        else:
                                            if _LOGGER.isEnabledFor(logging.DEBUG):
                                                debug_data = copy.copy(msg)
                                                # debug_data["token"] = "*****"
                                                _LOGGER.debug(
                                                    "Send Json : %s",
                                                    json.dumps(debug_data),
                                                )

                                            await self._websocket.send_json(msg)

                                        msg = None
                                        await asyncio.sleep(0.1)
                                except Exception:
                                    _LOGGER.error("Failed to send Json")
                                    if msg is not None:
                                        self._msg_to_send.insert(0, msg)

        except Exception:
            _LOGGER.error(sys.exc_info()[1])

        if hasattr(self, "_ws_session") and not self._ws_session.closed:
            # self._timer_ping.cancel()
            await self._ws_session.close()

        if hasattr(self, "_websocket") and not self._websocket.closed:
            # self._timer_ping.cancel()
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
            self._last_ts_ping = 0
            self.create_websocket_log_exception(True)

    def send_action(self, msg) -> None:
        """None."""
        # msg["token"] = self._access_token
        msg["mid"] = self._session_id
        msg["ts"] = self.get_ts()

        # to be sure each msg have different ts, when 2 msg are send quickly
        if msg["ts"] == self._last_ts_msg:
            msg["ts"] = msg["ts"] + 1

        self._last_ts_msg = msg["ts"]

        self.send_json(msg)

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

    def send_json(self, data):
        """None."""
        with self._msg_lock:
            try:
                self._msg_to_send.append(data)
            except Exception:
                _LOGGER.error(sys.exc_info()[1])

    def get_ts(self) -> int:
        """None."""
        return int(datetime.now().timestamp())
        # return int((datetime.utcnow() - datetime.fromtimestamp(0)).total_seconds())  # noqa: DTZ003

    async def async_get_devices(self):
        """None."""
        devices = await self.async_get_thermostats()
        devicesNotSupported = []

        appliance_ids = ""
        if devices is not None:
            for device in devices:
                appliance_id: str = str(device["applianceId"])
                if appliance_id in ("0", ""):
                    devicesNotSupported.append(device)
                    continue

                if appliance_id in appliance_ids:
                    continue

                if appliance_ids != "":
                    appliance_ids = appliance_ids + ","

                appliance_ids = appliance_ids + str(appliance_id)

            appliances = await self.async_get_thermostat_info(appliance_ids)
            appliance_ids = ""

            if len(devicesNotSupported) > 0:
                for device in devicesNotSupported:
                    _LOGGER.warning(
                        "Device '"
                        + str(device["deviceName"])
                        + "' not supported, invalid appliance '"
                        + str(device["applianceId"])
                        + "'"
                    )
                    devices.remove(device)

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
        if self._last_x_api_key is None:
            await self.try_async_refresh_token()

        self._headers["authorization"] = self._access_token
        self._headers["x-api-key"] = self._last_x_api_key
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
        self._headers["x-api-key"] = self._last_x_api_key
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

    def create_websocket_log_exception(self, update_state: bool = True) -> asyncio.Task:
        """None."""
        task = asyncio.create_task(_log_exception(self.async_connect_wss(update_state)))
        self.background_tasks_wss.add(task)
        task.add_done_callback(self.call_back_task)
        return task

    def call_back_task(self, task: asyncio.Task):
        """None."""
        self.background_tasks_wss.remove(task)

    def create_task_log_exception(
        self, awaitable: Awaitable, long_running: bool = True
    ) -> asyncio.Task:
        """None."""

        task = asyncio.create_task(_log_exception(awaitable))
        if long_running:
            self.background_tasks_wss.add(task)
            task.add_done_callback(self.call_back_task)
        return task


async def _log_exception(awaitable):
    try:
        return await awaitable
    except Exception as e:
        _LOGGER.exception(e)
