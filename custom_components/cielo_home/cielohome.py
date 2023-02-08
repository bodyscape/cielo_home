"""c"""
import asyncio
from datetime import datetime
import json
import logging
from threading import Timer

from aiohttp import ClientSession, ClientWebSocketResponse, WSMsgType

from .const import URL_API, URL_API_WSS, URL_CIELO

_LOGGER = logging.getLogger(__name__)


class CieloHome:
    """Set up Cielo Home api."""

    def __init__(self) -> None:
        """Set up Cielo Home api."""
        self._is_running: bool = True
        self._stop_running: bool = False
        self._access_token: str = ""
        self._refresh_token: str = ""
        self._session_id: str = ""
        self._user_id: str = ""
        self._user_name: str = ""
        self._password: str = ""
        self._headers: dict[str, str] = {}
        self._websocket: ClientWebSocketResponse
        self.__event_listener: list[object] = []
        self._timer_refresh: Timer
        self._timer_ping: Timer
        self._last_refresh_token_ts: int

    async def close(self):
        """c"""
        self._stop_running = True
        self._is_running = False
        await asyncio.sleep(0.5)

    def add_listener(self, listener: object):
        """c"""
        self.__event_listener.append(listener)

    async def async_auth(
        self, user_name: str, password: str, connect_ws: bool = False
    ) -> bool:
        """Set up Cielo Home auth."""
        pload = {}
        pload["user"] = {
            "userId": user_name,
            "password": password,
            "mobileDeviceId": "WEB",
            "deviceTokenId": "WEB",
            "appType": "WEB",
            "appVersion": "1.0",
            "timeZone": "America/Toronto",
            "mobileDeviceName": "chrome",
            "deviceType": "WEB",
            "ipAddress": "0.0.0.0",
            "isSmartHVAC": 0,
            "locale": "en",
        }

        self._headers = {
            "content-type": "application/json; charset=UTF-8",
            "referer": URL_CIELO,
            "origin": URL_CIELO,
            "user-agent": "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "x-api-key": "7xTAU4y4B34u8DjMsODlEyprRRQEsbJ3IB7vZie4",
        }

        async with ClientSession() as session:
            async with session.post(
                "https://" + URL_API + "/web/login",
                headers=self._headers,
                json=pload,
            ) as response:
                if response.status == 200:
                    repjson = await response.json()
                    if repjson["status"] == 200 and repjson["message"] == "SUCCESS":
                        # print("repJson:", repjson)
                        self._access_token = repjson["data"]["user"]["accessToken"]
                        self._refresh_token = repjson["data"]["user"]["refreshToken"]
                        self._session_id = repjson["data"]["user"]["sessionId"]
                        self._user_id = repjson["data"]["user"]["userId"]
                        self._user_name = user_name
                        self._password = password

                    if connect_ws and self._access_token != "":
                        asyncio.create_task(self.async_connect_wss())
                    # task.cancel()

                    self._last_refresh_token_ts = self.get_ts()
                    self.start_timer_refreshtoken()
                    # self._websocket.close()
                    return self._access_token != ""

        return False

    def start_timer_refreshtoken(self):
        """c"""
        self._timer_refresh = Timer(60, self.refresh_token)
        self._timer_refresh.start()  # Here run is called

    def refresh_token(self):
        """c"""

        self.start_timer_refreshtoken()
        if (self.get_ts() - self._last_refresh_token_ts) > 1200:
            asyncio.run(self.async_refresh_token())

    async def async_refresh_token(self):
        """Set up Cielo Home refresh."""
        self._headers["authorization"] = self._access_token
        async with ClientSession() as session:
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
                        self._last_refresh_token_ts = self.get_ts()
                        self._is_running = False

    async def async_connect_wss(self):
        """c"""
        headers_wss = {
            "host": URL_API_WSS,
            "origin": URL_CIELO,
            "accept-encoding": "gzip, deflate, br",
            "cache-control": "no-cache",
            "connection": "Upgrade",
            "pragma": "no-cache",
            "upgrade": "websocket",
            "user-agent": "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        }

        wss_uri = (
            "wss://"
            + URL_API_WSS
            + "/websocket/?sessionId="
            + self._session_id
            + "&token="
            + self._access_token
        )

        self._is_running = True
        self._stop_running = False
        try:
            async with ClientSession() as ws_session:
                async with ws_session.ws_connect(
                    wss_uri, headers=headers_wss
                ) as websocket:
                    self._websocket = websocket

                    # await prompt_and_send(ws, access_token, session_id)
                    self._last_refresh_token_ts = self.get_ts()
                    self.start_timer_ping()
                    while self._is_running:
                        try:
                            msg = await self._websocket.receive(timeout=0.1)
                            if msg.type in (
                                WSMsgType.CLOSE,
                                WSMsgType.CLOSED,
                                WSMsgType.CLOSING,
                            ):
                                break

                            try:
                                js_data = json.loads(msg.data)
                                _LOGGER.debug("Receive Json : %s", json.dumps(msg))
                            except ValueError:
                                pass

                            if js_data["message_type"] == "StateUpdate":
                                for listener in self.__event_listener:
                                    listener.data_receive(js_data)
                        except asyncio.exceptions.TimeoutError:
                            # print("TimeoutError ", self.get_ts())
                            pass
                        except asyncio.exceptions.CancelledError:
                            pass

                        await asyncio.sleep(0.1)
        except Exception:
            self._last_refresh_token_ts = self.get_ts() - 1200

        if not self._websocket.closed:
            self._timer_ping.cancel()
            await self._websocket.close()

        if not self._stop_running:
            await self.async_connect_wss()

    def send_action(self, msg) -> None:
        """c"""
        msg["token"] = self._access_token
        msg["mid"] = self._session_id
        msg["ts"] = self.get_ts()

        self.send_json(msg)

    def start_timer_ping(self):
        """c"""
        self._timer_ping = Timer(600, self.send_ping)
        self._timer_ping.start()  # Here run is called

    def send_ping(self):
        """c"""
        data = {"message": "Ping Connection Reset", "token": self._access_token}
        self.start_timer_ping()
        self.send_json(data)

    def send_json(self, data):
        """c"""
        _LOGGER.debug("Send Json : %s", json.dumps(data))
        asyncio.run(self._websocket.send_json(data))

    def get_ts(self) -> int:
        """c"""
        return int((datetime.utcnow() - datetime.fromtimestamp(0)).total_seconds())

    async def async_get_thermostats(self):
        """Get de the list Devices/Thermostats."""

        self._headers["authorization"] = self._access_token
        devices = None
        async with ClientSession() as session:
            async with session.get(
                "https://" + URL_API + "/web/devices?limit=100",
                headers=self._headers,
            ) as response:
                if response.status == 200:
                    repjson = await response.json()
                    appliance_ids = ""
                    if repjson["status"] == 200 and repjson["message"] == "SUCCESS":
                        devices = repjson["data"]["listDevices"]
                else:
                    pass

        if devices is not None:
            for device in devices:
                appliance_id: str = str(device["applianceId"])
                if appliance_id in appliance_ids:
                    break

                if appliance_ids != "":
                    appliance_ids = appliance_ids + ","

                appliance_ids = appliance_ids + str(appliance_id)

            appliances = await self.async_get_thermostat_info(appliance_ids)
            for device in devices:
                for appliance in appliances:
                    if appliance["applianceId"] == device["applianceId"]:
                        device["appliance"] = appliance

            return devices

        return []

    async def async_get_thermostat_info(self, appliance_ids):
        """Get de the list Devices/Thermostats."""
        # https://api.smartcielo.com/web/sync/appliances/1?applianceIdList=[785]&
        self._headers["authorization"] = self._access_token
        async with ClientSession() as session:
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
                        return repjson["data"]["listAppliances"]
                else:
                    pass
        return []
