from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Callable

from prompt_action.app_version import APP_VERSION
from .defaults import default_settings
from .models import AppSettings
from .validator import normalize_for_storage


class SettingsWriteError(RuntimeError):
    pass


@dataclass(slots=True)
class SettingsLoadResult:
    settings: AppSettings
    source: str
    degraded: bool = False
    error: str | None = None


class SettingsRepository:
    def __init__(self, project_root: Path, *, runtime_root: Path | None = None, replace_func: Callable[[str | os.PathLike[str], str | os.PathLike[str]], None] = os.replace) -> None:
        self.project_root = project_root.resolve(strict=False)
        self.runtime_root = (runtime_root or self.project_root / "runtime").resolve(strict=False)
        self.settings_dir = self.runtime_root / "settings"
        self.settings_path = self.settings_dir / "settings.json"
        self._replace = replace_func

    def load(self) -> SettingsLoadResult:
        if not self.settings_path.exists():
            return SettingsLoadResult(default_settings(self.project_root), "defaults", False, None)
        try:
            raw = json.loads(self.settings_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("root settings JSON must be an object")
            return SettingsLoadResult(AppSettings.from_dict(raw, app_version=APP_VERSION), "persisted", False, None)
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            # Never guess old values or overwrite a corrupt file automatically.
            return SettingsLoadResult(default_settings(self.project_root), "safe_defaults", True, f"Settings tidak dapat dibaca: {type(exc).__name__}")

    def save(self, settings: AppSettings) -> AppSettings:
        to_write = AppSettings.from_dict(settings.to_dict(), app_version=APP_VERSION)
        to_write.general.root_dir = normalize_for_storage(to_write.general.root_dir, self.project_root)
        to_write.general.prompts_dir = normalize_for_storage(to_write.general.prompts_dir, self.project_root)
        to_write.general.backup_dir = normalize_for_storage(to_write.general.backup_dir, self.project_root)
        if to_write.backup.second_copy_dir:
            to_write.backup.second_copy_dir = normalize_for_storage(to_write.backup.second_copy_dir, self.project_root)
        if to_write.advanced.diagnostics_dir:
            to_write.advanced.diagnostics_dir = normalize_for_storage(to_write.advanced.diagnostics_dir, self.project_root)
        to_write.github.repository = to_write.github.repository.strip()
        to_write.github.branch = to_write.github.branch.strip()
        to_write.meta.saved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        to_write.meta.app_version = APP_VERSION

        self.settings_dir.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(to_write.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", prefix=".settings-", suffix=".tmp", dir=self.settings_dir, delete=False) as handle:
                temp_path = Path(handle.name)
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            self._replace(temp_path, self.settings_path)
            temp_path = None
        except Exception as exc:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise SettingsWriteError(f"Atomic settings write failed: {type(exc).__name__}") from exc

        verified = self.load()
        if verified.degraded or verified.source != "persisted":
            raise SettingsWriteError("Settings verification failed after atomic replace")
        return verified.settings
