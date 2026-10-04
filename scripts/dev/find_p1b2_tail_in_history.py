from __future__ import annotations

import base64
import hashlib
import json
import re
import struct
import subprocess
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPSULE = ROOT / "docs/evidence/step095/exact_prompt_capsule"
TARGET_SHA = "12cc083ac1e107a2ffa4b10269b644df30f401ee3bd10a5fe42c9605c7b46576"
TARGET_SIZE = 19437
ENTRY_OFFSET = 24580
LOCAL_HEADER_LEN = 30


def run(*args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.check_output(args, cwd=ROOT, input=input_bytes)


def capsule_bytes() -> bytes:
    text = "".join(
        "".join(path.read_text(encoding="ascii").split())
        for path in sorted(CAPSULE.glob("part*.b64"))
    )
    return base64.b64decode(text, validate=True)


def parse_p1b2(raw: bytes) -> dict[str, int | str]:
    if raw[ENTRY_OFFSET:ENTRY_OFFSET + 4] != b"PK\x03\x04":
        raise SystemExit("P1B2 local header not found at protected capsule offset")
    (
        _sig,
        _ver,
        flags,
        method,
        _mtime,
        _mdate,
        crc32_expected,
        compressed_size,
        uncompressed_size,
        name_len,
        extra_len,
    ) = struct.unpack_from("<IHHHHHIIIHH", raw, ENTRY_OFFSET)
    name_start = ENTRY_OFFSET + LOCAL_HEADER_LEN
    name_end = name_start + name_len
    data_offset = name_end + extra_len
    name = raw[name_start:name_end].decode("utf-8")
    if flags & 0x08:
        raise SystemExit("P1B2 unexpectedly uses a data descriptor")
    if method != 8 or uncompressed_size != TARGET_SIZE:
        raise SystemExit("P1B2 ZIP header does not match expected deflate/size")
    return {
        "name": name,
        "flags": flags,
        "method": method,
        "crc32": crc32_expected,
        "compressed_size": compressed_size,
        "uncompressed_size": uncompressed_size,
        "data_offset": data_offset,
    }


def try_decode_base64(raw: bytes) -> list[tuple[str, bytes]]:
    variants: list[tuple[str, bytes]] = []
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        return variants
    compact = "".join(text.split())
    if not compact:
        return variants
    # Exact Base64-only blob.
    if re.fullmatch(r"[A-Za-z0-9+/=]+", compact):
        for label, candidate in (("strict", compact), ("padded", compact + "=" * ((-len(compact)) % 4))):
            try:
                decoded = base64.b64decode(candidate, validate=(label == "strict"))
            except Exception:
                continue
            variants.append((f"base64_{label}", decoded))
            if label == "strict":
                break
    # Also probe long Base64-looking runs embedded in text wrappers/logs.
    for idx, token in enumerate(re.findall(r"[A-Za-z0-9+/]{256,}={0,2}", text)):
        padded = token + "=" * ((-len(token)) % 4)
        try:
            decoded = base64.b64decode(padded, validate=False)
        except Exception:
            continue
        variants.append((f"embedded_base64_{idx}", decoded))
    return variants


def verify_tail(prefix: bytes, continuation: bytes, needed: int, expected_crc: int) -> tuple[bool, dict]:
    if len(continuation) < needed:
        return False, {}
    compressed = prefix + continuation[:needed]
    try:
        plain = zlib.decompress(compressed, -15)
    except zlib.error:
        return False, {}
    digest = hashlib.sha256(plain).hexdigest()
    crc = zlib.crc32(plain) & 0xFFFFFFFF
    ok = len(plain) == TARGET_SIZE and digest == TARGET_SHA and crc == expected_crc
    return ok, {
        "plain_size": len(plain),
        "sha256": digest,
        "crc32": f"{crc:08x}",
        "expected_crc32": f"{expected_crc:08x}",
    }


def main() -> int:
    cap = capsule_bytes()
    header = parse_p1b2(cap)
    data_offset = int(header["data_offset"])
    compressed_size = int(header["compressed_size"])
    prefix = cap[data_offset:]
    needed = compressed_size - len(prefix)
    if needed <= 0:
        raise SystemExit("P1B2 capsule is not truncated as expected")

    objects = run("git", "rev-list", "--objects", "--all").decode("utf-8", errors="replace").splitlines()
    oid_paths: dict[str, set[str]] = {}
    for line in objects:
        if not line.strip():
            continue
        oid, *rest = line.split(" ", 1)
        oid_paths.setdefault(oid, set())
        if rest:
            oid_paths[oid].add(rest[0])

    oids = list(oid_paths)
    batch = ("\n".join(oids) + "\n").encode()
    meta_lines = run(
        "git",
        "cat-file",
        "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        input_bytes=batch,
    ).decode().splitlines()
    sizes: dict[str, int] = {}
    for line in meta_lines:
        parts = line.split()
        if len(parts) == 3 and parts[1] == "blob":
            sizes[parts[0]] = int(parts[2])

    interesting_words = ("b64", "chunk", "capsule", "rescue", "bootstrap", "transfer", "prompt")
    tested_variants = 0
    tested_offsets = 0
    candidates_report: list[dict] = []
    matches: list[dict] = []

    for oid, size in sizes.items():
        paths = sorted(oid_paths.get(oid, set()))
        path_text = " ".join(paths).lower()
        # Keep search broad enough for renamed/deleted transfer pieces while
        # avoiding unrelated large binaries.
        if size > 2_000_000:
            continue
        if not any(word in path_text for word in interesting_words) and not (512 <= size <= 250_000):
            continue
        blob = run("git", "cat-file", "blob", oid)
        variants: list[tuple[str, bytes]] = [("raw_blob", blob)]
        variants.extend(try_decode_base64(blob))
        seen_variant_hashes: set[str] = set()
        for variant_name, candidate in variants:
            digest = hashlib.sha256(candidate).hexdigest()
            if digest in seen_variant_hashes:
                continue
            seen_variant_hashes.add(digest)
            tested_variants += 1
            if len(candidate) < needed:
                continue

            # Fast path: historical transfer chunk begins exactly at archive
            # offset 30000, which is the most likely continuation.
            ok, proof = verify_tail(prefix, candidate, needed, int(header["crc32"]))
            tested_offsets += 1
            if ok:
                matches.append({
                    "oid": oid,
                    "paths": paths,
                    "variant": variant_name,
                    "candidate_offset": 0,
                    "candidate_size": len(candidate),
                    "candidate_sha256": digest,
                    "proof": proof,
                })
                continue

            # Robust fallback: the continuation may be embedded inside a
            # larger historical blob. Scan every possible offset, but cap the
            # work per variant to keep CI deterministic.
            max_start = len(candidate) - needed
            if max_start > 300_000:
                max_start = 300_000
            found_here = False
            for offset in range(1, max_start + 1):
                ok, proof = verify_tail(prefix, candidate[offset:], needed, int(header["crc32"]))
                tested_offsets += 1
                if ok:
                    matches.append({
                        "oid": oid,
                        "paths": paths,
                        "variant": variant_name,
                        "candidate_offset": offset,
                        "candidate_size": len(candidate),
                        "candidate_sha256": digest,
                        "proof": proof,
                    })
                    found_here = True
                    break
            if found_here:
                continue

            if any(word in path_text for word in interesting_words):
                candidates_report.append({
                    "oid": oid,
                    "paths": paths[:12],
                    "variant": variant_name,
                    "size": len(candidate),
                    "sha256": digest,
                })

    report = {
        "capsule_size": len(cap),
        "p1b2_header": header,
        "compressed_prefix_bytes": len(prefix),
        "compressed_tail_bytes_needed": needed,
        "reachable_objects": len(oids),
        "tested_variants": tested_variants,
        "tested_offsets": tested_offsets,
        "matches": matches,
        "interesting_candidates_sample": candidates_report[:80],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if matches:
        print("P1B2_EXACT_TAIL_FOUND")
    else:
        print("P1B2_EXACT_TAIL_NOT_FOUND")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
