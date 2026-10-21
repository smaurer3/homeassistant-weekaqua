# Week Aqua for Home Assistant

Local Bluetooth control of Week Aqua M-series aquarium lights from Home Assistant. Tested on the **M800 Pro K** (four channels: red, green, blue, UV). The protocol was worked out from the WeekAqua app's Bluetooth traffic; no cloud account needed.

## What you get

| Entity | Does |
|---|---|
| Red / Green / Blue / UV | 0–100% sliders, one per channel. |
| Total power | The app's total-power figure: `0.39·R + 0.41·G + 0.53·B + 0.11·UV`. |
| On time / Off time | The light's built-in daily schedule. |
| Sunrise/sunset fade | Fade length for the schedule, 0–2.5 h in half-hour steps. |
| Periodic clock sync | On by default. Every 15 minutes it sets the light's clock and nothing else, so the schedule is back on time soon after a power cut. |

Like the app, it won't let the total power go over 100%. A slider is capped at whatever budget the other channels leave.

There's no on/off control, because the light has no off command. It follows its own daily schedule, just as with the app. To keep it dark, set a schedule that doesn't come on, the same way you would in the app.

These controls drive the app's **Mode** program, and the integration switches the light to Mode every time it connects. The app's **Advanced** program (up to 8 timed periods) isn't supported yet.

The light keeps a plain 24-hour clock with no timezone, set by whoever connects last. The integration sets it to Home Assistant's local time on every connection and with the periodic clock sync. The periodic sync sends only the clock. It doesn't switch programs or change levels, and it disconnects straight away so the phone app can still get in.

## Installation

### HACS

1. In HACS, open the menu → **Custom repositories**, add `https://github.com/smaurer3/homeassistant-weekaqua` with type **Integration**.
2. Download **Week Aqua** and restart Home Assistant.
3. The light should appear under **Settings → Devices & services → Discovered**. If it doesn't, use **Add integration → Week Aqua**.

### Manual

Copy `custom_components/weekaqua` into your Home Assistant `config/custom_components/` folder and restart.

## Things to know

- **Bluetooth range.** Home Assistant needs a Bluetooth adapter or an [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy.html) within reach of the light. It has worked at around -91 dBm with automatic retries, but closer is more reliable.
- **One connection at a time.** The light only advertises while nothing is connected to it. The WeekAqua app keeps its connection open in the background, so force-stop it if Home Assistant can't reach the light. The integration lets go 15 seconds after its last command, so the app can still be used.
- **Assumed state.** The light never reports what it's doing. Home Assistant shows what it last sent, so changes made in the app won't show up in HA.
- **Scenes** in the app are just saved channel levels; the light knows nothing about them. Use Home Assistant scenes instead.

## Protocol

[PROTOCOL.md](PROTOCOL.md) documents the GATT layout and every command. [`tools/`](tools/) has the scripts used to capture and decode the app's traffic from an Android bug report.
