"""Daily on/off schedule times."""
from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import WeekAquaEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([ScheduleTime(entry, "on_time"), ScheduleTime(entry, "off_time")])


class ScheduleTime(WeekAquaEntity, TimeEntity):
    _attr_assumed_state = True

    def __init__(self, entry: ConfigEntry, key: str) -> None:
        super().__init__(entry, key)
        self._key = key
        self._attr_translation_key = key

    @property
    def native_value(self) -> time:
        return getattr(self._controller, self._key)

    async def async_set_value(self, value: time) -> None:
        await self._controller.async_set_schedule(**{self._key: value})
