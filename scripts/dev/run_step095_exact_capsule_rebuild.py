from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import struct
import subprocess
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/dev/rebuild_step095_bootstrap_from_preserved_chunks.py"
CAPSULE = ROOT / "docs/evidence/step095/exact_prompt_capsule"

spec = importlib.util.spec_from_file_location("step095_rebuild", SOURCE)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load STEP 09.5 rebuild module")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

LOCAL_SIG = b"PK\x03\x04"
P1B2_TAIL_BLOBS = (
    "9fe91437994c9339fc55c552cd947818539ac1dd",
    "9495e76ed055019d98dba979e1638622a44a69a9",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def add_match(raw: bytes, source: str, found: dict[str, bytes], provenance: dict[str, str]) -> None:
    pid = module.BY_HASH.get(sha(raw))
    if not pid:
        return
    raw.decode("utf-8")
    if pid in found and found[pid] != raw:
        raise SystemExit(f"ambiguous exact payload for {pid}")
    found[pid] = raw
    provenance[pid] = source


def inflate_entry(method: int, compressed: bytes) -> bytes:
    if method == 0:
        return compressed
    if method == 8:
        return zlib.decompress(compressed, -15)
    raise ValueError(f"unsupported ZIP method {method}")


def scan_local_entries(data: bytes, source: str, found: dict[str, bytes], provenance: dict[str, str]) -> list[dict[str, object]]:
    diagnostics: list[dict[str, object]] = []
    offset = 0
    while True:
        pos = data.find(LOCAL_SIG, offset)
        if pos < 0:
            break
        offset = pos + 1
        if pos + 30 > len(data):
            continue
        try:
            (_sig, _version, flags, method, _mtime, _mdate, crc_expected, compressed_size, uncompressed_size, name_len, extra_len) = struct.unpack_from(
                "<IHHHHHIIIHH", data, pos
            )
        except struct.error:
            continue
        name_start = pos + 30
        name_end = name_start + name_len
        payload_start = name_end + extra_len
        if name_end > len(data) or payload_start > len(data):
            continue
        try:
            name = data[name_start:name_end].decode("utf-8")
        except UnicodeDecodeError:
            continue
        if not module.safe_name(name):
            continue
        entry_diag: dict[str, object] = {
            "source": source,
            "offset": pos,
            "name": name,
            "flags": flags,
            "method": method,
            "compressed_size": compressed_size,
            "uncompressed_size": uncompressed_size,
        }
        if flags & 0x08:
            entry_diag["status"] = "SKIP_DATA_DESCRIPTOR"
            diagnostics.append(entry_diag)
            continue
        payload_end = payload_start + compressed_size
        if payload_end > len(data):
            entry_diag["status"] = "TRUNCATED"
            entry_diag["available_compressed_bytes"] = max(0, len(data) - payload_start)
            entry_diag["missing_compressed_bytes"] = payload_end - len(data)
            diagnostics.append(entry_diag)
            continue
        compressed = data[payload_start:payload_end]
        try:
            plain = inflate_entry(method, compressed)
        except Exception as exc:
            entry_diag["status"] = "DECOMPRESS_FAIL"
            entry_diag["error"] = type(exc).__name__
            diagnostics.append(entry_diag)
            continue
        crc_actual = zlib.crc32(plain) & 0xFFFFFFFF
        digest = sha(plain)
        entry_diag["actual_uncompressed_size"] = len(plain)
        entry_diag["crc_match"] = crc_actual == crc_expected
        entry_diag["sha256"] = digest
        if len(plain) == uncompressed_size and crc_actual == crc_expected:
            add_match(plain, f"{source}!/{name}", found, provenance)
            entry_diag["status"] = "PASS"
            entry_diag["protected_prompt_match"] = module.BY_HASH.get(digest)
        else:
            entry_diag["status"] = "VERIFY_FAIL"
        diagnostics.append(entry_diag)
    return diagnostics


def exact_capsule_bytes() -> bytes:
    parts = sorted(CAPSULE.glob("part*.b64"))
    if not parts:
        raise SystemExit("exact prompt capsule is missing")
    text = "".join("".join(path.read_text(encoding="ascii").split()) for path in parts)
    return base64.b64decode(text, validate=True)


def locate_p1b2_prefix(capsule: bytes) -> tuple[bytes, int, int, int, str]:
    marker = b"Prompt-1B2_V1_R1.txt"
    search = 0
    while True:
        pos = capsule.find(LOCAL_SIG, search)
        if pos < 0:
            break
        search = pos + 1
        if pos + 30 > len(capsule):
            continue
        (_sig, _version, flags, method, _mtime, _mdate, crc_expected, compressed_size, uncompressed_size, name_len, extra_len) = struct.unpack_from(
            "<IHHHHHIIIHH", capsule, pos
        )
        name_start = pos + 30
        name_end = name_start + name_len
        payload_start = name_end + extra_len
        if name_end > len(capsule) or payload_start > len(capsule):
            continue
        name_raw = capsule[name_start:name_end]
        if marker not in name_raw:
            continue
        name = name_raw.decode("utf-8")
        if flags & 0x08 or method != 8:
            raise SystemExit("P1B2 exact capsule header uses unsupported ZIP features")
        prefix = capsule[payload_start:]
        if len(prefix) >= compressed_size:
            raise SystemExit("P1B2 exact capsule unexpectedly contains a complete payload")
        return prefix, compressed_size, uncompressed_size, crc_expected, name
    raise SystemExit("P1B2 local header not found in exact prompt capsule")


def git_blob(oid: str) -> bytes:
    return subprocess.check_output(["git", "cat-file", "blob", oid], cwd=ROOT)


def decode_base64_blob(raw: bytes) -> bytes:
    text = "".join(raw.decode("ascii").split())
    return base64.b64decode(text, validate=True)


def recover_p1b2(found: dict[str, bytes], provenance: dict[str, str], diagnostics: list[dict[str, object]]) -> None:
    if "P1B2" in found:
        return
    capsule = exact_capsule_bytes()
    prefix, compressed_size, uncompressed_size, crc_expected, name = locate_p1b2_prefix(capsule)
    needed = compressed_size - len(prefix)
    target_sha = module.EXPECTED["P1B2"][1]
    candidates: list[tuple[int, str, bytes, int]] = []
    for oid in P1B2_TAIL_BLOBS:
        try:
            decoded = decode_base64_blob(git_blob(oid))
        except Exception as exc:
            diagnostics.append({"source": f"git-blob:{oid}", "status": "UNAVAILABLE", "error": type(exc).__name__})
            continue
        if len(decoded) < needed:
            continue
        for offset in range(0, len(decoded) - needed + 1):
            compressed = prefix + decoded[offset : offset + needed]
            try:
                plain = zlib.decompress(compressed, -15)
            except zlib.error:
                continue
            if len(plain) != uncompressed_size:
                continue
            digest = sha(plain)
            crc_actual = zlib.crc32(plain) & 0xFFFFFFFF
            if digest == target_sha and crc_actual == crc_expected:
                remainder = len(decoded) - (offset + needed)
                candidates.append((remainder, oid, plain, offset))
                diagnostics.append({
                    "source": f"git-blob:{oid}",
                    "status": "P1B2_EXACT_TAIL_MATCH",
                    "candidate_offset": offset,
                    "tail_bytes_used": needed,
                    "bytes_after_tail": remainder,
                    "sha256": digest,
                    "crc32": f"{crc_actual:08x}",
                    "entry_name": name,
                })
                break
    if not candidates:
        raise SystemExit("exact P1B2 compressed tail was not recoverable from verified Git history")
    candidates.sort(reverse=True, key=lambda item: item[0])
    _remainder, oid, plain, offset = candidates[0]
    add_match(plain, f"exact-capsule+git-blob:{oid}@{offset}", found, provenance)


def locate_exact_prompts() -> tuple[dict[str, bytes], dict[str, str], list[dict[str, object]]]:
    found: dict[str, bytes] = {}
    provenance: dict[str, str] = {}
    diagnostics: list[dict[str, object]] = []
    chunk_dirs = [CAPSULE, ROOT / "zz_REBUILD/chunks", ROOT / "zz_BOOTSTRAP/chunks"]
    for chunk_dir in chunk_dirs:
        rel = str(chunk_dir.relative_to(ROOT)).replace("\\", "/")
        for mode, decoded in module.chunk_candidates(chunk_dir):
            source = f"{rel}:{mode}"
            diagnostics.append({"source": source, "decoded_size": len(decoded), "sha256": sha(decoded)})
            module.collect_matches(decoded, source, found, provenance)
            diagnostics.extend(scan_local_entries(decoded, source, found, provenance))
    recover_p1b2(found, provenance, diagnostics)
    missing = sorted(set(module.EXPECTED) - set(found))
    if missing:
        raise SystemExit(f"exact protected Prompt bytes still missing after recovery: {missing}")
    for pid, raw in found.items():
        if sha(raw) != module.EXPECTED[pid][1]:
            raise SystemExit(f"{pid}: protected SHA proof failed")
        raw.decode("utf-8")
    return found, provenance, diagnostics


def main() -> int:
    payloads, provenance, diagnostics = locate_exact_prompts()
    bootstrap = module.build_bootstrap_zip(payloads, provenance)
    module.PRIMARY.parent.mkdir(parents=True, exist_ok=True)
    module.SECOND.parent.mkdir(parents=True, exist_ok=True)
    module.PRIMARY.write_bytes(bootstrap)
    module.SECOND.write_bytes(bootstrap)
    digest = sha(bootstrap)
    module.PRIMARY.with_suffix(module.PRIMARY.suffix + ".sha256").write_text(f"{digest}  {module.PRIMARY.name}\n", encoding="utf-8")
    module.SECOND.with_suffix(module.SECOND.suffix + ".sha256").write_text(f"{digest}  {module.SECOND.name}\n", encoding="utf-8")
    evidence = ROOT / "docs/evidence/step095/preserved_chunk_materialization.json"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(
        json.dumps({
            "status": "PASS",
            "verified_rescue_container_sha256_anchor": module.RESCUE_SHA,
            "proof": "each recovered Prompt byte stream exactly matches its protected STEP 00 SHA-256; local ZIP entries additionally require CRC/size verification",
            "prompt_hashes": {pid: module.EXPECTED[pid][1] for pid in module.EXPECTED},
            "provenance": provenance,
            "chunk_diagnostics": diagnostics,
            "prompt_bytes_reconstructed": False,
            "p1b2_tail_recovered_from_git_history": True,
            "bootstrap_zip_sha256": digest,
            "bootstrap_zip_size": len(bootstrap),
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "PASS",
        "prompt_count": len(payloads),
        "bootstrap_zip_sha256": digest,
        "bootstrap_zip_size": len(bootstrap),
        "provenance": provenance,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
