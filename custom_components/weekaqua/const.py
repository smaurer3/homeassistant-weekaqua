"""Constants for the Week Aqua integration."""
from typing import Final

DOMAIN: Final = "weekaqua"
MANUFACTURER: Final = "Week Aqua"

MANUFACTURER_ID: Final = 18007
SERVICE_UUID: Final = "0000fff0-0000-1000-8000-00805f9b34fb"
COMMAND_CHAR_UUID: Final = "0000fff2-0000-1000-8000-00805f9b34fb"

CHANNELS: Final = ("red", "green", "blue", "uv")

# Share of the app's "total power" each channel uses at 100%, read off the app
# with one channel at a time. The total is a plain weighted sum capped at 100%.
POWER_WEIGHTS: Final = (0.39, 0.41, 0.53, 0.11)

FADE_MAX_HOURS: Final = 2.5

# Seconds of inactivity before dropping the BLE link, so the phone app can
# connect again (the light only accepts one connection).
DISCONNECT_DELAY: Final = 15
