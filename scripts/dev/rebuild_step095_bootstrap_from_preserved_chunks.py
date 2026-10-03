from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "data/version_history.json"
PRIMARY = ROOT / "backups/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip"
SECOND = ROOT / "backups/second-copy/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip"
RESCUE_SHA = "f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2"
EXPECTED = {
    "P1A": ("Prompt-1A", "65fb561dfaf328b204bb86ef2a55789e835fa56cfab01d89f1c67a7b348a46c5"),
    "P1B": ("Prompt-1B", "7064081b9a264ba66da2c4eb297cc00f0f2d4133a97c84bed6f0171318d870cf"),
    "P1B1": ("Prompt-1B1", "a750b81cc0aa3b0fef5d6daaaaddddbae2be4c522ea4813784952f09eed26cc6"),
    "P1B2": ("Prompt-1B2", "12cc083ac1e107a2ffa4b10269b644df30f401ee3bd10a5fe42c9605c7b46576"),
    "P2": ("Prompt-2", "d972981dde11a5f07a76d8c9357c9ce2ae84ac2a52a6e06545936ca45c27ef98"),
    "P3": ("Prompt-3", "de7268db093be34156ccbdff04ada92956bc7469d75f222ec7bf3e5f19d77fc8"),
    "P4": ("Prompt-4", "a1bdb7c980de1aadd10e9492730892977e7a525d6dbbd5e8643ddec4da48b1c0"),
    "P5": ("Prompt-5", "bf0c0ea1dca1414794ad54a6c9f9d2a0617766706e55d366c2df081944fb2786"),
}
CHUNK_DIRS = [ROOT / "zz_REBUILD/chunks", ROOT / "zz_BOOTSTRAP/chunks"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str) -> bool:
    p = PurePosixPath(name.replace("\\", "/"))
    return not p.is_absolute() and ".." not in p.parts and not re.match(r"^[A-Za-z]:", name) and not name.startswith("//")


def decode_chunk_dir(path: Path) -> bytes | None:
    parts = sorted(path.glob("part*.b64"))
    if not parts:
        return None
    encoded = "".join("".join(p.read_text(encoding="ascii").split()) for p in parts)
    try:
        return base64.b64decode(encoded, validate=True)
    except Exception:
        return None


def find_verified_rescue(data: bytes, *, depth: int = 0, seen: set[str] | None = None) -> bytes | None:
    seen = seen or set()
    digest = sha(data)
    if digest in seen:
        return None
    seen.add(digest)
    if digest == RESCUE_SHA:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                if zf.testzip() is None:
                    return data
        except zipfile.BadZipFile:
            return None
    if depth >= 3:
        return None
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            if zf.testzip() is not None:
                return None
            for info in zf.infolist():
                if info.is_dir() or not safe_name(info.filename):
                    continue
                raw = zf.read(info)
                if sha(raw) == RESCUE_SHA:
                    try:
                        with zipfile.ZipFile(io.BytesIO(raw)) as nested:
                            if nested.testzip() is None:
                                return raw
                    except zipfile.BadZipFile:
                        pass
                if info.filename.lower().endswith((".zip", ".bin", ".dat")) or raw.startswith(b"PK\x03\x04"):
                    found = find_verified_rescue(raw, depth=depth + 1, seen=seen)
                    if found is not None:
                        return found
    except zipfile.BadZipFile:
        return None
    return None


def locate_rescue() -> tuple[bytes, str]:
    for chunk_dir in CHUNK_DIRS:
        decoded = decode_chunk_dir(chunk_dir)
        if decoded is None:
            continue
        found = find_verified_rescue(decoded)
        if found is not None:
            return found, str(chunk_dir.relative_to(ROOT)).replace("\\", "/")
    raise SystemExit("verified rescue ZIP f7ac13... not recoverable from preserved STEP 00 chunks")


def extract_exact_prompts(rescue: bytes) -> dict[str, bytes]:
    by_hash = {digest: pid for pid, (_, digest) in EXPECTED.items()}
    found: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(rescue)) as zf:
        if zf.testzip() is not None:
            raise SystemExit("verified rescue ZIP failed CRC")
        for info in zf.infolist():
            if info.is_dir() or not safe_name(info.filename):
                continue
            raw = zf.read(info)
            pid = by_hash.get(sha(raw))
            if pid:
                raw.decode("utf-8")
                previous = found.get(pid)
                if previous is not None and previous != raw:
                    raise SystemExit(f"ambiguous payload for {pid}")
                found[pid] = raw
    missing = sorted(set(EXPECTED) - set(found))
    if missing:
        raise SystemExit(f"verified rescue missing exact prompt payloads: {missing}")
    return found


def canonical_rel(pid: str) -> str:
    label = EXPECTED[pid][0]
    return f"prompts/V1/{label}/{label}_V1_R1.txt"


def candidate_canonical(payloads: dict[str, bytes]) -> bytes:
    doc = json.loads(CANONICAL.read_text(encoding="utf-8"))
    if doc.get("active_system") != "V1" or doc.get("active_snapshot") != "S001":
        raise SystemExit("unexpected canonical identity")
    if doc.get("app_data_revision") not in (1, 2):
        raise SystemExit("unexpected app_data_revision")
    # The backup captures the materialized, pre-completion state. Completion itself is recorded after ZIP verification.
    doc["app_data_revision"] = 2
    snapshot = next((s for s in doc.get("snapshots", []) if s.get("id") == "S001"), None)
    if not snapshot:
        raise SystemExit("S001 missing")
    snapshot["status"] = "BACKUP_REQUIRED"
    snapshot["backup_id"] = None
    doc["backups"] = []
    for pid, raw in payloads.items():
        rev = doc["prompts"][pid]["revisions"]["R1"]
        if sha(raw) != EXPECTED[pid][1] or rev.get("sha256") != EXPECTED[pid][1]:
            raise SystemExit(f"{pid}: hash contract mismatch")
        rev["file"] = canonical_rel(pid)
        rev["file_available"] = True
    return (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def build_bootstrap_zip(payloads: dict[str, bytes], source_chunk_dir: str) -> bytes:
    canonical = candidate_canonical(payloads)
    recovery_guide = (
        "# Prompt Action S001 Bootstrap Recovery\n\n"
        "This bootstrap backup exists only to close the historical baseline gap before STEP 10.\n"
        "Restore/rollback activation remains STEP 12 scope.\n"
        "Every Prompt R1 byte must match the protected STEP 00 SHA-256 map.\n"
    ).encode("utf-8")
    rescue_ref = json_bytes({
        "source": "Legacy V22.5.1 verified rescue",
        "sha256": RESCUE_SHA,
        "recovered_from_preserved_chunks": source_chunk_dir,
        "prompt_bytes_reconstructed": False,
    })
    entries: dict[str, bytes] = {
        "bootstrap/recovery-guide.md": recovery_guide,
        "bootstrap/rescue-source-reference.json": rescue_ref,
        "data/version_history.json": canonical,
    }
    for pid in EXPECTED:
        entries[canonical_rel(pid)] = payloads[pid]
    manifest = {
        "schema": "prompt-action-bootstrap-backup/v1",
        "system": "V1",
        "snapshot": "S001",
        "snapshot_status_at_backup": "BACKUP_REQUIRED",
        "rescue_source": {"name": "V22.5.1 verified rescue", "sha256": RESCUE_SHA},
        "canonical_sha256": sha(canonical),
        "composition": {pid: "R1" for pid in EXPECTED},
        "entries": [
            {"path": name, "size": len(raw), "sha256": sha(raw)}
            for name, raw in sorted(entries.items())
        ],
        "tool": {
            "name": "STEP 09.5 Baseline Materialization Bootstrap",
            "zip_format": "deflate-9",
            "deterministic_timestamp": "1980-01-01T00:00:00Z",
        },
    }
    entries["bootstrap/manifest.json"] = json_bytes(manifest)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, entries[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    raw_zip = out.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
        if zf.testzip() is not None or zf.namelist() != sorted(zf.namelist()):
            raise SystemExit("generated bootstrap ZIP verification failed")
    return raw_zip


def main() -> int:
    rescue, source = locate_rescue()
    if sha(rescue) != RESCUE_SHA:
        raise SystemExit("rescue SHA mismatch after recovery")
    payloads = extract_exact_prompts(rescue)
    bootstrap = build_bootstrap_zip(payloads, source)
    PRIMARY.parent.mkdir(parents=True, exist_ok=True)
    SECOND.parent.mkdir(parents=True, exist_ok=True)
    PRIMARY.write_bytes(bootstrap)
    SECOND.write_bytes(bootstrap)
    digest = sha(bootstrap)
    PRIMARY.with_suffix(PRIMARY.suffix + ".sha256").write_text(f"{digest}  {PRIMARY.name}\n", encoding="utf-8")
    SECOND.with_suffix(SECOND.suffix + ".sha256").write_text(f"{digest}  {SECOND.name}\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "rescue_sha256": RESCUE_SHA,
        "source_chunks": source,
        "prompt_count": len(payloads),
        "bootstrap_zip_sha256": digest,
        "bootstrap_zip_size": len(bootstrap),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
