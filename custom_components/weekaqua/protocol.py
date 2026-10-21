"""Week Aqua M-series BLE command encoding. See PROTOCOL.md in the repo."""
from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, time

PAD = 0x55
LEVEL_MAX = 235


def _bcd(value: int) -> int:
    return (value // 10) << 4 | value % 10


def level_byte(percent: float) -> int:
    return max(0, min(LEVEL_MAX, int(percent * LEVEL_MAX / 100 + 0.5)))


def clock_packet(now: datetime) -> bytes:
    return bytes([0xFF, _bcd(now.hour), _bcd(now.minute), _bcd(now.second), PAD, PAD, PAD, PAD])


def connect_packets(now: datetime) -> list[bytes]:
    """What the app sends straight after connecting. F9 and FD F1 are of
    unknown purpose and replayed as-is."""
    return [
        clock_packet(now),
        bytes([0xF9, PAD, PAD, PAD, PAD, PAD, PAD, PAD]),
        bytes([0xFD, 0xF1, PAD, PAD, PAD, PAD, PAD, PAD]),
    ]


def levels_packet(levels: Sequence[float]) -> bytes:
    return bytes([0xFB, 0xF9, *(level_byte(p) for p in levels), PAD, PAD])


def schedule_packet(on: time, off: time, fade_hours: float, always_on: bool = False) -> bytes:
    """Byte 6: 00 follows the schedule, 01 keeps the light on outside it."""
    return bytes([
        0xFE, 0xF9,
        _bcd(on.hour), _bcd(on.minute),
        _bcd(off.hour), _bcd(off.minute),
        0x01 if always_on else 0x00, round(fade_hours * 2),
    ])


def power_used(levels: Sequence[float], weights: Sequence[float]) -> float:
    return sum(p * w for p, w in zip(levels, weights))


def clamp_to_power_limit(levels: Sequence[float], weights: Sequence[float]) -> tuple[float, ...]:
    used = power_used(levels, weights)
    if used <= 100:
        return tuple(levels)
    return tuple(p * 100 / used for p in levels)
