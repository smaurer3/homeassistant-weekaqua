"""BLE connection to a Week Aqua light."""
from __future__ import annotations

import asyncio
import logging

from bleak.backends.device import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.util import dt as dt_util

from .const import COMMAND_CHAR_UUID, DISCONNECT_DELAY
from .protocol import clock_packet, connect_packets

_LOGGER = logging.getLogger(__name__)

# The app spaces its connect-time writes ~0.5 s apart.
PACKET_GAP = 0.3
# Writes are without-response, so give the last one time to leave before disconnecting.
FLUSH_DELAY = 1.0


class WeekAquaDevice:
    """Connects on demand and drops the link after DISCONNECT_DELAY idle."""

    def __init__(self, ble_device: BLEDevice) -> None:
        self._ble_device = ble_device
        self._client: BleakClientWithServiceCache | None = None
        self._lock = asyncio.Lock()
        self._idle_timer: asyncio.TimerHandle | None = None
        self._idle_task: asyncio.Task | None = None

    def set_ble_device(self, ble_device: BLEDevice) -> None:
        self._ble_device = ble_device

    async def write(self, packet: bytes) -> None:
        """Send a command. A new connection first gets the app's connect sequence,
        which also switches the light to the Mode program."""
        self._cancel_idle_timer()
        async with self._lock:
            try:
                client = await self._connect(connect_packets(dt_util.now()))
                await client.write_gatt_char(COMMAND_CHAR_UUID, packet, response=False)
            except Exception:
                await self._close()
                raise
        self._idle_timer = asyncio.get_running_loop().call_later(DISCONNECT_DELAY, self._on_idle)

    async def sync_clock(self) -> None:
        """Set the light's clock and nothing else, then drop the link straight away
        unless a command connection was already open."""
        async with self._lock:
            reusing = self._client is not None and self._client.is_connected
            try:
                client = await self._connect([])
                await client.write_gatt_char(COMMAND_CHAR_UUID, clock_packet(dt_util.now()), response=False)
                if not reusing:
                    await asyncio.sleep(FLUSH_DELAY)
                    await self._close()
            except Exception:
                await self._close()
                raise

    async def disconnect(self) -> None:
        self._cancel_idle_timer()
        async with self._lock:
            await self._close()

    async def _connect(self, prelude: list[bytes]) -> BleakClientWithServiceCache:
        """Return the open connection, or open one and send `prelude` on it."""
        if self._client is not None and self._client.is_connected:
            return self._client
        _LOGGER.debug("Connecting to %s", self._ble_device.address)
        client = await establish_connection(
            BleakClientWithServiceCache,
            self._ble_device,
            self._ble_device.name or self._ble_device.address,
            disconnected_callback=self._on_disconnected,
        )
        self._client = client
        for packet in prelude:
            await client.write_gatt_char(COMMAND_CHAR_UUID, packet, response=False)
            await asyncio.sleep(PACKET_GAP)
        return client

    async def _close(self) -> None:
        client, self._client = self._client, None
        if client is not None and client.is_connected:
            await client.disconnect()

    def _on_disconnected(self, client) -> None:
        if client is self._client:
            self._client = None

    def _on_idle(self) -> None:
        self._idle_timer = None
        self._idle_task = asyncio.get_running_loop().create_task(self.disconnect())

    def _cancel_idle_timer(self) -> None:
        if self._idle_timer is not None:
            self._idle_timer.cancel()
            self._idle_timer = None
