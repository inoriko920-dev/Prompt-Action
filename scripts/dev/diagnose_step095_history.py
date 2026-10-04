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


def show(path: str) -> str:
    return subprocess.check_output(["git", "show", f"{COMMIT}:{path}"], cwd=ROOT, text=True, encoding="utf-8")


def compact_part(prefix: str, idx: int) -> str:
    return "".join(show(f"{prefix}/part{idx:03d}.b64").split())


def decode_strict(text: str):
    try:
        return base64.b64decode(text, validate=True), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def decode_padded(text: str):
    padded = text + ("=" * ((-len(text)) % 4))
    try:
        return base64.b64decode(padded, validate=False), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def header_info(raw: bytes, pos: int) -> dict:
    info = {"offset": pos, "valid_header": False}
    if pos + 30 > len(raw) or raw[pos:pos + 4] != LOCAL:
        info["reason"] = "truncated_header"
        return info
    try:
        _sig, ver, flags, method, _mt, _md, crc, csize, usize, nlen, xlen = struct.unpack_from("<IHHHHHIIIHH", raw, pos)
    except struct.error:
        info["reason"] = "unpack_failed"
        return info
    ns = pos + 30
    ne = ns + nlen
    ds = ne + xlen
    if ne > len(raw):
        info.update({"reason": "truncated_name", "flags": flags, "method": method, "compressed_size": csize, "uncompressed_size": usize})
        return info
    name_bytes = raw[ns:ne]
    try:
        name = name_bytes.decode("utf-8")
    except UnicodeDecodeError:
        name = name_bytes.decode("cp437", errors="replace")
    info.update({
        "valid_header": True,
        "name": name,
        "version": ver,
        "flags": flags,
        "method": method,
        "crc32_header": f"{crc:08x}",
        "compressed_size": csize,
        "uncompressed_size": usize,
        "name_len": nlen,
        "extra_len": xlen,
        "data_offset": ds,
        "available_after_data_offset": max(0, len(raw) - ds),
        "expected_end": ds + csize if not (flags & 0x08) else None,
        "bytes_missing_if_fixed_size": max(0, ds + csize - len(raw)) if not (flags & 0x08) else None,
    })
    return info


def parse_entry_at(raw: bytes, pos: int):
    meta = header_info(raw, pos)
    if not meta.get("valid_header"):
        return None
    flags = meta["flags"]
    method = meta["method"]
    ds = meta["data_offset"]
    csize = meta["compressed_size"]
    usize = meta["uncompressed_size"]
    crc_header = int(meta["crc32_header"], 16)
    name = meta["name"]
    if method not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
        return None

    if not (flags & 0x08):
        de = ds + csize
        if de > len(raw):
            return None
        cdata = raw[ds:de]
        try:
            data = cdata if method == zipfile.ZIP_STORED else zlib.decompress(cdata, -15)
        except zlib.error:
            return None
        if len(data) != usize or (zlib.crc32(data) & 0xFFFFFFFF) != crc_header:
            return None
        return {"offset": pos, "name": name, "data": data, "end": de, "flags": flags, "method": method, "descriptor": False}

    if method != zipfile.ZIP_DEFLATED:
        return None
    obj = zlib.decompressobj(-15)
    try:
        data = obj.decompress(raw[ds:])
        data += obj.flush()
    except zlib.error:
        return None
    if not obj.eof:
        return None
    consumed = len(raw[ds:]) - len(obj.unused_data)
    de = ds + consumed
    tail = raw[de:]
    candidates = []
    if len(tail) >= 16 and tail[:4] == b"PK\x07\x08":
        crc, csz, usz = struct.unpack_from("<III", tail, 4)
        candidates.append((crc, csz, usz, de + 16))
    if len(tail) >= 12:
        crc, csz, usz = struct.unpack_from("<III", tail, 0)
        candidates.append((crc, csz, usz, de + 12))
    actual_crc = zlib.crc32(data) & 0xFFFFFFFF
    for crc, csz, usz, end in candidates:
        if crc == actual_crc and csz == consumed and usz == len(data):
            return {"offset": pos, "name": name, "data": data, "end": end, "flags": flags, "method": method, "descriptor": True}
    return None


def scan(raw: bytes):
    entries = []
    headers = []
    seen = set()
    start = 0
    while True:
        pos = raw.find(LOCAL, start)
        if pos < 0:
            break
        meta = header_info(raw, pos)
        entry = parse_entry_at(raw, pos)
        meta["crc_valid_complete_entry"] = entry is not None
        if entry is None and meta.get("valid_header") and meta.get("method") == zipfile.ZIP_DEFLATED:
            ds = meta["data_offset"]
            obj = zlib.decompressobj(-15)
            try:
                partial = obj.decompress(raw[ds:])
                meta["partial_inflate_bytes"] = len(partial)
                meta["inflate_eof"] = obj.eof
                meta["partial_sha256"] = hashlib.sha256(partial).hexdigest() if partial else None
            except zlib.error as exc:
                meta["inflate_error"] = str(exc)
        headers.append(meta)
        if entry is not None:
            key = (entry["name"], hashlib.sha256(entry["data"]).hexdigest())
            if key not in seen:
                seen.add(key)
                entries.append(entry)
        start = pos + 4
    return entries, headers


def add_candidate(candidates: list, label: str, raw: bytes | None, error: str | None, meta: dict):
    item = {"label": label, **meta, "decode_error": error}
    if raw is not None:
        entries, headers = scan(raw)
        item.update({
            "decoded_bytes": len(raw),
            "decoded_sha256": hashlib.sha256(raw).hexdigest(),
            "local_header_count": len(headers),
            "crc_valid_entries": len(entries),
            "entry_names": [e["name"] for e in entries],
            "invalid_or_incomplete_headers": [h for h in headers if not h.get("crc_valid_complete_entry")],
        })
        item["entries"] = entries
    candidates.append(item)


def source_candidates(prefix: str, count: int):
    parts = [compact_part(prefix, i) for i in range(1, count + 1)]
    candidates = []
    joined = "".join(parts)
    raw, err = decode_strict(joined)
    add_candidate(candidates, "joined_strict", raw, err, {"chars": len(joined), "mod4": len(joined) % 4})
    raw_parts = []
    all_parts_ok = True
    part_meta = []
    for idx, text in enumerate(parts, 1):
        r, e = decode_strict(text)
        mode = "strict"
        if r is None:
            r, e2 = decode_padded(text)
            mode = "padded"
            e = None if r is not None else f"strict={e}; padded={e2}"
        part_meta.append({"part": idx, "chars": len(text), "mod4": len(text) % 4, "ends_padding": text.endswith("="), "mode": mode, "error": e, "decoded_bytes": len(r) if r is not None else None})
        if r is None:
            all_parts_ok = False
        else:
            raw_parts.append(r)
            add_candidate(candidates, f"part_{idx:03d}_{mode}", r, e, {"part": idx, "chars": len(text), "mod4": len(text) % 4})
    if all_parts_ok:
        add_candidate(candidates, "decoded_parts_concatenated", b"".join(raw_parts), None, {"parts": count})
    return candidates, part_meta


def main() -> int:
    report = {"sources": {}, "matches": {}, "missing": []}
    by_hash = {}
    for prefix, count in (("zz_REBUILD/chunks", 9), ("zz_BOOTSTRAP/chunks", 3)):
        candidates, part_meta = source_candidates(prefix, count)
        clean_candidates = []
        for candidate in candidates:
            entries = candidate.pop("entries", [])
            for entry in entries:
                h = hashlib.sha256(entry["data"]).hexdigest()
                by_hash.setdefault(h, []).append({
                    "source": prefix,
                    "candidate": candidate["label"],
                    "offset": entry["offset"],
                    "path": entry["name"],
                    "size": len(entry["data"]),
                    "descriptor": entry["descriptor"],
                })
            clean_candidates.append(candidate)
        report["sources"][prefix] = {"parts": part_meta, "candidates": clean_candidates}
    for pid, h in EXPECTED.items():
        matches = by_hash.get(h, [])
        if matches:
            report["matches"][pid] = matches
        else:
            report["missing"].append(pid)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
