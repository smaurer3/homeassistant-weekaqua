"""State for a Week Aqua light.

The light never reports anything back, so this holds what HA last sent and
persists it across restarts.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import time
import math

from bleak.exc import BleakError

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store

from .const import DOMAIN, POWER_WEIGHTS
from .device import WeekAquaDevice
from .protocol import clamp_to_power_limit, levels_packet, power_used, schedule_packet

STORAGE_VERSION = 1
DEFAULT_ON_TIME = time(8, 0)
DEFAULT_OFF_TIME = time(20, 0)
DEFAULT_FADE_HOURS = 1.0


class WeekAquaController:
    """Assumed state plus the commands that change it."""

    def __init__(self, hass: HomeAssistant, entry_id: str, device: WeekAquaDevice) -> None:
        self.device = device
        self._store: Store[dict] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}")
        self._listeners: list[Callable[[], None]] = []
        self.levels: tuple[float, ...] | None = None
        self.on_time = DEFAULT_ON_TIME
        self.off_time = DEFAULT_OFF_TIME
        self.fade_hours = DEFAULT_FADE_HOURS
        self.always_on = False
        self.clock_sync = True

    async def async_load(self) -> None:
        data = await self._store.async_load()
        if not data:
            return
        if data.get("levels") is not None:
            self.levels = tuple(data["levels"])
        self.on_time = time.fromisoformat(data.get("on_time", DEFAULT_ON_TIME.isoformat()))
        self.off_time = time.fromisoformat(data.get("off_time", DEFAULT_OFF_TIME.isoformat()))
        self.fade_hours = data.get("fade_hours", DEFAULT_FADE_HOURS)
        self.always_on = data.get("always_on", False)
        self.clock_sync = data.get("clock_sync", True)

    @callback
    def async_add_listener(self, update_callback: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(update_callback)
        return lambda: self._listeners.remove(update_callback)

    async def async_set_levels(self, levels: Sequence[float]) -> None:
        levels = clamp_to_power_limit([max(0.0, min(100.0, p)) for p in levels], POWER_WEIGHTS)
        await self._send(levels_packet(levels))
        self.levels = levels
        self._changed()

    async def async_set_channel(self, index: int, percent: float) -> None:
        """Change one channel, capping it at the power budget the others leave
        (the app stops the slider the same way)."""
        levels = list(self.levels or (0.0, 0.0, 0.0, 0.0))
        levels[index] = 0.0
        headroom = math.floor((100 - power_used(levels, POWER_WEIGHTS)) / POWER_WEIGHTS[index])
        levels[index] = max(0.0, min(percent, headroom))
        await self.async_set_levels(levels)

    async def async_set_schedule(
        self,
        on_time: time | None = None,
        off_time: time | None = None,
        fade_hours: float | None = None,
        always_on: bool | None = None,
    ) -> None:
        on_time = on_time or self.on_time
        off_time = off_time or self.off_time
        fade_hours = self.fade_hours if fade_hours is None else fade_hours
        always_on = self.always_on if always_on is None else always_on
        await self._send(schedule_packet(on_time, off_time, fade_hours, always_on))
        self.on_time, self.off_time, self.fade_hours = on_time, off_time, fade_hours
        self.always_on = always_on
        self._changed()

    @callback
    def set_clock_sync(self, enabled: bool) -> None:
        self.clock_sync = enabled
        self._changed()

    async def async_sync_clock(self) -> None:
        try:
            await self.device.sync_clock()
        except (BleakError, TimeoutError) as err:
            raise HomeAssistantError(f"Could not reach the Week Aqua light: {err}") from err

    async def _send(self, packet: bytes) -> None:
        try:
            await self.device.write(packet)
        except (BleakError, TimeoutError) as err:
            raise HomeAssistantError(f"Could not reach the Week Aqua light: {err}") from err

    def _changed(self) -> None:
        self._store.async_delay_save(self._data, 1)
        for update in list(self._listeners):
            update()

    def _data(self) -> dict:
        return {
            "levels": list(self.levels) if self.levels is not None else None,
            "on_time": self.on_time.isoformat(),
            "off_time": self.off_time.isoformat(),
            "fade_hours": self.fade_hours,
            "always_on": self.always_on,
            "clock_sync": self.clock_sync,
        }
