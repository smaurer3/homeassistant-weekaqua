"""
Pull a bug report, save the full btsnoop_hci.log from it, and print the GATT
traffic to the light.

Needs Developer options > Enable Bluetooth HCI snoop log = Enabled, followed
by a reboot (the quick-settings Bluetooth toggle doesn't restart the stack).

Usage: python capture_snoop.py <label> [light_mac]
Writes captures/<label>/btsnoop_hci.log. Without light_mac, prints ATT
traffic for every LE connection.
"""
import os
import subprocess
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from btsnoop_att import ZIP_PATHS, decode


def main():
    label = sys.argv[1]
    peer = sys.argv[2].lower() if len(sys.argv) > 2 else None
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(project_root, "captures", label)
    os.makedirs(out_dir, exist_ok=True)

    zip_path = os.path.join(out_dir, "bugreport.zip")
    subprocess.run(["adb", "bugreport", zip_path], check=True)

    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        member = next((p for p in ZIP_PATHS if p in names), None)
        if member is None:
            raise SystemExit("bug report has no btsnoop_hci.log - is full snoop logging on and the phone rebooted since?")
        data = zf.read(member)

    log_path = os.path.join(out_dir, "btsnoop_hci.log")
    with open(log_path, "wb") as f:
        f.write(data)
    os.remove(zip_path)
    print(f"Saved {log_path} ({len(data)} bytes)\n")
    decode(data, peer)


if __name__ == "__main__":
    main()
