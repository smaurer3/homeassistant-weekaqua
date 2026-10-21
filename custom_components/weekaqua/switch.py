"""Toggle for the periodic clock sync."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import WeekAquaEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([ClockSyncSwitch(entry, "clock_sync"), ScheduleTypeSwitch(entry, "schedule_type")])


class ClockSyncSwitch(WeekAquaEntity, SwitchEntity):
    """Re-send only the clock every CLOCK_SYNC_INTERVAL, so the light keeps
    the right time after a power cut."""

    _attr_translation_key = "clock_sync"
    _attr_icon = "mdi:clock-check-outline"
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool:
        return self._controller.clock_sync

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._controller.set_clock_sync(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._controller.set_clock_sync(False)


class ScheduleTypeSwitch(WeekAquaEntity, SwitchEntity):
    """Byte 6 of the Mode schedule packet. The app flips it when the centre of
    the schedule dial is tapped; its effect on the light is still unknown."""

    _attr_translation_key = "schedule_type"
    _attr_icon = "mdi:flask-outline"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_assumed_state = True

    @property
    def is_on(self) -> bool:
        return self._controller.schedule_type

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._controller.async_set_schedule(schedule_type=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._controller.async_set_schedule(schedule_type=False)
