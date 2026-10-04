from __future__ import annotations

import base64
import hashlib
import json
import struct
import subprocess
import zlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "d23512acd3ae9d6f4877e4d4873eb89b061289ef"
EXPECTED = {
    "P1A": "65fb561dfaf328b204bb86ef2a55789e835fa56cfab01d89f1c67a7b348a46c5",
    "P1B": "7064081b9a264ba66da2c4eb297cc00f0f2d4133a97c84bed6f0171318d870cf",
    "P1B1": "a750b81cc0aa3b0fef5d6daaaaddddbae2be4c522ea4813784952f09eed26cc6",
    "P1B2": "12cc083ac1e107a2ffa4b10269b644df30f401ee3bd10a5fe42c9605c7b46576",
    "P2": "d972981dde11a5f07a76d8c9357c9ce2ae84ac2a52a6e06545936ca45c27ef98",
    "P3": "de7268db093be34156ccbdff04ada92956bc7469d75f222ec7bf3e5f19d77fc8",
    "P4": "a1bdb7c980de1aadd10e9492730892977e7a525d6dbbd5e8643ddec4da48b1c0",
    "P5": "bf0c0ea1dca1414794ad54a6c9f9d2a0617766706e55d366c2df081944fb2786",
}


def show(path: str) -> str:
    return subprocess.check_output(["git", "show", f"{COMMIT}:{path}"], cwd=ROOT, text=True, encoding="utf-8")


def parse_local(raw: bytes):
    out = []
    pos = 0
    while pos + 30 <= len(raw) and raw[pos:pos+4] == b"PK\x03\x04":
        sig, ver, flags, method, mt, md, crc, csize, usize, nlen, xlen = struct.unpack_from("<IHHHHHIIIHH", raw, pos)
        ns = pos + 30
        ne = ns + nlen
        ds = ne + xlen
        de = ds + csize
        if de > len(raw):
            break
        name = raw[ns:ne].decode("utf-8", errors="replace")
        cdata = raw[ds:de]
        if method == zipfile.ZIP_STORED:
            data = cdata
        elif method == zipfile.ZIP_DEFLATED:
            data = zlib.decompress(cdata, -15)
        else:
            break
        if len(data) != usize or (zlib.crc32(data) & 0xFFFFFFFF) != crc:
            break
        out.append((name, data))
        pos = de
    return out, pos


def decode_joined(prefix: str, count: int):
    parts = ["".join(show(f"{prefix}/part{i:03d}.b64").split()) for i in range(1, count + 1)]
    joined = "".join(parts)
    try:
        return base64.b64decode(joined, validate=True), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}; compact_chars={len(joined)}; mod4={len(joined)%4}"


def main() -> int:
    report = {"sources": {}, "matches": {}, "missing": []}
    hashes = {}
    for prefix, count in (("zz_REBUILD/chunks", 9), ("zz_BOOTSTRAP/chunks", 3)):
        raw, err = decode_joined(prefix, count)
        src = {"decode_error": err}
        if raw is not None:
            entries, consumed = parse_local(raw)
            src.update({"decoded_bytes": len(raw), "decoded_sha256": hashlib.sha256(raw).hexdigest(), "crc_valid_complete_entries": len(entries), "consumed_bytes": consumed, "trailing_bytes": len(raw)-consumed})
            src["entry_names"] = [n for n, _ in entries]
            for name, data in entries:
                h = hashlib.sha256(data).hexdigest()
                hashes.setdefault(h, []).append({"source": prefix, "path": name, "size": len(data)})
        report["sources"][prefix] = src
    for pid, h in EXPECTED.items():
        if h in hashes:
            report["matches"][pid] = hashes[h]
        else:
            report["missing"].append(pid)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

# trigger: historical coverage diagnostic
