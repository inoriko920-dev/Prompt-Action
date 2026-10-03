from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "docs/evidence/step095/bootstrap-source"
RESCUE_SHA256 = "f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2"
EXPECTED_PROMPTS = {
    "P1A": ("Prompt-1A-Pelajari-Sinopsis-dan-SRT-Full-Film.txt", "65fb561dfaf328b204bb86ef2a55789e835fa56cfab01d89f1c67a7b348a46c5", "prompts/V1/Prompt-1A/Prompt-1A_V1_R1.txt"),
    "P1B": ("Prompt-1B-Satu-Dokumen-Teknis-dan-Naskah-Bersih-Edit-Manual.txt", "7064081b9a264ba66da2c4eb297cc00f0f2d4133a97c84bed6f0171318d870cf", "prompts/V1/Prompt-1B/Prompt-1B_V1_R1.txt"),
    "P1B1": ("Prompt-1B1-Sinkronisasi-Naskah-Bersih-Dialog-Timestamp-dan-Penguncian.txt", "a750b81cc0aa3b0fef5d6daaaaddddbae2be4c522ea4813784952f09eed26cc6", "prompts/V1/Prompt-1B1/Prompt-1B1_V1_R1.txt"),
    "P1B2": ("Prompt-1B2-Identifikasi-Blok-Urutan-dan-Kepemilikan-Visual.txt", "12cc083ac1e107a2ffa4b10269b644df30f401ee3bd10a5fe42c9605c7b46576", "prompts/V1/Prompt-1B2/Prompt-1B2_V1_R1.txt"),
    "P2": ("Prompt-2-Eksekusi-Langsung-Satu-Jangkar.txt", "d972981dde11a5f07a76d8c9357c9ce2ae84ac2a52a6e06545936ca45c27ef98", "prompts/V1/Prompt-2/Prompt-2_V1_R1.txt"),
    "P3": ("Prompt-3-Eksekusi-Langsung-Satu-Narasi.txt", "de7268db093be34156ccbdff04ada92956bc7469d75f222ec7bf3e5f19d77fc8", "prompts/V1/Prompt-3/Prompt-3_V1_R1.txt"),
    "P4": ("Prompt-4-Gabung-dan-Audit-Satu-Blok.txt", "a1bdb7c980de1aadd10e9492730892977e7a525d6dbbd5e8643ddec4da48b1c0", "prompts/V1/Prompt-4/Prompt-4_V1_R1.txt"),
    "P5": ("Prompt-5-Finalisasi-Seluruh-Part.txt", "bf0c0ea1dca1414794ad54a6c9f9d2a0617766706e55d366c2df081944fb2786", "prompts/V1/Prompt-5/Prompt-5_V1_R1.txt"),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_create_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(path, flags, 0o644)
    try:
        with os.fdopen(fd, "wb", closefd=False) as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
    finally:
        os.close(fd)


def safe_zip_members(zf: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    infos = zf.infolist()
    seen: set[str] = set()
    for info in infos:
        raw = info.filename.replace("\\", "/")
        p = PurePosixPath(raw)
        if raw.startswith("/") or p.is_absolute() or ".." in p.parts:
            raise RuntimeError(f"unsafe archive path: {raw}")
        normalized = str(p)
        if normalized in seen:
            raise RuntimeError(f"duplicate archive path: {normalized}")
        seen.add(normalized)
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"symlink not allowed: {raw}")
        suffix = p.suffix.lower()
        if suffix in {".zip", ".7z", ".rar", ".tar", ".gz"}:
            raise RuntimeError(f"nested archive not allowed: {raw}")
    return infos


def read_source_zip() -> bytes:
    parts = sorted(SOURCE_DIR.glob("rescue.b64.part*"))
    if len(parts) != 6:
        raise RuntimeError(f"expected 6 rescue chunks, found {len(parts)}")
    encoded = "".join(path.read_text(encoding="utf-8").strip() for path in parts)
    data = base64.b64decode(encoded, validate=True)
    actual = sha256_bytes(data)
    if actual != RESCUE_SHA256:
        raise RuntimeError(f"rescue SHA mismatch: {actual}")
    return data


def locate_sources(zf: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    infos = safe_zip_members(zf)
    result: dict[str, zipfile.ZipInfo] = {}
    for prompt_id, (basename, expected_sha, _) in EXPECTED_PROMPTS.items():
        matches = [i for i in infos if PurePosixPath(i.filename.replace("\\", "/")).name == basename]
        if len(matches) != 1:
            raise RuntimeError(f"{prompt_id}: expected one source {basename}, found {len(matches)}")
        payload = zf.read(matches[0])
        actual = sha256_bytes(payload)
        if actual != expected_sha:
            raise RuntimeError(f"{prompt_id}: source hash mismatch {actual}")
        payload.decode("utf-8")
        result[prompt_id] = matches[0]
    return result


def validate_initial_canonical(doc: dict) -> None:
    if doc.get("active_system") != "V1" or doc.get("active_snapshot") != "S001":
        raise RuntimeError("bootstrap requires V1/S001")
    if doc.get("app_data_revision") != 1:
        raise RuntimeError("bootstrap requires app_data_revision=1")
    snapshots = [s for s in doc.get("snapshots", []) if isinstance(s, dict)]
    s001 = next((s for s in snapshots if s.get("id") == "S001"), None)
    if not s001 or s001.get("status") != "BACKUP_REQUIRED" or s001.get("backup_id") is not None:
        raise RuntimeError("S001 must be BACKUP_REQUIRED with no backup")
    if doc.get("backups") != []:
        raise RuntimeError("bootstrap requires no existing backups")
    if {s.get("id") for s in snapshots} != {"S001"}:
        raise RuntimeError("bootstrap must not run after later snapshots exist")
    if {s.get("id") for s in doc.get("systems", []) if isinstance(s, dict)} != {"V1"}:
        raise RuntimeError("bootstrap must not create/operate on V2+")
    prompts = doc.get("prompts", {})
    if set(prompts) != set(EXPECTED_PROMPTS):
        raise RuntimeError("canonical prompt set differs from expected eight prompts")
    for pid, (_, expected_sha, _) in EXPECTED_PROMPTS.items():
        p = prompts[pid]
        if p.get("active_revision") != "R1" or set(p.get("revisions", {})) != {"R1"}:
            raise RuntimeError(f"{pid}: bootstrap expects only R1")
        r1 = p["revisions"]["R1"]
        if r1.get("sha256") != expected_sha:
            raise RuntimeError(f"{pid}: canonical baseline hash mismatch")
        if r1.get("file_available") is not False or r1.get("file") is not None:
            raise RuntimeError(f"{pid}: baseline is already materialized; refusing rerun")


def deterministic_zip(path: Path, entries: dict[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".partial")
    if path.exists() or tmp.exists():
        raise RuntimeError(f"backup target already exists: {path}")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 3, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, entries[name])
    os.replace(tmp, path)


def verify_backup(path: Path, manifest: dict) -> dict:
    with zipfile.ZipFile(path, "r") as zf:
        infos = safe_zip_members(zf)
        names = [i.filename for i in infos]
        if names != sorted(names):
            raise RuntimeError("backup ZIP entry order is not deterministic")
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"CRC verification failed for {bad}")
        embedded = json.loads(zf.read("bootstrap/manifest.json").decode("utf-8"))
        if embedded != manifest:
            raise RuntimeError("embedded manifest mismatch")
        for item in manifest["entries"]:
            data = zf.read(item["path"])
            if len(data) != item["size"] or sha256_bytes(data) != item["sha256"]:
                raise RuntimeError(f"backup entry verification failed: {item['path']}")
        canonical_inside = json.loads(zf.read("data/version_history.json").decode("utf-8"))
        s001 = next(s for s in canonical_inside["snapshots"] if s["id"] == "S001")
        if s001["status"] != "BACKUP_REQUIRED" or canonical_inside["backups"] != []:
            raise RuntimeError("backup must contain pre-completion canonical state")
    return {"zip_sha256": sha256_file(path), "entry_count": len(names), "safe_paths": True, "crc": "PASS", "manifest": "PASS", "status": "PASS"}


def main() -> int:
    rescue_data = read_source_zip()
    with tempfile.TemporaryDirectory(prefix="step095-") as td:
        rescue_path = Path(td) / "rescue.zip"
        rescue_path.write_bytes(rescue_data)
        with zipfile.ZipFile(rescue_path, "r") as zf:
            sources = locate_sources(zf)
            source_bytes = {pid: zf.read(info) for pid, info in sources.items()}
            source_names = {pid: info.filename for pid, info in sources.items()}

    canonical_path = ROOT / "data/version_history.json"
    original_bytes = canonical_path.read_bytes()
    original_sha = sha256_bytes(original_bytes)
    doc = json.loads(original_bytes.decode("utf-8"))
    validate_initial_canonical(doc)

    materialized = json.loads(json.dumps(doc))
    materialized["app_data_revision"] = 2
    for pid, (_, expected_sha, rel) in EXPECTED_PROMPTS.items():
        target = ROOT / rel
        if target.exists():
            raise RuntimeError(f"refusing overwrite of materialized prompt: {rel}")
        data = source_bytes[pid]
        if sha256_bytes(data) != expected_sha:
            raise RuntimeError(f"{pid}: in-memory source hash mismatch")
        write_create_new(target, data)
        if sha256_file(target) != expected_sha:
            raise RuntimeError(f"{pid}: post-write hash mismatch")
        r1 = materialized["prompts"][pid]["revisions"]["R1"]
        r1["file"] = rel
        r1["file_available"] = True

    precompletion_bytes = json_bytes(materialized)
    precompletion_sha = sha256_bytes(precompletion_bytes)

    recovery_guide = (
        "# STEP 09.5 Bootstrap Recovery Guide\n\n"
        "This archive is the one-time V1/S001 bootstrap backup. Validate the ZIP SHA-256, reopen the archive, "
        "verify bootstrap/manifest.json, and verify every listed entry hash before any future restore workflow. "
        "Do not activate extracted data directly; STEP 12 owns restore/rollback.\n"
    ).encode("utf-8")
    rescue_ref = json_bytes({"source": "V22.5.1 rescue evidence", "sha256": RESCUE_SHA256, "bytes_embedded": False})

    entries: dict[str, bytes] = {"data/version_history.json": precompletion_bytes, "recovery/RECOVERY_GUIDE.md": recovery_guide, "bootstrap/rescue-source.json": rescue_ref}
    for pid, (_, _, rel) in EXPECTED_PROMPTS.items():
        entries[rel] = source_bytes[pid]
    manifest_entries = [{"path": name, "size": len(data), "sha256": sha256_bytes(data)} for name, data in sorted(entries.items())]
    manifest = {
        "schema": "prompt-action-step095-bootstrap-v1",
        "system": "V1",
        "snapshot": "S001",
        "snapshot_status_at_capture": "BACKUP_REQUIRED",
        "rescue_sha256": RESCUE_SHA256,
        "canonical_precompletion_sha256": precompletion_sha,
        "entries": manifest_entries,
    }
    entries["bootstrap/manifest.json"] = json_bytes(manifest)

    primary_rel = "backups/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip"
    primary = ROOT / primary_rel
    deterministic_zip(primary, entries)
    verify = verify_backup(primary, manifest)
    backup_sha = verify["zip_sha256"]
    sidecar_rel = primary_rel + ".sha256"
    sidecar = ROOT / sidecar_rel
    write_create_new(sidecar, f"{backup_sha}  {primary.name}\n".encode("utf-8"))

    second_rel = "backups/second-copy/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip"
    second_path = ROOT / second_rel
    second_path.parent.mkdir(parents=True, exist_ok=True)
    if second_path.exists():
        raise RuntimeError("refusing overwrite of second copy")
    shutil.copyfile(primary, second_path)
    with second_path.open("rb+") as f:
        f.flush()
        os.fsync(f.fileno())
    second_sha = sha256_file(second_path)
    if second_sha != backup_sha:
        raise RuntimeError("second-copy hash mismatch")
    second_sidecar_rel = second_rel + ".sha256"
    write_create_new(ROOT / second_sidecar_rel, f"{second_sha}  {second_path.name}\n".encode("utf-8"))
    second_verify = verify_backup(second_path, manifest)

    backup_record = {
        "id": "B001",
        "system": "V1",
        "snapshot": "S001",
        "status": "VALID",
        "verified": True,
        "second_copy_verified": True,
        "file": primary_rel,
        "sha256": backup_sha,
        "sha256_file": sidecar_rel,
        "second_copy": second_rel,
        "second_copy_sha256": second_sha,
        "second_copy_sha256_file": second_sidecar_rel,
        "manifest_path": "bootstrap/manifest.json",
        "bootstrap": True,
        "source_rescue_sha256": RESCUE_SHA256,
    }
    final_doc = json.loads(json.dumps(materialized))
    final_doc["backups"] = [backup_record]
    s001 = next(s for s in final_doc["snapshots"] if s["id"] == "S001")
    s001["status"] = "COMPLETE"
    s001["backup_id"] = "B001"
    if final_doc.get("active_snapshot") != "S001" or final_doc.get("active_system") != "V1":
        raise RuntimeError("bootstrap identity drift")
    if any("R2" in p.get("revisions", {}) for p in final_doc["prompts"].values()):
        raise RuntimeError("bootstrap unexpectedly created R2")
    if any(s.get("id") == "S002" for s in final_doc["snapshots"]):
        raise RuntimeError("bootstrap unexpectedly created S002")

    tmp = canonical_path.with_suffix(".json.step095.tmp")
    tmp.write_bytes(json_bytes(final_doc))
    with tmp.open("rb+") as f:
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, canonical_path)
    post_doc = json.loads(canonical_path.read_text(encoding="utf-8"))
    post_s001 = next(s for s in post_doc["snapshots"] if s["id"] == "S001")
    if post_s001.get("status") != "COMPLETE" or post_s001.get("backup_id") != "B001":
        raise RuntimeError("post-commit canonical verification failed")

    evidence_dir = ROOT / "docs/evidence/step095"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "rescue_verification.json").write_bytes(json_bytes({"status":"PASS","sha256":RESCUE_SHA256,"prompt_sources":{pid:{"archive_member":source_names[pid],"sha256":EXPECTED_PROMPTS[pid][1]} for pid in EXPECTED_PROMPTS}}))
    (evidence_dir / "backup_verification.json").write_bytes(json_bytes({"status":"PASS","primary":verify,"second_copy":second_verify,"second_copy_sha256":second_sha,"sidecar_sha256":sha256_file(sidecar)}))
    (evidence_dir / "bootstrap_transaction.json").write_bytes(json_bytes({"status":"COMMITTED","source_canonical_sha256":original_sha,"precompletion_canonical_sha256":precompletion_sha,"final_canonical_sha256":sha256_file(canonical_path),"backup_id":"B001","snapshot":"S001","final_snapshot_status":"COMPLETE"}))
    (evidence_dir / "allowed_canonical_diff.json").write_bytes(json_bytes({"allowed_changes":["app_data_revision 1 -> 2","R1.file null -> canonical project-relative path for eight prompts","R1.file_available false -> true for eight prompts","backups [] -> [B001]","S001.backup_id null -> B001","S001.status BACKUP_REQUIRED -> COMPLETE"],"forbidden_identity_changes":{"active_system":"V1","active_snapshot":"S001","new_system":False,"new_snapshot":False,"new_revision":False},"prompt_hashes_unchanged":True,"prompt_bytes_reconstructed":False}))
    changelog = ROOT / "docs/CHANGELOG.md"
    if not changelog.exists():
        changelog.write_text("# Prompt Action Changelog\n\n## STEP 09.5 — V1/S001 Bootstrap Completion\n- Materialized exact verified R1 prompt bytes from rescue evidence.\n- Created and independently verified primary + second-copy bootstrap backup.\n- Completed S001 without creating V2, S002, or R2.\n", encoding="utf-8")

    result = {"status":"PASS","rescue_sha256":RESCUE_SHA256,"prompt_count":8,"backup_sha256":backup_sha,"final_canonical_sha256":sha256_file(canonical_path),"snapshot":"S001","snapshot_status":"COMPLETE"}
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
