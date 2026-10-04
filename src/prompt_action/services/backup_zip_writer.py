from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import zipfile

from prompt_action.domain.errors import BackupWorkflowError
from prompt_action.services.backup_planner import BackupEntryPlan, BackupPlan

_FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
_RESERVED_WINDOWS = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def validate_zip_entry_name(name: str) -> str:
    if not isinstance(name, str) or not name or "\x00" in name:
        raise BackupWorkflowError("UNSAFE_ZIP_PATH", "ZIP entry path is empty or contains NUL")
    normalized = name.replace("\\", "/")
    if normalized.startswith("/") or normalized.startswith("//") or re.match(r"^[A-Za-z]:", normalized):
        raise BackupWorkflowError("UNSAFE_ZIP_PATH", f"Absolute/drive ZIP path rejected: {name}")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise BackupWorkflowError("UNSAFE_ZIP_PATH", f"Unsafe ZIP path rejected: {name}")
    for part in pure.parts:
        stem = part.split(".", 1)[0].upper()
        if stem in _RESERVED_WINDOWS:
            raise BackupWorkflowError("UNSAFE_ZIP_PATH", f"Reserved device ZIP path rejected: {name}")
    return pure.as_posix()


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(filename=validate_zip_entry_name(name), date_time=_FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (0o100644 & 0xFFFF) << 16
    info.flag_bits &= ~0x1
    return info


class BackupZipWriter:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()

    def _stream_entry(self, archive: zipfile.ZipFile, entry: BackupEntryPlan) -> None:
        info = _zip_info(entry.path)
        digest = hashlib.sha256()
        total = 0
        with archive.open(info, "w", force_zip64=True) as target:
            if entry.generated_text is not None:
                payload = entry.generated_text.encode("utf-8")
                digest.update(payload)
                total += len(payload)
                target.write(payload)
            else:
                if not entry.source_path:
                    raise BackupWorkflowError("BACKUP_PLAN_INVALID", f"Missing source for {entry.path}")
                source = (self.project_root / entry.source_path).resolve()
                try:
                    source.relative_to(self.project_root)
                except ValueError as exc:
                    raise BackupWorkflowError("PATH_POLICY_BLOCKED", f"Backup source escaped project root: {entry.source_path}") from exc
                if not source.is_file() or source.is_symlink():
                    raise BackupWorkflowError("SOURCE_UNAVAILABLE", f"Backup source missing/unsafe: {entry.path}")
                with source.open("rb") as reader:
                    for chunk in iter(lambda: reader.read(1024 * 1024), b""):
                        digest.update(chunk)
                        total += len(chunk)
                        target.write(chunk)
        if total != entry.size or digest.hexdigest() != entry.sha256:
            raise BackupWorkflowError("SOURCE_HASH_CHANGED", f"Source changed during ZIP write: {entry.path}")

    def write_partial(self, plan: BackupPlan, target_partial: Path) -> Path:
        target_partial.parent.mkdir(parents=True, exist_ok=True)
        if target_partial.exists():
            raise BackupWorkflowError("BACKUP_TARGET_EXISTS", f"Partial target already exists: {target_partial}")
        names = [entry.path for entry in plan.entries] + ["backup/manifest.json"]
        normalized = [validate_zip_entry_name(name) for name in names]
        if normalized != sorted(normalized):
            # The planner must sort payload entries. Manifest is forced into the
            # deterministic final order below, so only duplicate safety matters here.
            normalized = sorted(normalized)
        if len(normalized) != len(set(normalized)):
            raise BackupWorkflowError("BACKUP_PLAN_INVALID", "Duplicate normalized ZIP path")

        manifest_bytes = (json.dumps(plan.manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        entry_map = {entry.path: entry for entry in plan.entries}
        try:
            with zipfile.ZipFile(
                target_partial,
                mode="x",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=9,
                allowZip64=True,
                strict_timestamps=True,
            ) as archive:
                for name in sorted(normalized):
                    if name == "backup/manifest.json":
                        with archive.open(_zip_info(name), "w", force_zip64=True) as target:
                            target.write(manifest_bytes)
                    else:
                        self._stream_entry(archive, entry_map[name])
            # Ensure bytes reach the filesystem before verification/promotion.
            with target_partial.open("rb") as handle:
                os.fsync(handle.fileno())
        except Exception:
            try:
                target_partial.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        return target_partial
