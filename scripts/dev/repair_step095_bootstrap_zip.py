from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "data/version_history.json"
PRIMARY = ROOT / "backups/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip"
SECOND = ROOT / "backups/second-copy/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip"
EVIDENCE = ROOT / "docs/evidence/step095/archive_repair.json"
RESCUE_SHA = "f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2"
HISTORICAL_COMMIT = "d23512acd3ae9d6f4877e4d4873eb89b061289ef"
HISTORICAL_CHUNK_COUNT = 9
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


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def safe_name(name: str) -> bool:
    p = PurePosixPath(name.replace("\\", "/"))
    return not p.is_absolute() and ".." not in p.parts and not re.match(r"^[A-Za-z]:", name) and not name.startswith("//")


def expected_rel(prompt_id: str) -> str:
    label = EXPECTED[prompt_id][0]
    return f"prompts/V1/{label}/{label}_V1_R1.txt"


def normal_zip_payloads(path: Path) -> dict[str, bytes] | None:
    try:
        with zipfile.ZipFile(path) as zf:
            if zf.testzip() is not None:
                return None
            names = zf.namelist()
            if names != sorted(names) or len(names) != len(set(names)):
                return None
            if any(not safe_name(name) for name in names):
                return None
            return {name: zf.read(name) for name in names}
    except (zipfile.BadZipFile, OSError):
        return None


def git_show_text(spec: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "show", spec], cwd=ROOT, text=True, encoding="utf-8"
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"historical source unavailable: {spec}") from exc


def historical_snapshot_bytes() -> bytes:
    chunks = []
    for idx in range(1, HISTORICAL_CHUNK_COUNT + 1):
        spec = f"{HISTORICAL_COMMIT}:zz_REBUILD/chunks/part{idx:03d}.b64"
        text = git_show_text(spec)
        compact = "".join(text.split())
        if not compact:
            raise SystemExit(f"historical chunk is empty: {spec}")
        chunks.append(compact)
    encoded = "".join(chunks)
    try:
        return base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise SystemExit("historical snapshot base64 is invalid") from exc


def extract_exact_prompt_bytes(snapshot: bytes) -> tuple[dict[str, bytes], dict]:
    try:
        zf = zipfile.ZipFile(io.BytesIO(snapshot))
    except zipfile.BadZipFile as exc:
        raise SystemExit("historical zz_REBUILD payload is not a valid ZIP") from exc
    with zf:
        if zf.testzip() is not None:
            raise SystemExit("historical zz_REBUILD ZIP CRC failed")
        names = zf.namelist()
        if len(names) != len(set(names)) or any(not safe_name(name) for name in names):
            raise SystemExit("historical zz_REBUILD ZIP paths are unsafe or duplicated")
        by_hash: dict[str, list[tuple[str, bytes]]] = {}
        for name in names:
            if name.endswith("/"):
                continue
            raw = zf.read(name)
            by_hash.setdefault(sha_bytes(raw), []).append((name, raw))
        prompts: dict[str, bytes] = {}
        matched_paths: dict[str, str] = {}
        for pid, (_, expected_hash) in EXPECTED.items():
            matches = by_hash.get(expected_hash, [])
            if len(matches) != 1:
                raise SystemExit(f"{pid}: expected exactly one historical file with protected hash, got {len(matches)}")
            source_name, raw = matches[0]
            raw.decode("utf-8")
            prompts[pid] = raw
            matched_paths[pid] = source_name
        return prompts, {
            "historical_commit": HISTORICAL_COMMIT,
            "historical_snapshot_sha256": sha_bytes(snapshot),
            "historical_snapshot_size_bytes": len(snapshot),
            "historical_archive_members": len(names),
            "matched_paths": matched_paths,
        }


def make_precompletion_canonical() -> bytes:
    doc = json.loads(CANONICAL.read_text(encoding="utf-8"))
    if doc.get("active_system") != "V1" or doc.get("active_snapshot") != "S001":
        raise SystemExit("canonical identity changed; refusing STEP 09.5 recovery")
    if doc.get("app_data_revision") != 1:
        raise SystemExit("historical bootstrap recovery requires app_data_revision=1")
    if doc.get("backups") != []:
        raise SystemExit("historical bootstrap recovery requires no canonical backups yet")
    snap = doc.get("snapshots", [None])[0]
    if not isinstance(snap, dict) or snap.get("id") != "S001" or snap.get("status") != "BACKUP_REQUIRED" or snap.get("backup_id") is not None:
        raise SystemExit("S001 is not in the expected precompletion state")
    if doc.get("integrity", {}).get("legacy_rescue_sha256") != RESCUE_SHA:
        raise SystemExit("legacy rescue provenance changed")
    doc["app_data_revision"] = 2
    for pid, (_, expected_hash) in EXPECTED.items():
        prompt = doc.get("prompts", {}).get(pid)
        if not prompt or prompt.get("active_revision") != "R1" or set(prompt.get("revisions", {})) != {"R1"}:
            raise SystemExit(f"{pid}: canonical revision topology changed")
        rev = prompt["revisions"]["R1"]
        if rev.get("sha256") != expected_hash:
            raise SystemExit(f"{pid}: protected canonical hash changed")
        rev["file"] = expected_rel(pid)
        rev["file_available"] = True
    return json_bytes(doc)


def build_bootstrap_payloads(prompts: dict[str, bytes], provenance: dict) -> dict[str, bytes]:
    payloads: dict[str, bytes] = {}
    for pid, raw in prompts.items():
        payloads[expected_rel(pid)] = raw
    payloads["data/version_history.json"] = make_precompletion_canonical()
    payloads["bootstrap/recovery-guide.md"] = (
        "# Prompt Action V1 / S001 Bootstrap Recovery\n\n"
        "This archive contains exact protected Prompt bytes recovered from the historical GitHub snapshot.\n"
        "Validate bootstrap/manifest.json and SHA-256 values before restoring.\n"
        "The canonical state embedded here is pre-completion: S001 remains BACKUP_REQUIRED until this backup is verified.\n"
    ).encode("utf-8")
    payloads["bootstrap/rescue-source-reference.json"] = json_bytes({
        "legacy_rescue_sha256": RESCUE_SHA,
        "legacy_rescue_verified_evidence": "docs/evidence/step095/rescue_verification.json",
        "materialization_source": "historical_git_snapshot",
        **provenance,
    })
    entries = [
        {"path": name, "size": len(raw), "sha256": sha_bytes(raw)}
        for name, raw in sorted(payloads.items())
    ]
    manifest = {
        "format": "Prompt-Action bootstrap backup",
        "system": "V1",
        "snapshot": "S001",
        "composition": {pid: "R1" for pid in EXPECTED},
        "entries": entries,
    }
    payloads["bootstrap/manifest.json"] = json_bytes(manifest)
    return payloads


def verify_semantics(payloads: dict[str, bytes]) -> None:
    names = sorted(payloads)
    if any(not safe_name(name) for name in names):
        raise SystemExit("bootstrap ZIP contains unsafe path")
    manifest_raw = payloads.get("bootstrap/manifest.json")
    if manifest_raw is None:
        raise SystemExit("bootstrap manifest missing")
    manifest = json.loads(manifest_raw.decode("utf-8"))
    if manifest.get("system") != "V1" or manifest.get("snapshot") != "S001":
        raise SystemExit("bootstrap manifest identity mismatch")
    if manifest.get("composition") != {pid: "R1" for pid in EXPECTED}:
        raise SystemExit("bootstrap manifest composition mismatch")
    entries = manifest.get("entries", [])
    if not isinstance(entries, list) or not entries:
        raise SystemExit("bootstrap manifest entries missing")
    for entry in entries:
        name = entry.get("path")
        if not isinstance(name, str) or name not in payloads:
            raise SystemExit(f"manifest entry missing: {name}")
        raw = payloads[name]
        if len(raw) != entry.get("size") or sha_bytes(raw) != entry.get("sha256"):
            raise SystemExit(f"manifest entry hash mismatch: {name}")
    for pid, (_, expected_hash) in EXPECTED.items():
        raw = payloads.get(expected_rel(pid))
        if raw is None or sha_bytes(raw) != expected_hash:
            raise SystemExit(f"{pid}: protected Prompt hash mismatch in bootstrap")
        raw.decode("utf-8")
    embedded = json.loads(payloads["data/version_history.json"].decode("utf-8"))
    if embedded.get("app_data_revision") != 2 or embedded.get("backups") != []:
        raise SystemExit("embedded canonical precompletion state invalid")
    snap = embedded.get("snapshots", [None])[0]
    if not isinstance(snap, dict) or snap.get("status") != "BACKUP_REQUIRED" or snap.get("backup_id") is not None:
        raise SystemExit("embedded S001 must remain BACKUP_REQUIRED")


def write_deterministic_zip(path: Path, payloads: dict[str, bytes]) -> None:
    temp = path.with_suffix(path.suffix + ".repair.tmp")
    temp.unlink(missing_ok=True)
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(payloads):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            zf.writestr(info, payloads[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    final_payloads = normal_zip_payloads(temp)
    if final_payloads is None:
        temp.unlink(missing_ok=True)
        raise SystemExit("rebuilt bootstrap ZIP failed structural verification")
    verify_semantics(final_payloads)
    temp.replace(path)


def main() -> int:
    original_sha = sha_file(PRIMARY) if PRIMARY.is_file() else None
    existing = normal_zip_payloads(PRIMARY) if PRIMARY.is_file() else None
    mode = "existing_valid"
    provenance: dict = {}
    if existing is None:
        snapshot = historical_snapshot_bytes()
        prompts, provenance = extract_exact_prompt_bytes(snapshot)
        payloads = build_bootstrap_payloads(prompts, provenance)
        verify_semantics(payloads)
        PRIMARY.parent.mkdir(parents=True, exist_ok=True)
        write_deterministic_zip(PRIMARY, payloads)
        mode = "rebuilt_from_historical_exact_bytes"
    else:
        verify_semantics(existing)

    primary_sha = sha_file(PRIMARY)
    SECOND.parent.mkdir(parents=True, exist_ok=True)
    second_replaced = not SECOND.is_file() or sha_file(SECOND) != primary_sha
    if second_replaced:
        shutil.copy2(PRIMARY, SECOND)
    if sha_file(SECOND) != primary_sha:
        raise SystemExit("second copy is not byte-identical to primary")

    final_payloads = normal_zip_payloads(PRIMARY)
    if final_payloads is None:
        raise SystemExit("final primary bootstrap ZIP is invalid")
    verify_semantics(final_payloads)

    evidence = {
        "status": "PASS",
        "mode": mode,
        "original_primary_sha256": original_sha,
        "final_primary_sha256": primary_sha,
        "final_second_copy_sha256": sha_file(SECOND),
        "second_copy_replaced": second_replaced,
        "entry_count": len(final_payloads),
        "prompt_hashes_preserved": True,
        "prompt_bytes_reconstructed": False,
        "container_rebuilt": mode != "existing_valid",
        "legacy_rescue_sha256": RESCUE_SHA,
        **provenance,
    }
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
