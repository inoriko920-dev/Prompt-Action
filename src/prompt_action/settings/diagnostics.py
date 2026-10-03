from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import tempfile
from typing import Callable

from prompt_action.app_version import APP_VERSION
from .models import AppSettings
from .sanitization import sanitize_text, sanitize_value
from .validator import ValidationReport


def build_diagnostics(settings: AppSettings, validation: ValidationReport, *, project_root: Path, log_excerpt: str | None = None) -> dict[str, object]:
    try:
        import PySide6
        pyside_version = PySide6.__version__
    except Exception:
        pyside_version = "unavailable"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "app_version": APP_VERSION,
        "platform": {
            "system": platform.system(), "release": platform.release(), "version": platform.version(),
            "machine": platform.machine(), "python": platform.python_version(), "pyside6": pyside_version,
        },
        "features": {"settings_atomic_persistence": True, "github_connection_test": False, "backup_engine_final": False, "restore_engine": False},
        "settings": sanitize_value(settings.to_dict(), project_root=project_root),
        "validation": {
            "valid": validation.valid,
            "errors": sanitize_value(validation.errors, project_root=project_root),
            "warnings": sanitize_value(validation.warnings, project_root=project_root),
            "path_capabilities": sanitize_value(validation.path_capabilities, project_root=project_root),
        },
        "recent_log_excerpt": sanitize_text(log_excerpt, project_root=project_root) if log_excerpt else None,
    }


def export_diagnostics(output_dir: Path, settings: AppSettings, validation: ValidationReport, *, project_root: Path, log_excerpt: str | None = None, replace_func: Callable[[str | os.PathLike[str], str | os.PathLike[str]], None] = os.replace) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    final_path = output_dir / f"PromptAction-Diagnostics-{stamp}.json"
    payload = json.dumps(build_diagnostics(settings, validation, project_root=project_root, log_excerpt=log_excerpt), indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", prefix=".diagnostics-", suffix=".tmp", dir=output_dir, delete=False) as handle:
            temp_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        replace_func(temp_path, final_path)
        temp_path = None
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
    return final_path
