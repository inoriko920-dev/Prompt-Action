from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Property, Signal, Slot

from prompt_action.services.step09 import CapabilityService, CompareError, RevisionCompareService
from .per_prompt_query_service import PerPromptQueryService


class PerPromptViewModel(QObject):
    stateChanged = Signal()
    navigationRequested = Signal(str, str)
    actionRejected = Signal(str)
    downloadRequested = Signal(str)
    compareRequested = Signal('QVariant')

    def __init__(self, project_root: Path, *, query_service: PerPromptQueryService | None = None, compare_service: RevisionCompareService | None = None, auto_refresh: bool = True):
        super().__init__()
        root = Path(project_root).resolve()
        self._query = query_service or PerPromptQueryService(root)
        self._compare = compare_service or RevisionCompareService(root)
        self._capabilities = CapabilityService()
        self._state: dict[str, Any] = self._loading_state()
        if auto_refresh:
            self.refresh()

    @Property("QVariant", notify=stateChanged)
    def state(self) -> dict[str, Any]:
        return self._state

    @Slot()
    def refresh(self) -> None:
        prompt_id = str(self._state.get("selected_prompt_id") or "") or None
        revision_id = str(self._state.get("selected_revision_id") or "") or None
        self._state = self._loading_state()
        self.stateChanged.emit()
        self._state = self._query.read(prompt_id, revision_id)
        self._apply_step09_capabilities()
        self.stateChanged.emit()

    def _apply_step09_capabilities(self) -> None:
        caps = self._state.get("capabilities", {})
        detail = self._state.get("selected_revision", {})
        if not isinstance(caps, dict) or not isinstance(detail, dict):
            return
        parent = detail.get("parent")
        selected_valid = str(detail.get("file_state") or "") == "VALID"
        parent_valid = False
        if parent:
            parent_node = next((x for x in self._state.get("official_revisions", []) if isinstance(x, dict) and x.get("id") == parent), None)
            parent_valid = bool(parent_node and str(parent_node.get("file_state") or "") == "VALID")
        compare_cap = self._capabilities.get("COMPARE_REVISION", {"same_prompt": True, "verified_files": int(selected_valid) + int(parent_valid)})
        caps["can_compare"] = bool(parent) and compare_cap.enabled
        caps["disabled_reason_compare"] = "Revision baseline tidak memiliki parent untuk dibandingkan." if not parent else compare_cap.reason
        caps["can_add_revision"] = False
        caps["disabled_reason_add_revision"] = self._capabilities.get("ADD_REVISION").reason

    @Slot(str)
    def selectPrompt(self, prompt_id: str) -> None:
        if not prompt_id:
            return
        self._state = self._query.read(prompt_id, None)
        self._apply_step09_capabilities()
        self.stateChanged.emit()

    @Slot(str)
    def selectRevision(self, revision_id: str) -> None:
        if not revision_id:
            return
        prompt_id = str(self._state.get("selected_prompt_id") or "") or None
        self._state = self._query.read(prompt_id, revision_id)
        self._apply_step09_capabilities()
        self.stateChanged.emit()

    @Slot()
    def downloadActivePrompt(self) -> None:
        caps = self._state.get("capabilities", {})
        path = caps.get("active_download_path") if isinstance(caps, dict) else None
        if not caps.get("can_download_active") or not path:
            self.actionRejected.emit(str(caps.get("disabled_reason_active_download") or "File Prompt aktif tidak tersedia."))
            return
        self.downloadRequested.emit(str(path))

    @Slot()
    def downloadSelectedRevision(self) -> None:
        caps = self._state.get("capabilities", {})
        path = caps.get("selected_download_path") if isinstance(caps, dict) else None
        if not caps.get("can_download_selected") or not path:
            self.actionRejected.emit(str(caps.get("disabled_reason_selected_download") or "File revision tidak tersedia."))
            return
        self.downloadRequested.emit(str(path))

    @Slot()
    def compareSelectedWithParent(self) -> None:
        caps = self._state.get("capabilities", {})
        detail = self._state.get("selected_revision", {})
        if not isinstance(caps, dict) or not caps.get("can_compare"):
            self.actionRejected.emit(str(caps.get("disabled_reason_compare") or "Perbandingan tidak tersedia."))
            return
        prompt_id = str(self._state.get("selected_prompt_id") or "")
        selected = str(self._state.get("selected_revision_id") or "")
        parent = str(detail.get("parent") or "") if isinstance(detail, dict) else ""
        try:
            result = self._compare.compare(prompt_id, parent, selected)
        except CompareError as exc:
            self.actionRejected.emit(exc.user_message)
            return
        self.compareRequested.emit(result.to_dict())

    @Slot()
    def viewSnapshot(self) -> None:
        detail = self._state.get("selected_revision", {})
        snapshot = detail.get("snapshot") if isinstance(detail, dict) else None
        caps = self._state.get("capabilities", {})
        if not caps.get("can_view_snapshot") or not snapshot:
            self.actionRejected.emit("Revision ini tidak memiliki Snapshot yang dapat dibuka.")
            return
        self.navigationRequested.emit("system_history", str(snapshot))

    @Slot()
    def openChangelog(self) -> None:
        caps = self._state.get("capabilities", {})
        self.actionRejected.emit(str(caps.get("disabled_reason_changelog") or "Changelog belum tersedia."))

    @Slot()
    def addRevision(self) -> None:
        caps = self._state.get("capabilities", {})
        self.actionRejected.emit(str(caps.get("disabled_reason_add_revision") or self._capabilities.get("ADD_REVISION").reason))

    @staticmethod
    def _loading_state() -> dict[str, Any]:
        return {
            "load_state": "loading", "prompts": [], "selected_prompt_id": "", "selected_prompt_name": "",
            "active_revision_id": "", "selected_revision_id": "", "official_revisions": [], "drafts": [],
            "selected_revision": {}, "available_files": [], "capabilities": {}, "issues": [], "diagnostics": [],
        }
