from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Property, Signal, Slot

from prompt_action.data.repository import VersionRepository
from prompt_action.data.transaction_journal import TransactionJournalStore
from prompt_action.domain.errors import ReleaseWorkflowError
from prompt_action.services.step09 import CapabilityService, CompareError, RevisionCompareService
from .per_prompt_query_service import PerPromptQueryService


class PerPromptViewModel(QObject):
    stateChanged = Signal()
    navigationRequested = Signal(str, str)
    actionRejected = Signal(str)
    downloadRequested = Signal(str)
    compareRequested = Signal('QVariant')
    addRevisionRequested = Signal(str)

    def __init__(self, project_root: Path, *, query_service: PerPromptQueryService | None = None, compare_service: RevisionCompareService | None = None, auto_refresh: bool = True):
        super().__init__()
        root = Path(project_root).resolve()
        self._root = root
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

    def _release_availability(self) -> tuple[bool, str]:
        try:
            repository = VersionRepository(self._root)
            state = repository.load()
            report = repository.validate(state)
            if not report.is_valid:
                return False, "Canonical data tidak valid; Tambah Revisi diblokir."
            pending = TransactionJournalStore(self._root).inspect_pending()
            if pending is not None:
                return False, "Ada transaksi release yang belum selesai; lakukan recovery terlebih dahulu."
            snapshot = next(
                (item for item in state.document.get("snapshots", []) if item.get("id") == state.active_snapshot),
                None,
            )
            if not isinstance(snapshot, dict) or snapshot.get("status") != "COMPLETE":
                return False, "Snapshot aktif belum COMPLETE. Selesaikan backup sebelum Tambah Revisi."
            prompt_id = str(self._state.get("selected_prompt_id") or "")
            if not prompt_id or prompt_id not in state.document.get("prompts", {}):
                return False, "Pilih Prompt yang valid terlebih dahulu."
            active_revision = state.document["prompts"][prompt_id].get("active_revision")
            revision = state.document["prompts"][prompt_id].get("revisions", {}).get(active_revision, {})
            if revision.get("file_available") is not True:
                return False, "File Prompt aktif belum termaterialisasi."
            return True, ""
        except ReleaseWorkflowError as exc:
            return False, exc.message
        except Exception as exc:
            return False, f"Tambah Revisi belum tersedia: {exc}"

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
        can_add, add_reason = self._release_availability()
        caps["can_add_revision"] = can_add
        caps["disabled_reason_add_revision"] = add_reason

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
        if not caps.get("can_add_revision"):
            self.actionRejected.emit(str(caps.get("disabled_reason_add_revision") or "Tambah Revisi belum tersedia."))
            return
        prompt_id = str(self._state.get("selected_prompt_id") or "")
        if not prompt_id:
            self.actionRejected.emit("Pilih Prompt terlebih dahulu.")
            return
        self.addRevisionRequested.emit(prompt_id)

    @staticmethod
    def _loading_state() -> dict[str, Any]:
        return {
            "load_state": "loading", "prompts": [], "selected_prompt_id": "", "selected_prompt_name": "",
            "active_revision_id": "", "selected_revision_id": "", "official_revisions": [], "drafts": [],
            "selected_revision": {}, "available_files": [], "capabilities": {}, "issues": [], "diagnostics": [],
        }
