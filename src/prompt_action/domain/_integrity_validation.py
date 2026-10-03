from __future__ import annotations

from pathlib import Path, PureWindowsPath
import re
from typing import Any

from .models import Severity, ValidationReport

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha256_file(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_absolute_like(value: str) -> bool:
    return Path(value).is_absolute() or PureWindowsPath(value).is_absolute() or bool(re.match(r"^[A-Za-z]:[\\/]", value))


def _safe_relative_path(project_root: Path, value: str) -> tuple[bool, Path | None]:
    if _is_absolute_like(value):
        return False, None
    candidate = (project_root / value).resolve()
    try:
        candidate.relative_to(project_root.resolve())
    except ValueError:
        return False, candidate
    return True, candidate


def validate_file_integrity(project_root: Path, document: dict[str, Any], report: ValidationReport) -> None:
    prompts = document.get("prompts", {})
    if not isinstance(prompts, dict):
        return
    for prompt_id, prompt in prompts.items():
        if not isinstance(prompt, dict):
            continue
        revisions = prompt.get("revisions", {})
        if not isinstance(revisions, dict):
            continue
        for revision_id, revision in revisions.items():
            if not isinstance(revision, dict):
                continue
            entity = f"{prompt_id}:{revision_id}"
            file_value = revision.get("file")
            sha_value = revision.get("sha256")
            available = revision.get("file_available")
            path_prefix = f"prompts.{prompt_id}.revisions.{revision_id}"
            candidate: Path | None = None
            if file_value is not None and not isinstance(file_value, str):
                report.add("SCHEMA-FILE-PATH", Severity.BLOCKING, entity, f"{path_prefix}.file", "Revision file must be a relative string path or null.")
                continue
            if isinstance(file_value, str):
                safe, candidate = _safe_relative_path(project_root, file_value)
                if not safe:
                    report.add("POLICY-ABSOLUTE-PATH", Severity.BLOCKING, entity, f"{path_prefix}.file", "Canonical history may contain only project-relative paths.")
                    candidate = None
            if sha_value is not None and (not isinstance(sha_value, str) or SHA256_RE.fullmatch(sha_value) is None):
                report.add("SCHEMA-SHA256", Severity.BLOCKING, entity, f"{path_prefix}.sha256", "sha256 must be lowercase 64-hex or null.")
            if available is True:
                if not isinstance(file_value, str) or not file_value:
                    report.add("INV-10", Severity.BLOCKING, entity, f"{path_prefix}.file", "file_available=true requires a relative file path.")
                    continue
                if not isinstance(sha_value, str) or SHA256_RE.fullmatch(sha_value) is None:
                    report.add("INV-10", Severity.BLOCKING, entity, f"{path_prefix}.sha256", "file_available=true requires a valid lowercase SHA-256.")
                    continue
                if candidate is None or not candidate.is_file():
                    report.add("INV-10", Severity.BLOCKING, entity, f"{path_prefix}.file", "file_available=true but the physical file does not exist.")
                    continue
                actual = _sha256_file(candidate)
                if actual != sha_value:
                    report.add("INV-10-SHA-MISMATCH", Severity.BLOCKING, entity, f"{path_prefix}.sha256", f"SHA-256 mismatch: expected {sha_value}, actual {actual}.")
            elif available is not False:
                report.add("SCHEMA-FILE-AVAILABLE", Severity.BLOCKING, entity, f"{path_prefix}.file_available", "file_available must be boolean.")

    for index, legacy in enumerate(document.get("legacy_sources", [])):
        if not isinstance(legacy, dict):
            continue
        source_path = legacy.get("source_path")
        if isinstance(source_path, str) and source_path:
            safe, _ = _safe_relative_path(project_root, source_path)
            if not safe:
                report.add("POLICY-ABSOLUTE-PATH", Severity.BLOCKING, str(legacy.get("id", index)), f"legacy_sources[{index}].source_path", "Legacy source_path must be project-relative.")


def validate_policy(document: dict[str, Any], report: ValidationReport) -> None:
    backups = {
        item.get("id"): item for item in document.get("backups", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    policy = document.get("release_policy", {})
    require_backup = bool(policy.get("require_backup_for_complete", True))
    require_second_copy = bool(policy.get("require_second_copy", True))
    for snapshot in document.get("snapshots", []):
        if not isinstance(snapshot, dict) or snapshot.get("status") != "COMPLETE" or not require_backup:
            continue
        snapshot_id = str(snapshot.get("id"))
        backup_id = snapshot.get("backup_id")
        backup = backups.get(backup_id)
        if not isinstance(backup, dict):
            report.add("INV-11", Severity.BLOCKING, snapshot_id, f"snapshots.{snapshot_id}.backup_id", "COMPLETE snapshot requires an existing valid backup.")
            continue
        valid = backup.get("status") == "VALID" and backup.get("verified") is True
        if require_second_copy:
            valid = valid and backup.get("second_copy_verified") is True
        if not valid:
            report.add("INV-11", Severity.BLOCKING, snapshot_id, f"backups.{backup_id}", "COMPLETE snapshot backup does not satisfy release policy.")
