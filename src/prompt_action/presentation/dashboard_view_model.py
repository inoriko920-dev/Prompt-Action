from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Property, Signal, Slot

from .dashboard_models import DashboardState
from .dashboard_query_service import DashboardQueryService


class DashboardViewModel(QObject):
    stateChanged = Signal()
    navigationRequested = Signal(str, str)
    actionRejected = Signal(str)
    downloadRequested = Signal(str)

    def __init__(self, project_root: Path, *, query_service: DashboardQueryService | None = None, auto_refresh: bool = True):
        super().__init__()
        self._project_root = Path(project_root).resolve()
        self._query = query_service or DashboardQueryService(self._project_root)
        self._state = DashboardState.loading()
        if auto_refresh:
            self.refresh()

    @Property("QVariant", notify=stateChanged)
    def state(self) -> dict[str, Any]:
        return self._state.to_dict()

    @Slot()
    def refresh(self) -> None:
        self._state = DashboardState.loading()
        self.stateChanged.emit()
        self._state = self._query.read()
        self.stateChanged.emit()

    @Slot(str)
    def openPrompt(self, prompt_id: str) -> None:
        if not prompt_id or not self._state.action_capabilities.can_open_prompt:
            self.actionRejected.emit("Prompt aktif belum dapat dibuka.")
            return
        self.navigationRequested.emit("prompt", prompt_id)

    @Slot(str)
    def openSnapshot(self, snapshot_id: str) -> None:
        if not snapshot_id or not self._state.latest_change.can_open_snapshot:
            self.actionRejected.emit("Snapshot belum dapat dibuka.")
            return
        self.navigationRequested.emit("system_history", snapshot_id)

    @Slot()
    def openLatestChange(self) -> None:
        snapshot_id = self._state.latest_change.snapshot_id
        if not snapshot_id or not self._state.action_capabilities.can_open_latest_change:
            self.actionRejected.emit("Perubahan terakhir belum tersedia.")
            return
        self.navigationRequested.emit("system_history", snapshot_id)

    @Slot()
    def openActivePrompts(self) -> None:
        if not self._state.active_prompts:
            self.actionRejected.emit("Belum ada prompt aktif.")
            return
        self.navigationRequested.emit("prompt", self._state.active_prompts[0].prompt_id)

    @Slot()
    def openBackupPage(self) -> None:
        if not self._state.action_capabilities.can_open_backup_page:
            self.actionRejected.emit("Halaman Backup & Recovery belum tersedia.")
            return
        self.navigationRequested.emit("backup", "")

    @Slot()
    def requestBackupNow(self) -> None:
        if not self._state.action_capabilities.can_request_backup:
            self.actionRejected.emit(self._state.action_capabilities.reason_if_disabled)
            return
        self.actionRejected.emit("Backup engine belum diimplementasikan pada STEP 04.")

    @Slot()
    def downloadFullBackup(self) -> None:
        caps = self._state.action_capabilities
        if not caps.can_download_full_backup or not caps.backup_download_path:
            self.actionRejected.emit("Full Backup tervalidasi belum tersedia untuk diunduh.")
            return
        self.downloadRequested.emit(caps.backup_download_path)
