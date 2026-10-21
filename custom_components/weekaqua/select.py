"""Experimental: raw value for byte 6 of the Mode schedule packet.

The app only sends 00 (follow the schedule) and 01 (stay on outside it).
Other values are offered to see whether the firmware understands more.
"""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import WeekAquaEntity

OPTIONS = ["00", "01", "02", "03"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([ScheduleTypeSelect(entry, "schedule_type")])


class ScheduleTypeSelect(WeekAquaEntity, SelectEntity):
    _attr_translation_key = "schedule_type"
    _attr_icon = "mdi:flask-outline"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = OPTIONS

    @property
    def current_option(self) -> str:
        return f"{self._controller.schedule_type:02X}"

    async def async_select_option(self, option: str) -> None:
        await self._controller.async_set_schedule(schedule_type=int(option, 16))
