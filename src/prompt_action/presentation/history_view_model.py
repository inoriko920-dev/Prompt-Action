from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Property, Signal, Slot

from .history_query_service import SystemHistoryQueryService


class SystemHistoryViewModel(QObject):
    stateChanged = Signal()
    navigationRequested = Signal(str, str)
    actionRejected = Signal(str)
    downloadRequested = Signal(str)

    def __init__(self, project_root: Path, *, query_service: SystemHistoryQueryService | None = None, auto_refresh: bool = True):
        super().__init__()
        self._query = query_service or SystemHistoryQueryService(Path(project_root).resolve())
        self._state: dict[str, Any] = {"load_state": "loading", "systems": [], "selected_snapshot": {}, "diagnostics": []}
        if auto_refresh:
            self.refresh()

    @Property("QVariant", notify=stateChanged)
    def state(self) -> dict[str, Any]:
        return self._state

    @Slot()
    def refresh(self) -> None:
        selected = str(self._state.get("selected_snapshot_id") or "") or None
        self._state = {"load_state": "loading", "systems": [], "selected_snapshot": {}, "diagnostics": []}
        self.stateChanged.emit()
        self._state = self._query.read(selected)
        self.stateChanged.emit()

    @Slot(str)
    def selectSnapshot(self, snapshot_id: str) -> None:
        if not snapshot_id:
            return
        self._state = self._query.read(snapshot_id)
        self.stateChanged.emit()

    @Slot()
    def viewChangedPrompts(self) -> None:
        detail = self._state.get("selected_snapshot", {})
        ids = detail.get("changed_prompt_ids", []) if isinstance(detail, dict) else []
        if not ids:
            self.actionRejected.emit("Snapshot ini tidak memiliki PRIMARY/SYNC change.")
            return
        self.navigationRequested.emit("prompt", str(ids[0]))

    @Slot()
    def openBackup(self) -> None:
        detail = self._state.get("selected_snapshot", {})
        self.navigationRequested.emit("backup", str(detail.get("id") or ""))

    @Slot()
    def downloadSnapshotBackup(self) -> None:
        detail = self._state.get("selected_snapshot", {})
        path = detail.get("backup_download_path") if isinstance(detail, dict) else None
        if not path:
            self.actionRejected.emit("Backup snapshot tervalidasi belum tersedia.")
            return
        self.downloadRequested.emit(str(path))

    @Slot()
    def comparePrevious(self) -> None:
        detail = self._state.get("selected_snapshot", {})
        parent = detail.get("parent_snapshot") if isinstance(detail, dict) else None
        if not parent:
            self.actionRejected.emit("Snapshot baseline tidak memiliki snapshot sebelumnya.")
            return
        self.actionRejected.emit("Perbandingan snapshot metadata belum memiliki dialog final pada STEP 05.")

    @Slot()
    def viewChangelog(self) -> None:
        detail = self._state.get("selected_snapshot", {})
        caps = detail.get("capabilities", {}) if isinstance(detail, dict) else {}
        if not caps.get("can_view_changelog"):
            self.actionRejected.emit("Changelog tambahan belum tersedia untuk snapshot ini.")
            return
        self.actionRejected.emit(str(detail.get("reason") or "Tidak ada changelog tambahan."))
