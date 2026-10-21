"""Per-channel level sliders and the sunrise/sunset fade."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CHANNELS, FADE_MAX_HOURS
from .entity import WeekAquaEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    entities: list[NumberEntity] = [ChannelNumber(entry, index) for index in range(len(CHANNELS))]
    entities.append(FadeNumber(entry, "fade"))
    async_add_entities(entities)


class ChannelNumber(WeekAquaEntity, NumberEntity):
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER
    _attr_assumed_state = True

    def __init__(self, entry: ConfigEntry, index: int) -> None:
        super().__init__(entry, CHANNELS[index])
        self._index = index
        self._attr_translation_key = CHANNELS[index]

    @property
    def native_value(self) -> float | None:
        levels = self._controller.levels
        return None if levels is None else round(levels[self._index], 1)

    async def async_set_native_value(self, value: float) -> None:
        await self._controller.async_set_channel(self._index, value)


class FadeNumber(WeekAquaEntity, NumberEntity):
    _attr_translation_key = "fade"
    _attr_native_min_value = 0
    _attr_native_max_value = FADE_MAX_HOURS
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_mode = NumberMode.BOX
    _attr_assumed_state = True

    @property
    def native_value(self) -> float:
        return self._controller.fade_hours

    async def async_set_native_value(self, value: float) -> None:
        await self._controller.async_set_schedule(fade_hours=value)
