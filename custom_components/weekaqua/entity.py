"""Base entity for Week Aqua."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, MANUFACTURER
from .controller import WeekAquaController


class WeekAquaEntity(Entity):
    """Shares the light's assumed state and redraws when it changes."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, key: str | None) -> None:
        self._controller: WeekAquaController = entry.runtime_data
        address = entry.unique_id
        self._attr_unique_id = f"{address}_{key}" if key else address
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            connections={(CONNECTION_BLUETOOTH, address)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=entry.title,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._controller.async_add_listener(self.async_write_ha_state))
