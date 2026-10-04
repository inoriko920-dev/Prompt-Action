from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import uuid
from typing import Any, Callable

from prompt_action.data.atomic_writer import atomic_write_bytes, atomic_write_json, atomic_write_text
from prompt_action.data.release_repository import ReleaseRepository, sha256_path
from prompt_action.data.repository import VersionRepository
from prompt_action.data.transaction_journal import TransactionJournalStore
from prompt_action.domain.errors import (
    ReleaseWorkflowError,
    RevisionConflictError,
    ValidationBlockedError,
)
from prompt_action.domain.models import Severity, ValidationReport
from prompt_action.services.release_planner import ReleaseChange, ReleasePlan, ReleasePlanner

FaultInjector = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class ReleaseResult:
    txn_id: str
    snapshot_id: str
    app_data_revision: int
    canonical_sha256: str
    changed_prompts: tuple[str, ...]
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "txn_id": self.txn_id,
            "snapshot_id": self.snapshot_id,
            "app_data_revision": self.app_data_revision,
            "canonical_sha256": self.canonical_sha256,
            "changed_prompts": list(self.changed_prompts),
            "status": self.status,
        }


def build_candidate_document(current: dict[str, Any], plan: ReleasePlan) -> dict[str, Any]:
    doc = deepcopy(current)
    if plan.snapshot_id in {item.get("id") for item in doc.get("snapshots", [])}:
        raise ReleaseWorkflowError("SNAPSHOT_ID_CONFLICT", f"Snapshot already exists: {plan.snapshot_id}")
    for item in plan.changes:
        prompt = doc["prompts"][item.prompt_id]
        if prompt.get("active_revision") != item.from_revision:
            raise ReleaseWorkflowError("STATE_CHANGED_RELOAD_REQUIRED", f"Active revision changed for {item.prompt_id}")
        if item.to_revision in prompt["revisions"]:
            raise ReleaseWorkflowError("REVISION_TARGET_EXISTS", f"Revision ID already exists: {item.prompt_id}:{item.to_revision}")
        prompt["revisions"][item.from_revision]["status"] = "SUPERSEDED"
        prompt["revisions"][item.to_revision] = {
            "parent": item.from_revision,
            "snapshot": plan.snapshot_id,
            "status": "ACTIVE",
            "file": item.target_relative,
            "sha256": item.source_sha256,
            "file_available": True,
            "change_role": item.role,
            "summary": list(item.summary),
            "reason": item.reason,
        }
        prompt["active_revision"] = item.to_revision
    doc["snapshots"].append({
        "id": plan.snapshot_id,
        "system": plan.system,
        "parent_snapshot": plan.parent_snapshot,
        "status": "BACKUP_REQUIRED",
        "primary_change": {
            "prompt_id": plan.primary.prompt_id,
            "from": plan.primary.from_revision,
            "to": plan.primary.to_revision,
        },
        "sync_changes": [
            {"prompt_id": item.prompt_id, "from": item.from_revision, "to": item.to_revision}
            for item in plan.sync
        ],
        "prompt_state": deepcopy(plan.prompt_state),
        "backup_id": None,
    })
    doc["active_snapshot"] = plan.snapshot_id
    system = next((item for item in doc["systems"] if item.get("id") == plan.system), None)
    if system is None:
        raise ReleaseWorkflowError("STATE_CHANGED_RELOAD_REQUIRED", f"Active system disappeared: {plan.system}")
    system["latest_snapshot"] = plan.snapshot_id
    doc["app_data_revision"] = plan.expected_app_data_revision + 1
    return doc


class ReleaseService:
    def __init__(self, project_root: Path, *, fault_injector: FaultInjector | None = None):
        self.project_root = project_root.resolve()
        self.version_repository = VersionRepository(self.project_root)
        self.release_repository = ReleaseRepository(self.project_root)
        self.journals = TransactionJournalStore(self.project_root)
        self.planner = ReleasePlanner(self.project_root)
        self.fault_injector = fault_injector

    def _fault(self, phase: str) -> None:
        if self.fault_injector is not None:
            self.fault_injector(phase)

    def plan_release(self, **kwargs: Any) -> ReleasePlan:
        return self.planner.plan_release(**kwargs)

    def _state_matches_plan(self, plan: ReleasePlan) -> bool:
        state = self.version_repository.load()
        return (
            state.app_data_revision == plan.expected_app_data_revision
            and state.app_version == plan.app_version
            and state.active_system == plan.system
            and state.active_snapshot == plan.parent_snapshot
            and self.release_repository.canonical_sha256() == plan.expected_canonical_sha256
        )

    def validate_plan(self, plan: ReleasePlan, expected_state: dict[str, Any] | None = None) -> ValidationReport:
        report = ValidationReport()
        try:
            state = self.version_repository.load()
            live = state.document
            baseline = expected_state if expected_state is not None else live
            if baseline.get("app_data_revision") != plan.expected_app_data_revision:
                report.add("STATE_CHANGED_RELOAD_REQUIRED", Severity.BLOCKING, "release", "app_data_revision", "Canonical app_data_revision changed after planning.")
            if live.get("app_version") != plan.app_version or live.get("active_system") != plan.system or live.get("active_snapshot") != plan.parent_snapshot:
                report.add("STATE_CHANGED_RELOAD_REQUIRED", Severity.BLOCKING, "release", "active_context", "Active release context changed after planning.")
            if self.release_repository.canonical_sha256() != plan.expected_canonical_sha256:
                report.add("STATE_CHANGED_RELOAD_REQUIRED", Severity.BLOCKING, "release", "canonical_sha256", "Canonical bytes changed after planning.")
            if any(item.get("id") == plan.snapshot_id for item in live.get("snapshots", [])):
                report.add("SNAPSHOT_ID_CONFLICT", Severity.BLOCKING, plan.snapshot_id, "snapshots", "Planned snapshot ID already exists.")
            for item in plan.changes:
                source = Path(item.source_path)
                if not source.is_file() or source.is_symlink():
                    report.add("HASH_MISMATCH", Severity.BLOCKING, item.prompt_id, "source_path", "Candidate source disappeared or became unsafe.")
                    continue
                if source.stat().st_size != item.source_size or sha256_path(source) != item.source_sha256:
                    report.add("HASH_MISMATCH", Severity.BLOCKING, item.prompt_id, "source_sha256", "Candidate source changed after planning.")
                target = self.release_repository.safe_project_path(item.target_relative)
                if target.exists():
                    report.add("REVISION_TARGET_EXISTS", Severity.BLOCKING, item.prompt_id, "target_relative", "Planned immutable revision target already exists.")
            for warning in plan.warnings:
                report.add("RELEASE_WARNING", Severity.WARNING, "release", "warnings", warning)
        except ReleaseWorkflowError as exc:
            report.add(exc.code, Severity.BLOCKING, "release", "preflight", exc.message)
        except Exception as exc:
            report.add("RECOVERY_REQUIRED", Severity.BLOCKING, "release", "preflight", str(exc))
        return report

    @staticmethod
    def _txn_id(plan: ReleasePlan) -> str:
        return f"{plan.snapshot_id.lower()}-{uuid.uuid4().hex[:16]}"

    def _write_staging(self, txn_id: str, plan: ReleasePlan, candidate: dict[str, Any]) -> dict[str, str]:
        txn_dir = self.journals.txn_dir(txn_id)
        staged: dict[str, str] = {}
        for item in plan.changes:
            source = Path(item.source_path)
            raw = source.read_bytes()
            if len(raw) != item.source_size or hashlib.sha256(raw).hexdigest() != item.source_sha256:
                raise ReleaseWorkflowError("HASH_MISMATCH", f"Candidate source changed while staging: {item.prompt_id}")
            staged_rel = f"staged/{item.prompt_id}_{item.to_revision}.txt"
            staged_path = txn_dir / staged_rel
            atomic_write_bytes(staged_path, raw)
            if sha256_path(staged_path) != item.source_sha256:
                raise ReleaseWorkflowError("HASH_MISMATCH", f"Staged copy hash mismatch: {item.prompt_id}")
            staged[item.prompt_id] = staged_rel
        atomic_write_json(txn_dir / "plan.json", plan.to_dict())
        atomic_write_json(txn_dir / "candidate_version_history.json", candidate)
        manifest = {
            "txn_id": txn_id,
            "snapshot_id": plan.snapshot_id,
            "parent_snapshot": plan.parent_snapshot,
            "expected_app_data_revision": plan.expected_app_data_revision,
            "expected_canonical_sha256": plan.expected_canonical_sha256,
            "resulting_status": "BACKUP_REQUIRED",
            "staged": staged,
            "changes": [item.to_dict() for item in plan.changes],
        }
        atomic_write_json(txn_dir / "manifest.json", manifest)
        changelog = [f"# Release {plan.snapshot_id}", "", f"Parent: {plan.parent_snapshot}", "Status after STEP 10: BACKUP_REQUIRED", ""]
        for item in plan.changes:
            changelog.append(f"- {item.role} {item.prompt_id}: {item.from_revision} -> {item.to_revision}")
        atomic_write_text(txn_dir / "CHANGELOG.md", "\n".join(changelog) + "\n")
        return staged

    def _post_commit_verify(self, plan: ReleasePlan) -> tuple[int, str]:
        state = self.version_repository.load()
        report = self.version_repository.validate(state)
        if not report.is_valid:
            raise ReleaseWorkflowError("POST_COMMIT_INVALID", "Canonical state is invalid after commit")
        if state.app_data_revision != plan.expected_app_data_revision + 1 or state.active_snapshot != plan.snapshot_id:
            raise ReleaseWorkflowError("POST_COMMIT_INVALID", "Committed canonical identity does not match release plan")
        snapshot = next((item for item in state.document["snapshots"] if item.get("id") == plan.snapshot_id), None)
        if not snapshot or snapshot.get("status") != "BACKUP_REQUIRED" or snapshot.get("backup_id") is not None:
            raise ReleaseWorkflowError("POST_COMMIT_INVALID", "New snapshot must remain BACKUP_REQUIRED after STEP 10")
        for item in plan.changes:
            target = self.release_repository.safe_project_path(item.target_relative)
            if not target.is_file() or sha256_path(target) != item.source_sha256:
                raise ReleaseWorkflowError("POST_COMMIT_INVALID", f"Committed revision file failed verification: {item.prompt_id}")
        return state.app_data_revision, self.release_repository.canonical_sha256()

    def _rollback_files(self, plan: ReleasePlan) -> None:
        for item in reversed(plan.changes):
            target = self.release_repository.safe_project_path(item.target_relative)
            self.release_repository.remove_if_exact(target, item.source_sha256)

    def commit_release(self, plan: ReleasePlan, explicit_confirmation_token: str) -> ReleaseResult:
        if explicit_confirmation_token != plan.confirmation_token:
            raise ReleaseWorkflowError("USER_CANCELLED", "Explicit release confirmation token was not accepted")
        pending = self.journals.inspect_pending()
        if pending is not None:
            raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Recover unresolved transaction first: {pending.get('txn_id')}")
        validation = self.validate_plan(plan)
        if not validation.is_valid:
            issue = (validation.blocking_issues + validation.errors)[0]
            raise ReleaseWorkflowError(issue.code, issue.message)
        txn_id = self._txn_id(plan)
        committed_or_ambiguous = False
        placed = False
        with self.release_repository.exclusive_lock(txn_id):
            if not self._state_matches_plan(plan):
                raise ReleaseWorkflowError("STATE_CHANGED_RELOAD_REQUIRED", "Canonical state changed before transaction start")
            current = self.version_repository.load().document
            candidate = build_candidate_document(current, plan)
            required_bytes = sum(item.source_size for item in plan.changes) + len(json.dumps(candidate).encode("utf-8"))
            self.release_repository.require_free_space(required_bytes)
            self.journals.create(txn_id, {
                "snapshot_id": plan.snapshot_id,
                "parent_snapshot": plan.parent_snapshot,
                "expected_app_data_revision": plan.expected_app_data_revision,
                "expected_canonical_sha256": plan.expected_canonical_sha256,
                "confirmation_token": plan.confirmation_token,
                "plan": plan.to_dict(),
                "placed_targets": [],
            })
            try:
                self._fault("PREPARING")
                staged = self._write_staging(txn_id, plan, candidate)
                self.journals.update(txn_id, "STAGED", staged=staged)
                self._fault("STAGED")
                self.journals.update(txn_id, "PLACING_FILES")
                self._fault("PLACING_FILES")
                placed_targets: list[str] = []
                for item in plan.changes:
                    staged_path = self.journals.txn_dir(txn_id) / staged[item.prompt_id]
                    raw = staged_path.read_bytes()
                    target = self.release_repository.safe_project_path(item.target_relative)
                    self.release_repository.place_new_file(target, raw, item.source_sha256)
                    placed_targets.append(item.target_relative)
                    self.journals.update(txn_id, "PLACING_FILES", placed_targets=list(placed_targets), staged=staged)
                placed = bool(placed_targets)
                self.journals.update(txn_id, "FILES_PLACED", placed_targets=placed_targets, staged=staged)
                self._fault("FILES_PLACED")
                candidate_report = self.version_repository.validate(candidate)
                if not candidate_report.is_valid:
                    raise ReleaseWorkflowError("CANONICAL_COMMIT_FAILED", "Candidate canonical metadata failed validation")
                if not self._state_matches_plan(plan):
                    raise ReleaseWorkflowError("STATE_CHANGED_RELOAD_REQUIRED", "Canonical state changed before metadata commit")
                self.journals.update(txn_id, "COMMITTING_METADATA", placed_targets=placed_targets, staged=staged)
                self._fault("COMMITTING_METADATA")
                try:
                    self.version_repository.save(candidate, expected_revision=plan.expected_app_data_revision)
                    committed_or_ambiguous = True
                except RevisionConflictError as exc:
                    raise ReleaseWorkflowError("STATE_CHANGED_RELOAD_REQUIRED", str(exc)) from exc
                except ValidationBlockedError as exc:
                    raise ReleaseWorkflowError("CANONICAL_COMMIT_FAILED", str(exc)) from exc
                except Exception as exc:
                    committed_or_ambiguous = True
                    raise ReleaseWorkflowError("CANONICAL_COMMIT_FAILED", f"Canonical atomic save failed: {exc}") from exc
                self._fault("METADATA_COMMITTED")
                revision, canonical_sha = self._post_commit_verify(plan)
                self.journals.update(
                    txn_id, "COMMITTED",
                    placed_targets=placed_targets,
                    resulting_app_data_revision=revision,
                    resulting_canonical_sha256=canonical_sha,
                )
                self._fault("COMMITTED")
                return ReleaseResult(
                    txn_id=txn_id,
                    snapshot_id=plan.snapshot_id,
                    app_data_revision=revision,
                    canonical_sha256=canonical_sha,
                    changed_prompts=tuple(item.prompt_id for item in plan.changes),
                    status="BACKUP_REQUIRED",
                )
            except ReleaseWorkflowError as exc:
                live = self.version_repository.load().document
                canonical_has_snapshot = live.get("active_snapshot") == plan.snapshot_id and live.get("app_data_revision") == plan.expected_app_data_revision + 1
                if canonical_has_snapshot or committed_or_ambiguous:
                    self.journals.update(txn_id, "RECOVERY_REQUIRED", error=exc.to_dict())
                    raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Release outcome is ambiguous and requires recovery: {exc.message}") from exc
                try:
                    if placed:
                        self._rollback_files(plan)
                    self.journals.update(txn_id, "ABORTED", error=exc.to_dict())
                except ReleaseWorkflowError as rollback_exc:
                    self.journals.update(txn_id, "RECOVERY_REQUIRED", error=rollback_exc.to_dict())
                    raise
                raise
            except Exception as exc:
                live = self.version_repository.load().document
                canonical_has_snapshot = live.get("active_snapshot") == plan.snapshot_id and live.get("app_data_revision") == plan.expected_app_data_revision + 1
                if canonical_has_snapshot or committed_or_ambiguous:
                    self.journals.update(txn_id, "RECOVERY_REQUIRED", error={"code": "RECOVERY_REQUIRED", "message": str(exc)})
                    raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Release interrupted after commit boundary: {exc}") from exc
                try:
                    if placed:
                        self._rollback_files(plan)
                    self.journals.update(txn_id, "ABORTED", error={"code": "CANONICAL_COMMIT_FAILED", "message": str(exc)})
                except Exception as rollback_exc:
                    self.journals.update(txn_id, "RECOVERY_REQUIRED", error={"code": "RECOVERY_REQUIRED", "message": str(rollback_exc)})
                    raise ReleaseWorkflowError("RECOVERY_REQUIRED", str(rollback_exc)) from rollback_exc
                raise ReleaseWorkflowError("CANONICAL_COMMIT_FAILED", str(exc)) from exc
