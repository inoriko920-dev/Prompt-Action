from __future__ import annotations

import base64
import hashlib
import json
import struct
import zlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPSULE = ROOT / "docs/evidence/step095/exact_prompt_capsule"
LOCAL = b"PK\x03\x04"
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
BY_HASH = {v: k for k, v in EXPECTED.items()}


def decode_capsule() -> bytes:
    text = "".join("".join(p.read_text(encoding="ascii").split()) for p in sorted(CAPSULE.glob("part*.b64")))
    return base64.b64decode(text, validate=True)


def scan(raw: bytes) -> list[dict]:
    out = []
    start = 0
    while True:
        pos = raw.find(LOCAL, start)
        if pos < 0:
            break
        item = {"offset": pos}
        if pos + 30 > len(raw):
            item["status"] = "truncated_header"
            out.append(item)
            break
        _sig, _ver, flags, method, _mt, _md, crc, csize, usize, nlen, xlen = struct.unpack_from("<IHHHHHIIIHH", raw, pos)
        ns = pos + 30
        ne = ns + nlen
        ds = ne + xlen
        name = raw[ns:ne].decode("utf-8", errors="replace") if ne <= len(raw) else "<truncated>"
        item.update({
            "name": name,
            "flags": flags,
            "method": method,
            "compressed_size": csize,
            "uncompressed_size": usize,
            "data_offset": ds,
            "available_from_data_offset": max(0, len(raw) - ds),
        })
        if flags & 0x08:
            item["status"] = "data_descriptor_not_scanned"
        else:
            de = ds + csize
            if de > len(raw):
                item["status"] = "truncated_payload"
                item["bytes_missing"] = de - len(raw)
                if method == zipfile.ZIP_DEFLATED and ds < len(raw):
                    obj = zlib.decompressobj(-15)
                    try:
                        partial = obj.decompress(raw[ds:])
                        item["partial_uncompressed_bytes"] = len(partial)
                        item["inflate_eof"] = obj.eof
                    except zlib.error as exc:
                        item["inflate_error"] = str(exc)
            else:
                cdata = raw[ds:de]
                try:
                    data = cdata if method == zipfile.ZIP_STORED else zlib.decompress(cdata, -15)
                    actual_crc = zlib.crc32(data) & 0xFFFFFFFF
                    digest = hashlib.sha256(data).hexdigest()
                    item.update({
                        "status": "PASS" if len(data) == usize and actual_crc == crc else "CRC_OR_SIZE_FAIL",
                        "actual_uncompressed_size": len(data),
                        "crc_match": actual_crc == crc,
                        "sha256": digest,
                        "protected_prompt_match": BY_HASH.get(digest),
                    })
                except Exception as exc:
                    item["status"] = "inflate_error"
                    item["error"] = str(exc)
        out.append(item)
        start = pos + 4
    return out


def main() -> int:
    raw = decode_capsule()
    report = {
        "decoded_bytes": len(raw),
        "decoded_sha256": hashlib.sha256(raw).hexdigest(),
        "starts_pk": raw.startswith(b"PK"),
        "entries": scan(raw),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
