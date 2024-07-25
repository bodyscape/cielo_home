"""Constants for the Cielo Home integration."""

from homeassistant.components.climate import PRESET_NONE

DOMAIN = "cielo_home"
URL_API = "api.smartcielo.com"
URL_API_WSS = "apiwss.smartcielo.com"
URL_CIELO = "https://home.cielowigle.com/"
USER_AGENT = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"

SWING_ADJUST = "Adjust"
SWING_AUTO_STOP = "Auto/stop"
SWING_AUTO = "Auto"
SWING_POSITION1 = "Position 1"
SWING_POSITION2 = "Position 2"
SWING_POSITION3 = "Position 3"
SWING_POSITION4 = "Position 4"
SWING_POSITION5 = "Position 5"
SWING_POSITION6 = "Position 6"


SWING_ADJUST_VALUE = "adjust"
SWING_AUTO_STOP_VALUE = "auto/stop"
SWING_AUTO_VALUE = "auto"
SWING_POSITION1_VALUE = "pos1"
SWING_POSITION2_VALUE = "pos2"
SWING_POSITION3_VALUE = "pos3"
SWING_POSITION4_VALUE = "pos4"
SWING_POSITION5_VALUE = "pos5"
SWING_POSITION6_VALUE = "pos6"

PRESET_TURBO = "Turbo"
PRESET_MODES = [PRESET_NONE, PRESET_TURBO]

FAN_AUTO = "auto"
FAN_LOW = "Low"
FAN_MEDIUM = "Medium"
FAN_HIGH = "High"


FAN_AUTO_VALUE = "auto"
FAN_LOW_VALUE = "low"
FAN_MEDIUM_VALUE = "medium"
FAN_HIGH_VALUE = "high"
FAN_FANSPEED_VALUE = "fanspeed"

FOLLOW_ME_ON = "on"
FOLLOW_ME_OFF = "off"

DEVICE_BREEZ_MAX = "BREEZ-MAX"