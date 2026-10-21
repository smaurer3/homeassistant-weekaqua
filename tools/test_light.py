"""
Connect to the light from a PC, print its Device Information, switch to 50%
blue for a few seconds, then set 100/100/37/0.

The WeekAqua app must be closed: the light only advertises while nothing is
connected to it.

Usage: python tools/test_light.py <light_mac>
"""
import asyncio
import sys

from bleak import BleakClient, BleakScanner

CMD_CHAR = "0000fff2-0000-1000-8000-00805f9b34fb"
DEVICE_INFO = {
    "manufacturer": "00002a29-0000-1000-8000-00805f9b34fb",
    "model": "00002a24-0000-1000-8000-00805f9b34fb",
    "serial": "00002a25-0000-1000-8000-00805f9b34fb",
    "hardware": "00002a27-0000-1000-8000-00805f9b34fb",
    "firmware": "00002a26-0000-1000-8000-00805f9b34fb",
    "software": "00002a28-0000-1000-8000-00805f9b34fb",
}


def level_byte(pct):
    return (pct * 235 + 50) // 100


def levels(r, g, b, uv):
    return bytes([0xFB, 0xF9, *(level_byte(p) for p in (r, g, b, uv)), 0x55, 0x55])


def show(raw):
    text = raw.decode("utf-8", "replace").strip("\x00")
    return text if text.isprintable() and text else raw.hex()


async def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    mac = sys.argv[1]
    print(f"Scanning for {mac} ...")
    device = await BleakScanner.find_device_by_address(mac, timeout=20)
    if device is None:
        raise SystemExit("Light not found. Is the WeekAqua app fully closed?")
    print(f"Found {device.name or '(no name)'}, connecting ...")

    async with BleakClient(device) as client:
        for name, uuid in DEVICE_INFO.items():
            try:
                print(f"  {name:12s} {show(await client.read_gatt_char(uuid))}")
            except Exception as e:
                print(f"  {name:12s} <{e}>")

        test = levels(0, 0, 50, 0)
        restore = levels(100, 100, 37, 0)
        print(f"Blue 50% only:     {test.hex(' ')}")
        await client.write_gatt_char(CMD_CHAR, test, response=False)
        await asyncio.sleep(4)
        print(f"Restore Standard:  {restore.hex(' ')}")
        await client.write_gatt_char(CMD_CHAR, restore, response=False)
        await asyncio.sleep(1)
    print("Done, disconnected.")


if __name__ == "__main__":
    asyncio.run(main())
