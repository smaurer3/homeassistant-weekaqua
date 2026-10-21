# Week Aqua for Home Assistant

Local Bluetooth control of Week Aqua M-series aquarium lights from Home Assistant. Tested on the **M800 Pro K** (four channels: red, green, blue, UV). The protocol was worked out from the WeekAqua app's Bluetooth traffic; no cloud account needed.

## What you get

| Entity | Does |
|---|---|
| Light | On/off, brightness and colour. Uses HA's RGBW colour mode with the "white" channel driving **UV**. Off sets every channel to 0; on restores the last mix. |
| Red / Green / Blue / UV | 0–100% sliders, one per channel. |
| Total power | The app's total-power figure: `0.39·R + 0.41·G + 0.53·B + 0.11·UV`. |
| On time / Off time | The light's built-in daily schedule. |
| Sunrise/sunset fade | Fade length for the schedule, 0–2.5 h in half-hour steps. |

Like the app, it won't let the total power go over 100%. A channel slider is capped at whatever budget the other channels leave. The light entity scales all channels down together, so the colour mix is kept.

It also sets the light's clock every time it connects, so the schedule runs on Home Assistant's time.

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
