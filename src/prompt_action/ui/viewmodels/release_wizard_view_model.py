from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Property, QTimer, QUrl, Signal, Slot

from prompt_action.data.repository import VersionRepository
from prompt_action.data.transaction_journal import TransactionJournalStore
from prompt_action.domain.errors import ReleaseWorkflowError
from prompt_action.services.release_recovery import ReleaseRecoveryService
from prompt_action.services.release_service import ReleaseService


class ReleaseWizardViewModel(QObject):
    """UI adapter for STEP 10.

    The wizard imports TXT files and delegates all authoritative mutation logic
    to ReleaseService. It deliberately does not expose a prompt text editor.
    """

    stateChanged = Signal()
    dialogRequested = Signal()
    releaseCompleted = Signal(str)
    recoveryRequired = Signal(str)

    def __init__(self, project_root: Path):
        super().__init__()
        self._root = Path(project_root).resolve()
        self._repository = VersionRepository(self._root)
        self._journals = TransactionJournalStore(self._root)
        self._recovery = ReleaseRecoveryService(self._root)
        self._service = ReleaseService(self._root)
        self._primary_source: Path | None = None
        self._sync_sources: dict[str, Path] = {}
        self._plan = None
        self._state: dict[str, Any] = self._empty_state()
        self.refreshAvailability()

    @Property("QVariant", notify=stateChanged)
    def state(self) -> dict[str, Any]:
        return self._state

    @staticmethod
    def _path_from_ui(value: str) -> Path:
        raw = str(value or "").strip()
        if raw.startswith("file:"):
            local = QUrl(raw).toLocalFile()
            if local:
                return Path(local).resolve()
        return Path(raw).expanduser().resolve()

    def _prompt_options(self, document: dict[str, Any]) -> list[dict[str, str]]:
        values: list[dict[str, str]] = []
        for prompt_id, prompt in document.get("prompts", {}).items():
            if not isinstance(prompt, dict):
                continue
            values.append({
                "id": str(prompt_id),
                "display_name": str(prompt.get("display_name") or prompt_id),
                "active_revision": str(prompt.get("active_revision") or "—"),
            })
        return values

    def _availability(self) -> dict[str, Any]:
        try:
            pending = self._journals.inspect_pending()
            if pending is not None:
                return {
                    "can_start": False,
                    "reason": "Ada transaksi release yang belum selesai. Lakukan recovery terlebih dahulu.",
                    "recovery_txn_id": str(pending.get("txn_id") or ""),
                }
            state = self._repository.load()
            report = self._repository.validate(state)
            if not report.is_valid:
                return {"can_start": False, "reason": "Canonical data tidak valid; release diblokir.", "recovery_txn_id": ""}
            snapshot = next(
                (item for item in state.document.get("snapshots", []) if item.get("id") == state.active_snapshot),
                None,
            )
            if not isinstance(snapshot, dict):
                return {"can_start": False, "reason": "Snapshot aktif tidak dapat ditemukan.", "recovery_txn_id": ""}
            if snapshot.get("status") != "COMPLETE":
                return {
                    "can_start": False,
                    "reason": "Snapshot aktif belum COMPLETE. Selesaikan backup STEP 11 sebelum membuat release berikutnya.",
                    "recovery_txn_id": "",
                }
            return {
                "can_start": True,
                "reason": "",
                "recovery_txn_id": "",
                "active_system": state.active_system,
                "active_snapshot": state.active_snapshot,
                "app_data_revision": state.app_data_revision,
            }
        except ReleaseWorkflowError as exc:
            return {"can_start": False, "reason": exc.message, "recovery_txn_id": ""}
        except Exception as exc:
            return {"can_start": False, "reason": f"Release belum tersedia: {exc}", "recovery_txn_id": ""}

    @Slot()
    def refreshAvailability(self) -> None:
        try:
            document = self._repository.load().document
            options = self._prompt_options(document)
        except Exception:
            options = []
        availability = self._availability()
        self._state.update({
            "availability": availability,
            "prompt_options": options,
        })
        self.stateChanged.emit()

    @Slot(str)
    def openForPrompt(self, prompt_id: str) -> None:
        self._primary_source = None
        self._sync_sources = {}
        self._plan = None
        self._state = self._empty_state()
        try:
            document = self._repository.load().document
            options = self._prompt_options(document)
            selected = next((item for item in options if item["id"] == prompt_id), options[0] if options else None)
            availability = self._availability()
            self._state.update({
                "availability": availability,
                "prompt_options": options,
                "primary_prompt_id": selected["id"] if selected else "",
                "primary_prompt_name": selected["display_name"] if selected else "",
                "primary_active_revision": selected["active_revision"] if selected else "",
                "stage": "input",
            })
            if not availability.get("can_start"):
                self._state["stage"] = "blocked"
                self._state["error_message"] = str(availability.get("reason") or "Release diblokir.")
        except Exception as exc:
            self._state["stage"] = "error"
            self._state["error_message"] = str(exc)
        self.stateChanged.emit()
        self.dialogRequested.emit()

    @Slot(str)
    def selectPrimaryPrompt(self, prompt_id: str) -> None:
        option = next((x for x in self._state.get("prompt_options", []) if x.get("id") == prompt_id), None)
        if not option:
            return
        self._plan = None
        self._primary_source = None
        self._state.update({
            "primary_prompt_id": prompt_id,
            "primary_prompt_name": option["display_name"],
            "primary_active_revision": option["active_revision"],
            "primary_source": "",
            "primary_source_name": "",
            "plan": {},
            "warnings": [],
            "stage": "input",
        })
        self.stateChanged.emit()

    @Slot(str)
    def setPrimarySource(self, value: str) -> None:
        path = self._path_from_ui(value)
        self._primary_source = path
        self._plan = None
        self._state["primary_source"] = str(path)
        self._state["primary_source_name"] = path.name
        self._state["stage"] = "input"
        self.stateChanged.emit()

    @Slot(str)
    def setReason(self, value: str) -> None:
        self._state["reason"] = str(value)
        self._plan = None
        self.stateChanged.emit()

    @Slot(str)
    def setSummary(self, value: str) -> None:
        self._state["summary"] = str(value)
        self._plan = None
        self.stateChanged.emit()

    @Slot(str, str, str)
    def addSync(self, prompt_id: str, source_value: str, reason: str) -> None:
        if not prompt_id or prompt_id == self._state.get("primary_prompt_id"):
            self._set_error("INVALID_SYNC", "Prompt SYNC harus berbeda dari PRIMARY.")
            return
        option = next((x for x in self._state.get("prompt_options", []) if x.get("id") == prompt_id), None)
        if not option:
            self._set_error("INVALID_SYNC", "Prompt SYNC tidak dikenal.")
            return
        path = self._path_from_ui(source_value)
        self._sync_sources[prompt_id] = path
        rows = [x for x in self._state.get("sync_changes", []) if x.get("prompt_id") != prompt_id]
        rows.append({
            "prompt_id": prompt_id,
            "display_name": option["display_name"],
            "active_revision": option["active_revision"],
            "source": str(path),
            "source_name": path.name,
            "reason": str(reason or "").strip(),
        })
        self._state["sync_changes"] = rows
        self._state["error_code"] = ""
        self._state["error_message"] = ""
        self._plan = None
        self.stateChanged.emit()

    @Slot(str)
    def removeSync(self, prompt_id: str) -> None:
        self._sync_sources.pop(prompt_id, None)
        self._state["sync_changes"] = [x for x in self._state.get("sync_changes", []) if x.get("prompt_id") != prompt_id]
        self._plan = None
        self.stateChanged.emit()

    def _set_error(self, code: str, message: str, *, stage: str | None = None) -> None:
        self._state["error_code"] = code
        self._state["error_message"] = message
        if stage is not None:
            self._state["stage"] = stage
        self.stateChanged.emit()

    @Slot()
    def planRelease(self) -> None:
        availability = self._availability()
        self._state["availability"] = availability
        if not availability.get("can_start"):
            self._set_error("PREVIOUS_BACKUP_INCOMPLETE", str(availability.get("reason") or "Release diblokir."), stage="blocked")
            return
        if self._primary_source is None:
            self._set_error("PATH_POLICY_BLOCKED", "Pilih file TXT baru untuk PRIMARY.")
            return
        reason = str(self._state.get("reason") or "").strip()
        if not reason:
            self._set_error("PATH_POLICY_BLOCKED", "Alasan perubahan wajib diisi.")
            return
        summary_text = str(self._state.get("summary") or "").strip()
        sync_payload = [
            {
                "prompt_id": row["prompt_id"],
                "source": str(self._sync_sources[row["prompt_id"]]),
                "reason": str(row.get("reason") or reason),
            }
            for row in self._state.get("sync_changes", [])
            if row.get("prompt_id") in self._sync_sources
        ]
        try:
            self._plan = self._service.plan_release(
                primary_prompt_id=str(self._state.get("primary_prompt_id") or ""),
                primary_source=self._primary_source,
                sync=sync_payload,
                reason=reason,
                summary=[summary_text] if summary_text else None,
            )
            validation = self._service.validate_plan(self._plan)
            if not validation.is_valid:
                issue = (validation.blocking_issues + validation.errors)[0]
                self._plan = None
                self._set_error(issue.code, issue.message)
                return
            self._state.update({
                "stage": "review",
                "plan": self._plan.to_dict(include_confirmation_token=False),
                "warnings": list(self._plan.warnings),
                "error_code": "",
                "error_message": "",
            })
            self.stateChanged.emit()
        except ReleaseWorkflowError as exc:
            stage = "recovery_required" if exc.code == "RECOVERY_REQUIRED" else "input"
            self._set_error(exc.code, exc.message, stage=stage)
            if exc.code == "RECOVERY_REQUIRED":
                self.recoveryRequired.emit(exc.message)
        except Exception as exc:
            self._set_error("RECOVERY_REQUIRED", str(exc), stage="error")

    @Slot()
    def commitRelease(self) -> None:
        if self._plan is None or self._state.get("stage") != "review":
            self._set_error("STATE_CHANGED_RELOAD_REQUIRED", "Review release belum valid atau sudah berubah.")
            return
        self._state["stage"] = "committing"
        self._state["error_code"] = ""
        self._state["error_message"] = ""
        self.stateChanged.emit()
        QTimer.singleShot(0, self._commit_now)

    def _commit_now(self) -> None:
        plan = self._plan
        if plan is None:
            return
        try:
            result = self._service.commit_release(plan, plan.confirmation_token)
            self._state.update({
                "stage": "success",
                "result": result.to_dict(),
                "availability": self._availability(),
                "error_code": "",
                "error_message": "",
            })
            self.stateChanged.emit()
            self.releaseCompleted.emit(result.snapshot_id)
        except ReleaseWorkflowError as exc:
            stage = "recovery_required" if exc.code == "RECOVERY_REQUIRED" else "error"
            self._set_error(exc.code, exc.message, stage=stage)
            if exc.code == "RECOVERY_REQUIRED":
                self.recoveryRequired.emit(exc.message)
        except Exception as exc:
            self._set_error("RECOVERY_REQUIRED", str(exc), stage="recovery_required")
            self.recoveryRequired.emit(str(exc))

    @Slot(str)
    def recover(self, strategy: str) -> None:
        pending = self._recovery.inspect_pending_transaction()
        if pending is None:
            self.refreshAvailability()
            return
        try:
            result = self._recovery.recover_transaction(pending.txn_id, strategy)
            self._state["recovery_result"] = result.to_dict()
            self._state["stage"] = "success" if result.phase == "COMMITTED" else "input"
            self._state["availability"] = self._availability()
            self._state["error_code"] = ""
            self._state["error_message"] = ""
            self.stateChanged.emit()
            if result.phase == "COMMITTED":
                self.releaseCompleted.emit(result.snapshot_id)
        except ReleaseWorkflowError as exc:
            self._set_error(exc.code, exc.message, stage="recovery_required")

    @Slot()
    def reset(self) -> None:
        options = list(self._state.get("prompt_options", []))
        availability = self._availability()
        self._primary_source = None
        self._sync_sources = {}
        self._plan = None
        self._state = self._empty_state()
        self._state["prompt_options"] = options
        self._state["availability"] = availability
        self.stateChanged.emit()

    @staticmethod
    def _empty_state() -> dict[str, Any]:
        return {
            "stage": "idle",
            "availability": {"can_start": False, "reason": "Memeriksa gate release...", "recovery_txn_id": ""},
            "prompt_options": [],
            "primary_prompt_id": "",
            "primary_prompt_name": "",
            "primary_active_revision": "",
            "primary_source": "",
            "primary_source_name": "",
            "reason": "",
            "summary": "",
            "sync_changes": [],
            "plan": {},
            "warnings": [],
            "result": {},
            "recovery_result": {},
            "error_code": "",
            "error_message": "",
        }
