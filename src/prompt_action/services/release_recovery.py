from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from prompt_action.data.release_repository import ReleaseRepository, sha256_path
from prompt_action.data.repository import VersionRepository
from prompt_action.data.transaction_journal import TERMINAL_PHASES, TransactionJournalStore
from prompt_action.domain.errors import ReleaseWorkflowError, RevisionConflictError, ValidationBlockedError
from prompt_action.services.release_planner import ReleaseChange, ReleasePlan
from prompt_action.services.release_service import ReleaseService


@dataclass(frozen=True, slots=True)
class RecoveryState:
    txn_id: str
    phase: str
    snapshot_id: str
    parent_snapshot: str
    expected_app_data_revision: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "txn_id": self.txn_id,
            "phase": self.phase,
            "snapshot_id": self.snapshot_id,
            "parent_snapshot": self.parent_snapshot,
            "expected_app_data_revision": self.expected_app_data_revision,
        }


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    txn_id: str
    strategy: str
    phase: str
    snapshot_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "txn_id": self.txn_id,
            "strategy": self.strategy,
            "phase": self.phase,
            "snapshot_id": self.snapshot_id,
        }


def _change(value: dict[str, Any]) -> ReleaseChange:
    return ReleaseChange(
        prompt_id=str(value["prompt_id"]), role=str(value["role"]),
        from_revision=str(value["from_revision"]), to_revision=str(value["to_revision"]),
        source_path=str(value["source_path"]), target_relative=str(value["target_relative"]),
        source_sha256=str(value["source_sha256"]), source_size=int(value["source_size"]),
        summary=tuple(str(item) for item in value.get("summary", [])), reason=str(value.get("reason", "")),
    )


def _plan(value: dict[str, Any]) -> ReleasePlan:
    return ReleasePlan(
        expected_app_data_revision=int(value["expected_app_data_revision"]),
        expected_canonical_sha256=str(value["expected_canonical_sha256"]),
        app_version=str(value["app_version"]), system=str(value["system"]),
        parent_snapshot=str(value["parent_snapshot"]), snapshot_id=str(value["snapshot_id"]),
        primary=_change(value["primary"]), sync=tuple(_change(item) for item in value.get("sync", [])),
        prompt_state={str(k): str(v) for k, v in value["prompt_state"].items()},
        warnings=tuple(str(item) for item in value.get("warnings", [])),
        confirmation_token=str(value["confirmation_token"]),
        resulting_status=str(value.get("resulting_status", "BACKUP_REQUIRED")),
    )


class ReleaseRecoveryService:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.journals = TransactionJournalStore(self.project_root)
        self.release_repository = ReleaseRepository(self.project_root)
        self.version_repository = VersionRepository(self.project_root)

    def inspect_pending_transaction(self) -> RecoveryState | None:
        pending = self.journals.inspect_pending()
        if pending is None:
            return None
        return RecoveryState(
            txn_id=str(pending["txn_id"]),
            phase=str(pending["phase"]),
            snapshot_id=str(pending["snapshot_id"]),
            parent_snapshot=str(pending["parent_snapshot"]),
            expected_app_data_revision=int(pending["expected_app_data_revision"]),
        )

    def _load_plan(self, journal: dict[str, Any]) -> ReleasePlan:
        value = journal.get("plan")
        if not isinstance(value, dict):
            plan_path = self.journals.txn_dir(str(journal["txn_id"])) / "plan.json"
            try:
                value = json.loads(plan_path.read_text(encoding="utf-8"))
            except Exception as exc:
                raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Release plan is unavailable for recovery: {exc}") from exc
        try:
            return _plan(value)
        except Exception as exc:
            raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Release plan is invalid for recovery: {exc}") from exc

    def _canonical_committed(self, plan: ReleasePlan) -> bool:
        state = self.version_repository.load()
        return state.app_data_revision == plan.expected_app_data_revision + 1 and state.active_snapshot == plan.snapshot_id

    def _canonical_still_parent(self, plan: ReleasePlan) -> bool:
        state = self.version_repository.load()
        return (
            state.app_data_revision == plan.expected_app_data_revision
            and state.active_snapshot == plan.parent_snapshot
            and self.release_repository.canonical_sha256() == plan.expected_canonical_sha256
        )

    def _rollback_targets(self, plan: ReleasePlan) -> None:
        for item in reversed(plan.changes):
            target = self.release_repository.safe_project_path(item.target_relative)
            self.release_repository.remove_if_exact(target, item.source_sha256)

    def recover_transaction(self, txn_id: str, strategy: str) -> RecoveryResult:
        journal = self.journals.load(txn_id)
        if journal.get("phase") in TERMINAL_PHASES:
            return RecoveryResult(txn_id, strategy, str(journal["phase"]), str(journal["snapshot_id"]))
        if strategy not in {"abort", "resume"}:
            raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Unsupported recovery strategy: {strategy}")
        plan = self._load_plan(journal)
        self.release_repository.clear_stale_lock(expected_txn_id=txn_id)

        if strategy == "abort":
            if self._canonical_committed(plan):
                raise ReleaseWorkflowError("RECOVERY_REQUIRED", "Canonical metadata is already committed; use resume to verify/finalize")
            if not self._canonical_still_parent(plan):
                raise ReleaseWorkflowError("STATE_CHANGED_RELOAD_REQUIRED", "Canonical state no longer matches the transaction parent")
            with self.release_repository.exclusive_lock(txn_id):
                self._rollback_targets(plan)
                self.journals.update(txn_id, "ABORTED", recovery_strategy="abort")
            return RecoveryResult(txn_id, "abort", "ABORTED", plan.snapshot_id)

        service = ReleaseService(self.project_root)
        if self._canonical_committed(plan):
            revision, canonical_sha = service._post_commit_verify(plan)
            self.journals.update(
                txn_id, "COMMITTED", recovery_strategy="resume-verify",
                resulting_app_data_revision=revision, resulting_canonical_sha256=canonical_sha,
            )
            return RecoveryResult(txn_id, "resume", "COMMITTED", plan.snapshot_id)
        if not self._canonical_still_parent(plan):
            raise ReleaseWorkflowError("STATE_CHANGED_RELOAD_REQUIRED", "Canonical state changed; automatic resume is unsafe")

        txn_dir = self.journals.txn_dir(txn_id)
        try:
            candidate = json.loads((txn_dir / "candidate_version_history.json").read_text(encoding="utf-8"))
        except Exception as exc:
            raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Candidate canonical metadata is unavailable: {exc}") from exc
        staged = journal.get("staged")
        if not isinstance(staged, dict):
            try:
                staged = json.loads((txn_dir / "manifest.json").read_text(encoding="utf-8"))["staged"]
            except Exception as exc:
                raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Staged manifest is unavailable: {exc}") from exc

        with self.release_repository.exclusive_lock(txn_id):
            for item in plan.changes:
                target = self.release_repository.safe_project_path(item.target_relative)
                if target.exists():
                    if not target.is_file() or sha256_path(target) != item.source_sha256:
                        raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Existing target conflicts with recovery: {item.prompt_id}")
                    continue
                rel = staged.get(item.prompt_id)
                if not isinstance(rel, str):
                    raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Missing staged source for {item.prompt_id}")
                staged_path = (txn_dir / rel).resolve()
                try:
                    staged_path.relative_to(txn_dir.resolve())
                except ValueError as exc:
                    raise ReleaseWorkflowError("PATH_POLICY_BLOCKED", "Staged path escapes transaction directory") from exc
                if not staged_path.is_file() or sha256_path(staged_path) != item.source_sha256:
                    raise ReleaseWorkflowError("HASH_MISMATCH", f"Staged bytes failed recovery verification: {item.prompt_id}")
                self.release_repository.place_new_file(target, staged_path.read_bytes(), item.source_sha256)
            report = self.version_repository.validate(candidate)
            if not report.is_valid:
                raise ReleaseWorkflowError("CANONICAL_COMMIT_FAILED", "Recovered candidate metadata failed validation")
            try:
                self.version_repository.save(candidate, expected_revision=plan.expected_app_data_revision)
            except RevisionConflictError as exc:
                raise ReleaseWorkflowError("STATE_CHANGED_RELOAD_REQUIRED", str(exc)) from exc
            except ValidationBlockedError as exc:
                raise ReleaseWorkflowError("CANONICAL_COMMIT_FAILED", str(exc)) from exc
            except Exception as exc:
                self.journals.update(txn_id, "RECOVERY_REQUIRED", error={"code": "CANONICAL_COMMIT_FAILED", "message": str(exc)})
                raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Canonical recovery commit outcome is ambiguous: {exc}") from exc
            revision, canonical_sha = service._post_commit_verify(plan)
            self.journals.update(
                txn_id, "COMMITTED", recovery_strategy="resume",
                resulting_app_data_revision=revision, resulting_canonical_sha256=canonical_sha,
            )
        return RecoveryResult(txn_id, "resume", "COMMITTED", plan.snapshot_id)
