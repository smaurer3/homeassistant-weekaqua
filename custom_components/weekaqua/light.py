"""Light entity for Week Aqua: brightness plus an R/G/B/UV mix (UV as "white")."""
from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGBW_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import WeekAquaEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([WeekAquaLight(entry, None)])


class WeekAquaLight(WeekAquaEntity, LightEntity):
    """Whole-light control. Brightness scales all four channels together."""

    _attr_name = None
    _attr_assumed_state = True
    _attr_color_mode = ColorMode.RGBW
    _attr_supported_color_modes = {ColorMode.RGBW}

    @property
    def is_on(self) -> bool | None:
        return self._controller.is_on

    @property
    def brightness(self) -> int | None:
        if not self.is_on:
            return None
        return round(max(self._controller.levels) * 255 / 100)

    @property
    def rgbw_color(self) -> tuple[int, int, int, int]:
        return _mix(self._controller.levels if self.is_on else self._controller.last_on_levels)

    async def async_turn_on(self, **kwargs: Any) -> None:
        if ATTR_BRIGHTNESS not in kwargs and ATTR_RGBW_COLOR not in kwargs:
            await self._controller.async_turn_on()
            return
        base = self._controller.levels if self.is_on else self._controller.last_on_levels
        mix = kwargs.get(ATTR_RGBW_COLOR, _mix(base))
        brightness = kwargs.get(ATTR_BRIGHTNESS, round(max(base) * 255 / 100) or 255)
        top = max(mix) or 1
        await self._controller.async_set_levels([c / top * brightness / 255 * 100 for c in mix])

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._controller.async_turn_off()


def _mix(levels: tuple[float, ...]) -> tuple[int, int, int, int]:
    top = max(levels) or 1
    return tuple(round(p / top * 255) for p in levels)
