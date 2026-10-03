from __future__ import annotations

from pathlib import Path
import re

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot

from prompt_action.settings.diagnostics import export_diagnostics
from prompt_action.settings.models import AppSettings
from prompt_action.settings.repository import SettingsRepository, SettingsWriteError
from prompt_action.settings.validator import PathProbe, default_path_probe, resolve_setting_path, validate_settings

_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class SettingsViewModel(QObject):
    stateChanged = Signal()
    pathOpenRequested = Signal(str)
    diagnosticsExported = Signal(str)

    def __init__(self, project_root: Path, *, runtime_root: Path | None = None, repository: SettingsRepository | None = None, path_probe: PathProbe = default_path_probe) -> None:
        super().__init__()
        self._project_root = project_root.resolve(strict=False)
        self._runtime_root = (runtime_root or self._project_root / "runtime").resolve(strict=False)
        self._repository = repository or SettingsRepository(self._project_root, runtime_root=self._runtime_root)
        self._path_probe = path_probe
        loaded = self._repository.load()
        self._persisted = loaded.settings
        self._draft = self._clone(self._persisted)
        self._degraded = loaded.degraded
        self._load_error = loaded.error
        self._save_state = "IDLE"
        self._status_message = ((loaded.error or "Pengaturan default aman dimuat.") if loaded.source != "persisted" else "Pengaturan dimuat.")
        self._last_export_path: str | None = None
        self._refresh_state()

    @staticmethod
    def _clone(settings: AppSettings) -> AppSettings:
        return AppSettings.from_dict(settings.to_dict(), app_version=settings.meta.app_version)

    def _refresh_state(self) -> None:
        report = validate_settings(self._draft, self._project_root, path_probe=self._path_probe, runtime_temp=self._runtime_root / "temp")
        persisted_dict = self._persisted.to_dict()
        draft_dict = self._draft.to_dict()
        dirty = draft_dict != persisted_dict
        restart_required = self._draft.appearance.ui_scale != self._persisted.appearance.ui_scale or self._draft.appearance.tree_density != self._persisted.appearance.tree_density
        repo = self._draft.github.repository.strip()
        repo_valid = bool(_REPO_RE.fullmatch(repo))
        self._state = {
            "load_state": "degraded" if self._degraded else "ready",
            "load_error": self._load_error or "",
            "persisted_settings": persisted_dict,
            "draft_settings": draft_dict,
            "is_dirty": dirty,
            "validation_errors": list(report.errors),
            "validation_warnings": list(report.warnings),
            "save_state": self._save_state,
            "path_capabilities": dict(report.path_capabilities),
            "github_capability": {
                "status": "UNAVAILABLE", "connected": False, "test_available": False,
                "reason": "Tes koneksi tersedia setelah GitHub service aktif (STEP 13).",
                "can_open_repository": repo_valid,
            },
            "repository_url": f"https://github.com/{repo}" if repo_valid else "",
            "restart_required": restart_required,
            "can_save": bool(dirty and report.valid and self._save_state != "SAVING"),
            "can_revert": bool(dirty and self._save_state != "SAVING"),
            "last_saved_at": self._persisted.meta.saved_at or "",
            "status_message": self._status_message,
            "last_export_path": self._last_export_path or "",
            "theme_locked": True,
            "integrity_policy_locked": True,
        }
        self._validation = report

    @Property("QVariant", notify=stateChanged)
    def state(self):
        return self._state

    def _emit(self) -> None:
        self._refresh_state()
        self.stateChanged.emit()

    @Slot(str, str, "QVariant")
    def updateField(self, section: str, field: str, value) -> None:
        if self._save_state == "SAVING":
            return
        if section == "backup" and field in {"write_sha256", "verify_after_write"}:
            self._status_message = "SHA256 dan verifikasi ZIP dikunci aktif karena merupakan release gate."
            self._emit(); return
        if section == "appearance" and field == "theme":
            self._status_message = "Theme V1 dikunci ke Light — Prompt Action Blue."
            self._emit(); return
        target = getattr(self._draft, section, None)
        if target is None or not hasattr(target, field):
            self._status_message = "Field pengaturan tidak dikenal."
            self._emit(); return
        current = getattr(target, field)
        if isinstance(current, bool):
            coerced = bool(value)
        elif isinstance(current, int) and not isinstance(current, bool):
            try: coerced = int(value)
            except (TypeError, ValueError): coerced = -1
        else:
            coerced = str(value)
        setattr(target, field, coerced)
        self._save_state = "IDLE"
        self._status_message = "Perubahan belum disimpan."
        self._emit()

    @Slot(str, str)
    def selectFolder(self, key: str, path: str) -> None:
        if not path:
            return
        if path.startswith("file:"):
            local = QUrl(path).toLocalFile()
            if local: path = local
        mapping = {
            "root_dir": ("general", "root_dir"), "prompts_dir": ("general", "prompts_dir"),
            "backup_dir": ("general", "backup_dir"), "second_copy_dir": ("backup", "second_copy_dir"),
            "diagnostics_dir": ("advanced", "diagnostics_dir"),
        }
        target = mapping.get(key)
        if target is not None:
            self.updateField(target[0], target[1], path)

    @Slot()
    def revertSettings(self) -> None:
        if self._save_state == "SAVING": return
        self._draft = self._clone(self._persisted)
        self._save_state = "IDLE"
        self._status_message = "Perubahan dibatalkan."
        self._emit()

    @Slot()
    def saveSettings(self) -> None:
        self._refresh_state()
        if self._save_state == "SAVING" or not self._state["is_dirty"]: return
        self._save_state = "VALIDATING"; self._emit()
        if self._validation.errors:
            self._save_state = "ERROR"; self._status_message = "Perbaiki field yang invalid sebelum menyimpan."; self._emit(); return
        self._save_state = "SAVING"; self._status_message = "Menyimpan pengaturan…"; self._emit()
        try:
            saved = self._repository.save(self._draft)
        except SettingsWriteError:
            self._save_state = "ERROR"; self._status_message = "Gagal menyimpan. Pengaturan lama tetap utuh."; self._emit(); return
        self._persisted = saved
        self._draft = self._clone(saved)
        self._degraded = False; self._load_error = None
        self._save_state = "SUCCESS"; self._status_message = "Pengaturan tersimpan."; self._emit()

    @Slot()
    def testGitHubConnection(self) -> None:
        self._status_message = "Tes koneksi belum tersedia; GitHub service aktif pada STEP 13."
        self._emit()

    @Slot(bool)
    def resetLayout(self, confirmed: bool) -> None:
        if not confirmed or self._save_state == "SAVING": return
        self._draft.appearance.theme = "light_blue"
        self._draft.appearance.ui_scale = 100
        self._draft.appearance.tree_density = "comfortable"
        self._status_message = "Preferensi layout dikembalikan ke default; belum disimpan."
        self._save_state = "IDLE"; self._emit()

    @Slot()
    def openLogFolder(self) -> None:
        log_dir = self._runtime_root / "logs"
        if not log_dir.is_dir():
            self._status_message = "Folder log belum tersedia."; self._emit(); return
        self.pathOpenRequested.emit(str(log_dir))
        self._status_message = "Folder log siap dibuka."; self._emit()

    @Slot()
    def exportDiagnostics(self) -> None:
        output_dir = resolve_setting_path(self._draft.advanced.diagnostics_dir, self._project_root)
        try:
            path = export_diagnostics(output_dir, self._draft, self._validation, project_root=self._project_root)
        except OSError:
            self._status_message = "Export diagnostics gagal."; self._emit(); return
        self._last_export_path = str(path)
        self._status_message = "Diagnostics berhasil diekspor dengan sanitasi."
        self.diagnosticsExported.emit(str(path)); self._emit()
