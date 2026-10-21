# Week Aqua M800 Pro K — BLE protocol notes

Sources:
- HCI snoop captures of the WeekAqua app (`com.weekled.weekaquas`, 2026-10-21; raw logs not published): `red_full_snoop2` (red toggles), `batch2` (each channel 0/100), `batch3` (scale, power cap, scenes, schedule), `batch4_fade` (fade time).
- The decompiled app, v3.0.28. Its packet builder for this light is `tools/StringTools`, with the screens in the app's `old/` package.

## Device

- Public address `C8:47:81:xx:xx:xx`, name `B3.0-M800pro-02`, connectable.
- Advertisement: `02 01 06 | 03 03 F0 FF | 0B FF 57 46 00 01 C8 47 81 xx xx xx` → flags, service `0xFFF0`, manufacturer ID 18007 (`0x4657`, "WF") with data `00 01 <MAC>`.
- HA discovery matcher: `manufacturer_id: 18007` + `service_uuid: 0000fff0-…` (FFF0 alone is too common).
- The app treats the first two manufacturer-data bytes as a model code. `5747`–`5752` open newer models' screens; anything else, including this light's `5746`, opens the original 4-channel screens described here.
- Only advertises while nothing is connected. The phone app holds its connection in the background until force-stopped.
- TI CC254x module: exposes TI OAD service `F000FFC0-0451-4000-B000-000000000000`.
- Peripheral requests MTU 131; all commands fit in 8 bytes regardless.

## GATT table

| Handle | UUID | Props | Notes |
|---|---|---|---|
| 0x0001–0x0009 | 0x1800 GAP | | |
| 0x000A–0x000D | 0x1801 GATT | | |
| 0x000E–0x0013 | **0xFFF0** | | vendor service |
| 0x0010 | **0xFFF2** | write w/o response | **command channel**: every write goes here |
| 0x0012 | 0xFFF1 | read, notify | CCCD at 0x0013. The app never subscribes for this light (it only does for a different product line), so there is no state readback |
| 0x0014–0x0026 | 0x180A Device Info | read | manufacturer, model, serial, HW/FW/SW rev, system ID, PnP |
| 0x0027–0x002F | TI OAD | | firmware update, ignore |

## Programs

The light stores two programs and runs one of them:

- **Mode** (program slot 9): one set of channel levels plus a daily on/off window with sunrise/sunset fade. This is the app's "Mode setting" tab and the one in daily use.
- **Advanced** (slots 1–8): up to 8 time periods, each with its own start/end time and channel levels. This is the app's "Advanced setting" tab.

`FD F1` selects Mode and `FD F2` selects Advanced. The app re-sends whichever tab was last used every time it connects.

## Commands

All 8 bytes, written to 0x0010. Unused bytes are padded with `0x55`. Times are BCD (`20 45` = 20:45). Levels are `round(percent × 2.35)`, so 100% = `0xEB`.

| Bytes | Meaning | Confidence |
|---|---|---|
| `FF hh mm ss 55 55 55 55` | set clock | confirmed (captures + app) |
| `FD F1 55 55 55 55 55 55` | run the **Mode** program | app |
| `FD F2 55 55 55 55 55 55` | run the **Advanced** program | app |
| `FB Fn R G B UV 55 55` | channel levels for program slot n (9 = Mode, 1–8 = Advanced period) | confirmed for n = 9 |
| `FE F9 onH onM offH offM aon fade` | Mode on/off window, always-on flag and fade | confirmed |
| `FE Fn stH stM enH enM 55 55` | Advanced period n time range; 23:59 is sent as `24 00` | app |
| `F9 55 55 55 55 55 55 55` | sent right after the clock on every connect (hard-coded in the app) | purpose unknown |

### Channel levels

- Byte order R, G, B, UV. Checked at 1, 2, 3, 49, 50 and 100%.
- Every write carries all four channels.
- Dragging a slider streams a write every ~15–20 ms. A tap at either end sends one write.

### Mode schedule (`FE F9`)

- Changing off time 20:45 → 20:46 sent `FE F9 13 45 20 46 00 02`; on time 13:45 → 13:46 sent `FE F9 13 46 20 45 00 02`.
- **aon** (byte 6) is an always-on flag. `00` follows the schedule. `01` keeps the light on outside the scheduled hours, and changes nothing during them. `02` and `03` were tested and are ignored, both in and out of the scheduled hours. There's no "always off" value. The app flips this flag when you tap the centre of the schedule dial but shows nothing on screen, and the captures always had `00`.
- **fade** (byte 7) is the ramp time in 30-minute steps, `00`–`05` (0–2.5 h). The app writes it as `"0"` + one digit.

### Scenes

Scenes live in the app only; the preset level bytes are a table inside the app. Selecting one sends `FB F9` with its levels, then `FE F9` with the schedule. Saving a scene sends nothing.

| Scene | Bytes | R / G / B / UV % |
|---|---|---|
| Green (preset) | `6C E3 73 EB` | 46 / 97 / 49 / 100 |
| Colorful (preset) | `EB 5E 94 EB` | 100 / 40 / 63 / 100 |
| Standard (user custom) | `EB EB 57 00` | 100 / 100 / 37 / 0 |

Because the Mode program has only one set of levels, sending all zeros (an "off") also becomes what the schedule turns on to, until new levels are sent.

### Connect sequence

What the app does on connect: `FF` clock → `F9` → `FD F1`/`FD F2` (last-used tab), then the current program's data. In Mode: `FB F9` levels → `FD F1` → `FE F9` schedule. The app stays connected afterwards.

### Total power limit (app-side)

```
total = 0.39·R + 0.41·G + 0.53·B + 0.11·UV     (percentages, cap 100)
```

These exact weights appear in the app's code (applied to `byte / 235`). They also match readings taken from the app with each channel alone at 100%, and every combination observed:

| Mix (R/G/B/UV %) | Total | App |
|---|---|---|
| 100 / 100 / 0 / 0 | 80.0 | showed 80% |
| 100 / 100 / 37 / 0 | 99.6 | blue stopped at 37% |
| 100 / 74 / 48 / 5 | 95.3 | allowed |
| Green preset | 94.5 | allowed |
| Colorful preset | 99.8 | allowed |
| 0 / 100 / 100 / 100 | 105.0 | blocked |

Unknown whether the light also enforces this. The integration applies the same limit.

## Other models (not this light)

The app's builders for other Week Aqua models also use: `FC xx` (fan, level × 2.35), `F9 xx` (another fan setting, (100 − %) × 2.46), `FD F3`, `FD F4`, bare `FD`, and `F6 F1` / `F6 F2`. None of these are sent to this light.

## Open questions

- What the standalone `F9 55…` does on this model. On other models `F9 xx` is a fan setting.
- Advanced-program packets are taken from the app code only. Not yet captured from or tested on the light.
