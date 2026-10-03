from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Callable

from .models import AppSettings, SUPPORTED_SCHEMA_VERSION

_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_BRANCH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
_UI_SCALES = {100, 110, 125}
_TREE_DENSITIES = {"comfortable", "compact"}
_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}
_SECRET_KEYWORDS = ("token", "password", "secret", "authorization", "cookie", "pat")


@dataclass(frozen=True, slots=True)
class PathStatus:
    exists: bool
    is_dir: bool
    readable: bool
    writable: bool


@dataclass(slots=True)
class ValidationReport:
    errors: list[dict[str, str]] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)
    path_capabilities: dict[str, dict[str, object]] = field(default_factory=dict)

    @property
    def valid(self) -> bool:
        return not self.errors

    def add_error(self, field_name: str, code: str, message: str) -> None:
        self.errors.append({"field": field_name, "code": code, "message": message})

    def add_warning(self, field_name: str, code: str, message: str) -> None:
        self.warnings.append({"field": field_name, "code": code, "message": message})


PathProbe = Callable[[Path], PathStatus]


def default_path_probe(path: Path) -> PathStatus:
    try:
        exists = path.exists()
        is_dir = path.is_dir() if exists else False
        return PathStatus(
            exists,
            is_dir,
            bool(exists and is_dir and os.access(path, os.R_OK)),
            bool(exists and is_dir and os.access(path, os.W_OK)),
        )
    except OSError:
        return PathStatus(False, False, False, False)


def resolve_setting_path(value: str, project_root: Path) -> Path:
    raw = Path(value).expanduser()
    if not raw.is_absolute():
        raw = project_root / raw
    return raw.resolve(strict=False)


def normalize_for_storage(value: str, project_root: Path) -> str:
    resolved = resolve_setting_path(value, project_root)
    root = project_root.resolve(strict=False)
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return str(resolved)
    text = relative.as_posix()
    return "." if text in ("", ".") else text


def _under(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def validate_settings(settings: AppSettings, project_root: Path, *, path_probe: PathProbe = default_path_probe, runtime_temp: Path | None = None) -> ValidationReport:
    report = ValidationReport()
    root = project_root.resolve(strict=False)
    temp_root = (runtime_temp or root / "runtime" / "temp").resolve(strict=False)

    if settings.meta.schema_version != SUPPORTED_SCHEMA_VERSION:
        report.add_error("schema_version", "unsupported_schema", f"Schema settings {settings.meta.schema_version} tidak didukung; versi yang didukung {SUPPORTED_SCHEMA_VERSION}.")

    path_specs = (
        ("general.root_dir", settings.general.root_dir, True, True),
        ("general.prompts_dir", settings.general.prompts_dir, True, False),
        ("general.backup_dir", settings.general.backup_dir, False, True),
    )
    resolved_paths: dict[str, Path] = {}
    for field_name, raw_value, require_read, require_write in path_specs:
        if not isinstance(raw_value, str) or not raw_value.strip():
            report.add_error(field_name, "empty_path", "Path tidak boleh kosong.")
            continue
        resolved = resolve_setting_path(raw_value.strip(), root)
        resolved_paths[field_name] = resolved
        status = path_probe(resolved)
        report.path_capabilities[field_name] = {
            "resolved": str(resolved), "exists": status.exists, "is_dir": status.is_dir,
            "readable": status.readable, "writable": status.writable,
        }
        if _under(resolved, temp_root):
            report.add_error(field_name, "runtime_temp_forbidden", "Path tidak boleh berada di bawah runtime/temp.")
            continue
        if not status.exists:
            report.add_warning(field_name, "path_missing", "Folder belum ada; tidak dibuat otomatis oleh STEP 08.")
            continue
        if not status.is_dir:
            report.add_error(field_name, "not_directory", "Path harus menunjuk ke folder.")
            continue
        if require_read and not status.readable:
            report.add_error(field_name, "not_readable", "Folder harus dapat dibaca.")
        if require_write and not status.writable:
            report.add_error(field_name, "not_writable", "Folder harus dapat ditulis.")

    prompts = resolved_paths.get("general.prompts_dir")
    backup = resolved_paths.get("general.backup_dir")
    if prompts is not None and backup is not None and prompts == backup:
        report.add_warning("general.backup_dir", "backup_same_as_prompts", "Folder Backup sama dengan folder Prompt; gunakan lokasi terpisah bila memungkinkan.")

    second_raw = settings.backup.second_copy_dir
    if settings.backup.second_copy_enabled:
        if not isinstance(second_raw, str) or not second_raw.strip():
            report.add_error("backup.second_copy_dir", "second_copy_missing", "Lokasi salinan kedua wajib diisi.")
        else:
            second = resolve_setting_path(second_raw.strip(), root)
            status = path_probe(second)
            report.path_capabilities["backup.second_copy_dir"] = {
                "resolved": str(second), "exists": status.exists, "is_dir": status.is_dir,
                "readable": status.readable, "writable": status.writable,
            }
            if _under(second, temp_root):
                report.add_error("backup.second_copy_dir", "runtime_temp_forbidden", "Salinan kedua tidak boleh berada di runtime/temp.")
            if backup is not None and second == backup:
                report.add_error("backup.second_copy_dir", "second_copy_same_as_primary", "Lokasi salinan kedua harus berbeda dari folder Backup utama.")
            if status.exists and (not status.is_dir or not status.writable):
                report.add_error("backup.second_copy_dir", "second_copy_not_writable", "Lokasi salinan kedua harus berupa folder yang dapat ditulis.")
            elif not status.exists:
                report.add_warning("backup.second_copy_dir", "second_copy_missing_dir", "Folder salinan kedua belum ada; tidak dibuat otomatis.")

    if not settings.backup.write_sha256:
        report.add_error("backup.write_sha256", "integrity_gate_locked", "SHA256 wajib aktif untuk release.")
    if not settings.backup.verify_after_write:
        report.add_error("backup.verify_after_write", "integrity_gate_locked", "Verifikasi ZIP wajib aktif untuk release.")

    repo = settings.github.repository.strip()
    if not _REPO_RE.fullmatch(repo):
        report.add_error("github.repository", "invalid_repository", "Repository harus berformat owner/name, bukan URL.")
    branch = settings.github.branch.strip()
    if not branch or not _BRANCH_RE.fullmatch(branch) or branch.startswith("/") or branch.endswith("/") or ".." in branch or "//" in branch:
        report.add_error("github.branch", "invalid_branch", "Branch tidak valid.")

    if settings.appearance.theme != "light_blue":
        report.add_error("appearance.theme", "theme_locked", "Theme V1 dikunci ke Light — Prompt Action Blue.")
    if settings.appearance.ui_scale not in _UI_SCALES:
        report.add_error("appearance.ui_scale", "invalid_ui_scale", "UI Scale harus salah satu dari 100%, 110%, atau 125%.")
    if settings.appearance.tree_density not in _TREE_DENSITIES:
        report.add_error("appearance.tree_density", "invalid_tree_density", "Tree Density harus Comfortable atau Compact.")
    if settings.advanced.log_level not in _LOG_LEVELS:
        report.add_error("advanced.log_level", "invalid_log_level", "Log level tidak didukung.")
    return report


def contains_secret_key(mapping: object) -> bool:
    if isinstance(mapping, dict):
        for key, value in mapping.items():
            if any(word in str(key).lower() for word in _SECRET_KEYWORDS) or contains_secret_key(value):
                return True
    elif isinstance(mapping, list):
        return any(contains_secret_key(v) for v in mapping)
    return False
