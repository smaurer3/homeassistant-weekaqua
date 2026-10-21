"""Total power sensor, matching the app's readout."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import POWER_WEIGHTS
from .entity import WeekAquaEntity
from .protocol import power_used


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([TotalPowerSensor(entry, "total_power")])


class TotalPowerSensor(WeekAquaEntity, SensorEntity):
    _attr_translation_key = "total_power"
    _attr_icon = "mdi:lightning-bolt"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    @property
    def native_value(self) -> float | None:
        levels = self._controller.levels
        return None if levels is None else round(power_used(levels, POWER_WEIGHTS), 1)
