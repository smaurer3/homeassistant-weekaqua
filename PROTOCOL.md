# Week Aqua M800 Pro K — BLE protocol notes

Sources: HCI snoop captures (app `com.weekled.weekaquas`, 2026-10-21; raw logs not published):
`red_full_snoop2` (red toggles), `batch2` (each channel 0/100), `batch3` (scale, power cap, scenes, schedule), `batch4_fade` (fade time).

## Device

- Public address `C8:47:81:xx:xx:xx`, name `B3.0-M800pro-02`, connectable.
- Advertisement: `02 01 06 | 03 03 F0 FF | 0B FF 57 46 00 01 C8 47 81 xx xx xx` → flags, service `0xFFF0`, manufacturer ID 18007 (`0x4657`, "WF") with data `00 01 <MAC>`.
- HA discovery matcher: `manufacturer_id: 18007` + `service_uuid: 0000fff0-…` (FFF0 alone is too common).
- Only advertises while nothing is connected. The phone app holds its connection in the background until force-stopped.
- TI CC254x module: exposes TI OAD service `F000FFC0-0451-4000-B000-000000000000`.
- Peripheral requests MTU 131; all app commands fit in 8 bytes regardless.
- Four channels: Red, Green, Blue, UV. No power on/off control in the app.

## GATT table

| Handle | UUID | Props | Notes |
|---|---|---|---|
| 0x0001–0x0009 | 0x1800 GAP | | |
| 0x000A–0x000D | 0x1801 GATT | | |
| 0x000E–0x0013 | **0xFFF0** | | vendor service |
| 0x0010 | **0xFFF2** | write w/o response | **command channel**: every app write goes here |
| 0x0012 | 0xFFF1 | read, notify | CCCD at 0x0013; app never subscribes or reads |
| 0x0014–0x0026 | 0x180A Device Info | read | manufacturer, model, serial, HW/FW/SW rev, system ID, PnP |
| 0x0027–0x002F | TI OAD | | firmware update, ignore |

The app never reads state back, so an integration has to assume the state it last sent.

## Commands

All 8 bytes, written to 0x0010. Unused bytes are padded with `0x55`. Times are BCD (`20 45` = 20:45).

| Bytes | Meaning | Confidence |
|---|---|---|
| `FF hh mm ss 55 55 55 55` | set clock | confirmed (2 captures match phone time) |
| `FB F9 R G B UV 55 55` | set channel levels | confirmed |
| `FE F9 onH onM offH offM 00 fade` | set daily on/off schedule with sunrise/sunset fade | confirmed |
| `F9 55 55 55 55 55 55 55` | unknown, sent at connect | — |
| `FD F1 55 55 55 55 55 55` | unknown, sent twice at connect | — |

### Channel levels

- Byte = `round(percent × 2.35)`, so 100% = `0xEB`. Checked at 1, 2, 3, 49, 50 and 100%.
- Every write carries all four channels.
- Dragging a slider streams a write every ~15–20 ms. A tap at either end sends one write.

### Schedule

- Changing off time 20:45 → 20:46 sent `FE F9 13 45 20 46 00 02`; on time 13:45 → 13:46 sent `FE F9 13 46 20 45 00 02`.
- Last byte = fade (sunrise/sunset) time in 30-minute steps: 0 h → `00`, 0.5 → `01`, 1 → `02`, 1.5 → `03`, 2 → `04`, 2.5 → `05` (`batch4_fade`). App maximum seen is 2.5 h.
- Byte 6 has always been `00`.

### Scenes

Scenes live in the app only. Selecting one sends `FB F9` with its levels, then `FE F9` with the schedule. Saving a scene sends nothing.

| Scene | Bytes | R / G / B / UV % |
|---|---|---|
| Green (preset) | `6C E3 73 EB` | 46 / 97 / 49 / 100 |
| Colorful (preset) | `EB 5E 94 EB` | 100 / 40 / 63 / 100 |
| Standard (user custom) | `EB EB 57 00` | 100 / 100 / 37 / 0 |

### Connect sequence

`FF` clock → `F9` → `FD F1` → `FB F9` current levels → `FD F1` → `FE F9` schedule. The app stays connected afterwards.

### Total power limit (app-side)

The app shows a total power figure and stops sliders when it would pass 100%:

```
total = 0.39·R + 0.41·G + 0.53·B + 0.11·UV     (percentages, cap 100)
```

Weights read off the app with each channel alone at 100% (R 39, G 41, B 53, UV 11). The formula matches every combination observed:

| Mix (R/G/B/UV %) | Total | App |
|---|---|---|
| 100 / 100 / 0 / 0 | 80.0 | showed 80% |
| 100 / 100 / 37 / 0 | 99.6 | blue stopped at 37% |
| 100 / 74 / 48 / 5 | 95.3 | allowed |
| Green preset | 94.5 | allowed |
| Colorful preset | 99.8 | allowed |
| 0 / 100 / 100 / 100 | 105.0 | blocked |

Unknown whether the light also enforces this. The integration applies the same limit.

## Open questions

- `F9`, `FD F1`, and schedule byte 6 (always `00`).
- Whether `FB F9` sets only the live output or also the levels the schedule turns on to.
