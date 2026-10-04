from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "data/version_history.json"
PRIMARY = ROOT / "backups/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip"
SECOND = ROOT / "backups/second-copy/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip"
PRIMARY_SIDECAR = PRIMARY.with_suffix(PRIMARY.suffix + ".sha256")
SECOND_SIDECAR = SECOND.with_suffix(SECOND.suffix + ".sha256")
RECORD = ROOT / "backups/V1/S001/Prompt-Action-V1-S001-bootstrap-record.json"
EVIDENCE = ROOT / "docs/evidence/step095"
RESCUE_SHA = "f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2"
EXPECTED = {
    "P1A": ("Prompt-1A", "65fb561dfaf328b204bb86ef2a55789e835fa56cfab01d89f1c67a7b348a46c5"),
    "P1B": ("Prompt-1B", "7064081b9a264ba66da2c4eb297cc00f0f2d4133a97c84bed6f0171318d870cf"),
    "P1B1": ("Prompt-1B1", "a750b81cc0aa3b0fef5d6daaaaddddbae2be4c522ea4813784952f09eed26cc6"),
    "P1B2": ("Prompt-1B2", "12cc083ac1e107a2ffa4b10269b644df30f401ee3bd10a5fe42c9605c7b46576"),
    "P2": ("Prompt-2", "d972981dde11a5f07a76d8c9357c9ce2ae84ac2a52a6e06545936ca45c27ef98"),
    "P3": ("Prompt-3", "0aa955989b428700293a4d76793718bd33c78015f3b0021256a665dd386c3de1"),
    "P4": ("Prompt-4", "a1bdb7c980de1aadd10e9492730892977e7a525d6dbbd5e8643ddec4da48b1c0"),
    "P5": ("Prompt-5", "bf0c0ea1dca1414794ad54a6c9f9d2a0617766706e55d366c2df081944fb2786"),
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dump_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_zip_name(name: str) -> bool:
    p = PurePosixPath(name.replace("\\", "/"))
    return not p.is_absolute() and ".." not in p.parts and not re.match(r"^[A-Za-z]:", name) and not name.startswith("//")


def expected_rel(prompt_id: str) -> str:
    label = EXPECTED[prompt_id][0]
    return f"prompts/V1/{label}/{label}_V1_R1.txt"


def verify_bootstrap_zip(path: Path) -> tuple[str, dict, dict[str, bytes]]:
    if not path.is_file():
        raise SystemExit(f"bootstrap backup missing: {path}")
    zip_sha = sha_file(path)
    payloads: dict[str, bytes] = {}
    with zipfile.ZipFile(path) as zf:
        if zf.testzip() is not None:
            raise SystemExit("bootstrap backup CRC failed")
        names = zf.namelist()
        if names != sorted(names) or len(names) != len(set(names)):
            raise SystemExit("bootstrap ZIP order/uniqueness invalid")
        if any(not safe_zip_name(name) for name in names):
            raise SystemExit("bootstrap ZIP contains unsafe path")
        if "bootstrap/manifest.json" not in names:
            raise SystemExit("bootstrap manifest missing")
        manifest = json.loads(zf.read("bootstrap/manifest.json").decode("utf-8"))
        if manifest.get("system") != "V1" or manifest.get("snapshot") != "S001":
            raise SystemExit("bootstrap manifest identity mismatch")
        composition = manifest.get("composition")
        if composition is not None and composition != {pid: "R1" for pid in EXPECTED}:
            raise SystemExit("bootstrap manifest composition mismatch")
        entries = manifest.get("entries", [])
        if not isinstance(entries, list) or not entries:
            raise SystemExit("bootstrap manifest entries missing")
        for entry in entries:
            name = entry.get("path")
            if not isinstance(name, str) or name not in names:
                raise SystemExit(f"manifest entry missing: {name}")
            raw = zf.read(name)
            if len(raw) != entry.get("size") or sha_bytes(raw) != entry.get("sha256"):
                raise SystemExit(f"manifest entry hash mismatch: {name}")
        for pid, (_, expected_hash) in EXPECTED.items():
            rel = expected_rel(pid)
            if rel not in names:
                raise SystemExit(f"{pid}: exact canonical payload absent from bootstrap ZIP")
            raw = zf.read(rel)
            if sha_bytes(raw) != expected_hash:
                raise SystemExit(f"{pid}: bootstrap payload SHA mismatch")
            raw.decode("utf-8")
            payloads[pid] = raw
    return zip_sha, manifest, payloads


def validate_initial(doc: dict) -> None:
    if doc.get("app_data_revision") != 1:
        raise SystemExit("bootstrap requires app_data_revision=1")
    if doc.get("active_system") != "V1" or doc.get("active_snapshot") != "S001":
        raise SystemExit("bootstrap requires V1/S001")
    if [x.get("id") for x in doc.get("systems", [])] != ["V1"]:
        raise SystemExit("bootstrap cannot run after another System exists")
    if [x.get("id") for x in doc.get("snapshots", [])] != ["S001"]:
        raise SystemExit("bootstrap cannot run after another Snapshot exists")
    if doc.get("backups") != []:
        raise SystemExit("bootstrap requires empty backup list")
    snap = doc["snapshots"][0]
    if snap.get("status") != "BACKUP_REQUIRED" or snap.get("backup_id") is not None:
        raise SystemExit("S001 is not the expected bootstrap precondition")
    if doc.get("integrity", {}).get("legacy_rescue_sha256") != RESCUE_SHA:
        raise SystemExit("rescue provenance mismatch")
    if set(doc.get("prompts", {})) != set(EXPECTED):
        raise SystemExit("canonical prompt set differs from the verified eight")
    for pid, (_, expected_hash) in EXPECTED.items():
        prompt = doc["prompts"][pid]
        if prompt.get("active_revision") != "R1" or set(prompt.get("revisions", {})) != {"R1"}:
            raise SystemExit(f"{pid}: bootstrap expects only R1")
        rev = prompt["revisions"]["R1"]
        if rev.get("sha256") != expected_hash or rev.get("file") is not None or rev.get("file_available") is not False:
            raise SystemExit(f"{pid}: canonical precondition mismatch")


def verify_final(doc: dict) -> None:
    if doc.get("app_data_revision") != 2 or doc.get("active_system") != "V1" or doc.get("active_snapshot") != "S001":
        raise SystemExit("final canonical identity/revision invalid")
    snap = next((x for x in doc.get("snapshots", []) if x.get("id") == "S001"), None)
    if not snap or snap.get("status") != "COMPLETE" or snap.get("backup_id") != "B001":
        raise SystemExit("final S001 state invalid")
    if [x.get("id") for x in doc.get("systems", [])] != ["V1"] or [x.get("id") for x in doc.get("snapshots", [])] != ["S001"]:
        raise SystemExit("STEP 09.5 created forbidden System/Snapshot IDs")
    for pid, (_, expected_hash) in EXPECTED.items():
        prompt = doc["prompts"][pid]
        if set(prompt.get("revisions", {})) != {"R1"}:
            raise SystemExit(f"{pid}: STEP 09.5 created forbidden Revision")
        rev = prompt["revisions"]["R1"]
        target = ROOT / str(rev.get("file"))
        if rev.get("file_available") is not True or not target.is_file() or rev.get("sha256") != expected_hash or sha_file(target) != expected_hash:
            raise SystemExit(f"{pid}: final materialization invalid")


def main() -> int:
    primary_sha, manifest, payloads = verify_bootstrap_zip(PRIMARY)
    if not SECOND.is_file() or sha_file(SECOND) != primary_sha:
        raise SystemExit("second copy missing or not byte-identical to primary")

    doc = json.loads(CANONICAL.read_text(encoding="utf-8"))
    if doc.get("app_data_revision") == 2:
        verify_final(doc)
        print(json.dumps({"status": "PASS", "mode": "idempotent", "backup_sha256": primary_sha}, sort_keys=True))
        return 0
    validate_initial(doc)
    source_canonical_sha = sha_file(CANONICAL)

    # All verification above completed before any prompt/canonical mutation.
    for pid, raw in payloads.items():
        rel = expected_rel(pid)
        target = ROOT / rel
        if target.exists():
            raise SystemExit(f"refusing overwrite of existing prompt: {rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        if sha_file(target) != EXPECTED[pid][1]:
            raise SystemExit(f"{pid}: post-write hash mismatch")
        rev = doc["prompts"][pid]["revisions"]["R1"]
        rev["file"] = rel
        rev["file_available"] = True

    # Sidecars are derived from the actual, content-verified ZIP bytes.
    PRIMARY_SIDECAR.write_text(f"{primary_sha}  {PRIMARY.name}\n", encoding="utf-8")
    SECOND_SIDECAR.write_text(f"{primary_sha}  {SECOND.name}\n", encoding="utf-8")

    doc["app_data_revision"] = 2
    backup = {
        "id": "B001",
        "system": "V1",
        "snapshot": "S001",
        "status": "VALID",
        "verified": True,
        "second_copy_verified": True,
        "file": str(PRIMARY.relative_to(ROOT)).replace("\\", "/"),
        "sha256": primary_sha,
        "sha256_file": str(PRIMARY_SIDECAR.relative_to(ROOT)).replace("\\", "/"),
        "second_copy": str(SECOND.relative_to(ROOT)).replace("\\", "/"),
        "second_copy_sha256": primary_sha,
        "second_copy_sha256_file": str(SECOND_SIDECAR.relative_to(ROOT)).replace("\\", "/"),
        "manifest_path": "bootstrap/manifest.json",
        "bootstrap": True,
        "source_rescue_sha256": RESCUE_SHA,
        "created_at": "2026-10-03T00:00:00+07:00",
    }
    doc["backups"] = [backup]
    snap = doc["snapshots"][0]
    snap["status"] = "COMPLETE"
    snap["backup_id"] = "B001"

    temp = CANONICAL.with_suffix(".json.step095.tmp")
    temp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(CANONICAL)
    final = json.loads(CANONICAL.read_text(encoding="utf-8"))
    verify_final(final)

    dump_json(RECORD, backup)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    dump_json(EVIDENCE / "backup_verification.json", {
        "status": "PASS",
        "primary_sha256": primary_sha,
        "primary_size_bytes": PRIMARY.stat().st_size,
        "zip_crc": "PASS",
        "zip_paths": "PASS",
        "manifest": "PASS",
        "prompt_hashes": "PASS",
        "second_copy_sha256": primary_sha,
        "second_copy_verified": True,
    })
    dump_json(EVIDENCE / "bootstrap_transaction.json", {
        "status": "COMMITTED",
        "source_canonical_sha256": source_canonical_sha,
        "final_canonical_sha256": sha_file(CANONICAL),
        "backup_id": "B001",
        "snapshot": "S001",
        "final_snapshot_status": "COMPLETE",
    })
    dump_json(EVIDENCE / "allowed_canonical_diff.json", {
        "allowed_changes": [
            "app_data_revision 1 -> 2",
            "eight R1.file null -> canonical project-relative paths",
            "eight R1.file_available false -> true",
            "backups [] -> [B001]",
            "S001.backup_id null -> B001",
            "S001.status BACKUP_REQUIRED -> COMPLETE",
        ],
        "forbidden_changes_verified_absent": [
            "new System V", "new Snapshot S", "new Revision R", "protected baseline SHA mutation",
            "prompt byte reconstruction", "old history overwrite/delete",
        ],
        "prompt_hashes_unchanged": True,
        "prompt_bytes_reconstructed": False,
    })

    result = {
        "status": "PASS",
        "mode": "materialized",
        "prompt_count": 8,
        "backup_sha256": primary_sha,
        "active_system": "V1",
        "active_snapshot": "S001",
        "snapshot_status": "COMPLETE",
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
