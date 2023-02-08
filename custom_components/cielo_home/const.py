"""Constants for the Cielo Home integration."""
from homeassistant.components.climate import PRESET_NONE

DOMAIN = "cielo_home"
URL_API = "api.smartcielo.com"
URL_API_WSS = "apiwss.smartcielo.com"
URL_CIELO = "https://home.cielowigle.com/"

SWING_ADJUST = "Adjust"
SWING_AUTO_STOP = "Auto/stop"
SWING_AUTO = "Auto"
SWING_POSITION1 = "Position 1"
SWING_POSITION2 = "Position 2"
SWING_POSITION3 = "Position 3"
SWING_POSITION4 = "Position 4"
SWING_POSITION5 = "Position 5"
SWING_POSITION6 = "Position 6"

PRESET_NONE = "none"
PRESET_TURBO = "Turbo"
PRESET_MODES = [PRESET_NONE, PRESET_TURBO]

FAN_AUTO = "auto"
FAN_LOW = "Low"
FAN_MEDIUM = "Medium"
FAN_HIGH = "High"
