"""The Week Aqua integration."""
from __future__ import annotations

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady

from .controller import WeekAquaController
from .device import WeekAquaDevice

PLATFORMS: list[Platform] = [Platform.LIGHT, Platform.NUMBER, Platform.SENSOR, Platform.TIME]

WeekAquaConfigEntry = ConfigEntry[WeekAquaController]


async def async_setup_entry(hass: HomeAssistant, entry: WeekAquaConfigEntry) -> bool:
    """Set up a Week Aqua light from a config entry."""
    address = entry.unique_id
    ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
    if ble_device is None:
        raise ConfigEntryNotReady(
            f"Week Aqua light {address} not seen. Force-stop the WeekAqua app and "
            "check a Bluetooth proxy is in range."
        )

    device = WeekAquaDevice(ble_device)
    controller = WeekAquaController(hass, entry.entry_id, device)
    await controller.async_load()
    entry.runtime_data = controller

    @callback
    def _update_ble_device(service_info: BluetoothServiceInfoBleak, change: BluetoothChange) -> None:
        device.set_ble_device(service_info.device)

    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _update_ble_device,
            BluetoothCallbackMatcher(address=address, connectable=True),
            BluetoothScanningMode.PASSIVE,
        )
    )
    entry.async_on_unload(device.disconnect)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: WeekAquaConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
