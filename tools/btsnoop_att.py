"""
Decode GATT/ATT traffic from a standard btsnoop_hci.log (H4 datalink).

Usage:
  python btsnoop_att.py <btsnoop_hci.log | bugreport.zip> [peer_mac]

If given a bugreport zip, reads FS/data/log/bt/btsnoop_hci.log (Samsung)
or FS/data/misc/bluetooth/logs/btsnoop_hci.log (AOSP) from inside it.
Prints one line per ATT PDU on LE links, optionally filtered to one peer.
"""
import struct
import sys
import zipfile
from datetime import datetime, timedelta

BTSNOOP_EPOCH_DELTA_US = 0x00DCDDB30F2F8000
ZIP_PATHS = ("FS/data/log/bt/btsnoop_hci.log", "FS/data/misc/bluetooth/logs/btsnoop_hci.log")

ATT_OPS = {
    0x01: "ERROR_RSP", 0x02: "MTU_REQ", 0x03: "MTU_RSP",
    0x04: "FIND_INFO_REQ", 0x05: "FIND_INFO_RSP",
    0x08: "READ_BY_TYPE_REQ", 0x09: "READ_BY_TYPE_RSP",
    0x0A: "READ_REQ", 0x0B: "READ_RSP",
    0x10: "READ_BY_GROUP_REQ", 0x11: "READ_BY_GROUP_RSP",
    0x12: "WRITE_REQ", 0x13: "WRITE_RSP",
    0x1B: "NOTIFY", 0x1D: "INDICATE", 0x1E: "CONFIRM",
    0x52: "WRITE_CMD",
}


def load(path):
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path) as zf:
            names = set(zf.namelist())
            for p in ZIP_PATHS:
                if p in names:
                    return zf.read(p)
        raise SystemExit("no btsnoop_hci.log inside zip")
    with open(path, "rb") as f:
        return f.read()


def records(data):
    if data[:8] != b"btsnoop\x00":
        raise SystemExit("not a btsnoop file")
    version, datalink = struct.unpack(">II", data[8:16])
    if datalink != 1002:
        raise SystemExit(f"unsupported datalink {datalink}")
    pos = 16
    while pos + 24 <= len(data):
        orig, incl, flags, _drops, ts = struct.unpack(">IIIIq", data[pos:pos + 24])
        pos += 24
        yield flags, ts, data[pos:pos + incl]
        pos += incl


def fmt_mac(b):
    return ":".join(f"{x:02x}" for x in b[::-1])


def main():
    want = sys.argv[2].lower() if len(sys.argv) > 2 else None
    decode(load(sys.argv[1]), want)


def decode(data, want=None):
    peers = {}
    partial = {}
    t0 = None

    for flags, ts, pkt in records(data):
        if not pkt:
            continue
        when = datetime(1970, 1, 1) + timedelta(microseconds=ts - BTSNOOP_EPOCH_DELTA_US)
        if t0 is None:
            t0 = when
        h4 = pkt[0]

        if h4 == 0x04 and len(pkt) > 3 and pkt[1] == 0x3E and pkt[3] in (0x01, 0x0A):
            status, handle = pkt[4], struct.unpack("<H", pkt[5:7])[0]
            if status == 0:
                peers[handle] = fmt_mac(pkt[9:15])
                print(f"{when:%H:%M:%S.%f} CONNECT handle=0x{handle:04x} peer={peers[handle]}")
            continue
        if h4 == 0x04 and len(pkt) > 6 and pkt[1] == 0x05:
            handle = struct.unpack("<H", pkt[4:6])[0]
            print(f"{when:%H:%M:%S.%f} DISCONNECT handle=0x{handle:04x} reason=0x{pkt[6]:02x}")
            continue
        if h4 != 0x02 or len(pkt) < 5:
            continue

        hdr, _length = struct.unpack("<HH", pkt[1:5])
        handle, pb = hdr & 0x0FFF, (hdr >> 12) & 0x3
        direction = "RX" if flags & 1 else "TX"
        body = pkt[5:]
        key = (handle, direction)
        if pb == 0x01:
            if key not in partial:
                continue
            partial[key] += body
        else:
            partial[key] = body
        buf = partial[key]
        if len(buf) < 4:
            continue
        l2len, cid = struct.unpack("<HH", buf[:4])
        if len(buf) - 4 < l2len:
            continue
        del partial[key]
        if cid != 0x0004:
            continue

        peer = peers.get(handle, "?")
        if want and peer != want:
            continue
        att = buf[4:4 + l2len]
        op = att[0]
        name = ATT_OPS.get(op, f"OP_{op:02x}")
        detail = att[1:].hex()
        if op in (0x12, 0x52, 0x1B, 0x1D, 0x0A) and len(att) >= 3:
            attr = struct.unpack("<H", att[1:3])[0]
            detail = f"attr=0x{attr:04x} value={att[3:].hex()}"
        rel = (when - t0).total_seconds()
        print(f"{when:%H:%M:%S.%f} +{rel:8.3f} {direction} h=0x{handle:04x} {name:18s} {detail}")


if __name__ == "__main__":
    main()
