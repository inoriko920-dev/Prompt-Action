from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Callable
import uuid

from prompt_action.data.backup_repository import BackupRepository, sha256_path
from prompt_action.data.backup_transaction_journal import BackupTransactionJournalStore
from prompt_action.data.repository import VersionRepository
from prompt_action.data.transaction_journal import TransactionJournalStore
from prompt_action.domain.errors import BackupWorkflowError
from prompt_action.services.backup_allocator import allocate_backup
from prompt_action.services.backup_secret_scanner import scan_sources


@dataclass(frozen=True, slots=True)
class BackupEntryPlan:
    path: str
    logical_type: str
    size: int
    sha256: str
    source_path: str | None = None
    generated_text: str | None = None

    def payload_bytes(self, project_root: Path) -> bytes:
        if self.generated_text is not None:
            return self.generated_text.encode("utf-8")
        if not self.source_path:
            raise BackupWorkflowError("BACKUP_PLAN_INVALID", f"Backup entry has no source: {self.path}")
        return (project_root / self.source_path).read_bytes()

    def to_dict(self, *, include_internal: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {
            "path": self.path,
            "size": self.size,
            "sha256": self.sha256,
            "logical_type": self.logical_type,
        }
        if include_internal:
            result["source_path"] = self.source_path
            result["generated_text"] = self.generated_text
        return result

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "BackupEntryPlan":
        return cls(
            path=str(value["path"]),
            logical_type=str(value["logical_type"]),
            size=int(value["size"]),
            sha256=str(value["sha256"]),
            source_path=value.get("source_path"),
            generated_text=value.get("generated_text"),
        )


@dataclass(frozen=True, slots=True)
class BackupPlan:
    transaction_id: str
    backup_id: str
    expected_app_data_revision: int
    expected_canonical_sha256: str
    app_version: str
    system: str
    snapshot_id: str
    snapshot_status_at_start: str
    created_at_utc: str
    entries: tuple[BackupEntryPlan, ...]
    prompt_composition: dict[str, str]
    manifest: dict[str, Any]
    primary_zip: str
    primary_sha256: str
    primary_record: str
    secondary_zip: str
    secondary_sha256: str
    secondary_record: str
    estimated_payload_bytes: int

    def to_dict(self, *, include_internal: bool = True) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "backup_id": self.backup_id,
            "expected_app_data_revision": self.expected_app_data_revision,
            "expected_canonical_sha256": self.expected_canonical_sha256,
            "app_version": self.app_version,
            "system": self.system,
            "snapshot_id": self.snapshot_id,
            "snapshot_status_at_start": self.snapshot_status_at_start,
            "created_at_utc": self.created_at_utc,
            "entries": [item.to_dict(include_internal=include_internal) for item in self.entries],
            "prompt_composition": dict(self.prompt_composition),
            "manifest": self.manifest,
            "primary_zip": self.primary_zip,
            "primary_sha256": self.primary_sha256,
            "primary_record": self.primary_record,
            "secondary_zip": self.secondary_zip,
            "secondary_sha256": self.secondary_sha256,
            "secondary_record": self.secondary_record,
            "estimated_payload_bytes": self.estimated_payload_bytes,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "BackupPlan":
        return cls(
            transaction_id=str(value["transaction_id"]),
            backup_id=str(value["backup_id"]),
            expected_app_data_revision=int(value["expected_app_data_revision"]),
            expected_canonical_sha256=str(value["expected_canonical_sha256"]),
            app_version=str(value["app_version"]),
            system=str(value["system"]),
            snapshot_id=str(value["snapshot_id"]),
            snapshot_status_at_start=str(value["snapshot_status_at_start"]),
            created_at_utc=str(value["created_at_utc"]),
            entries=tuple(BackupEntryPlan.from_dict(item) for item in value["entries"]),
            prompt_composition={str(k): str(v) for k, v in value["prompt_composition"].items()},
            manifest=dict(value["manifest"]),
            primary_zip=str(value["primary_zip"]),
            primary_sha256=str(value["primary_sha256"]),
            primary_record=str(value["primary_record"]),
            secondary_zip=str(value["secondary_zip"]),
            secondary_sha256=str(value["secondary_sha256"]),
            secondary_record=str(value["secondary_record"]),
            estimated_payload_bytes=int(value["estimated_payload_bytes"]),
        )


class BackupPlanner:
    def __init__(
        self,
        project_root: Path,
        *,
        primary_root: Path | None = None,
        second_root: Path | None = None,
        now: Callable[[], datetime] | None = None,
        transaction_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.version_repository = VersionRepository(self.project_root)
        self.backup_repository = BackupRepository(
            self.project_root, primary_root=primary_root, second_root=second_root
        )
        self.backup_journals = BackupTransactionJournalStore(self.project_root)
        self.release_journals = TransactionJournalStore(self.project_root)
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._transaction_id_factory = transaction_id_factory or (
            lambda: f"bk-{uuid.uuid4().hex[:16]}"
        )

    @staticmethod
    def _safe_source(project_root: Path, relative: str, *, logical: str) -> Path:
        path = (project_root / relative).resolve()
        try:
            path.relative_to(project_root)
        except ValueError as exc:
            raise BackupWorkflowError("PATH_POLICY_BLOCKED", f"Source escapes project root: {relative}") from exc
        if not path.is_file() or path.is_symlink():
            raise BackupWorkflowError("SOURCE_UNAVAILABLE", f"Backup source is missing/unsafe: {logical}")
        return path

    @staticmethod
    def _entry_from_file(project_root: Path, relative: str, logical_type: str) -> BackupEntryPlan:
        path = BackupPlanner._safe_source(project_root, relative, logical=relative)
        return BackupEntryPlan(
            path=relative.replace("\\", "/"),
            logical_type=logical_type,
            size=path.stat().st_size,
            sha256=sha256_path(path),
            source_path=relative.replace("\\", "/"),
        )

    @staticmethod
    def _entry_from_text(path: str, logical_type: str, text: str) -> BackupEntryPlan:
        payload = text.encode("utf-8")
        return BackupEntryPlan(
            path=path,
            logical_type=logical_type,
            size=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
            generated_text=text,
        )

    def _verify_revision_sources(self, document: dict[str, Any]) -> list[BackupEntryPlan]:
        entries: list[BackupEntryPlan] = []
        seen_paths: set[str] = set()
        for prompt_id, prompt in document.get("prompts", {}).items():
            if not isinstance(prompt, dict):
                raise BackupWorkflowError("CANONICAL_INVALID", f"Invalid prompt record: {prompt_id}")
            revisions = prompt.get("revisions", {})
            if not isinstance(revisions, dict) or not revisions:
                raise BackupWorkflowError("CANONICAL_INVALID", f"Prompt has no revisions: {prompt_id}")
            for revision_id, revision in revisions.items():
                if not isinstance(revision, dict):
                    raise BackupWorkflowError("CANONICAL_INVALID", f"Invalid revision: {prompt_id}:{revision_id}")
                relative = revision.get("file")
                expected = revision.get("sha256")
                if revision.get("file_available") is not True or not isinstance(relative, str) or not isinstance(expected, str):
                    raise BackupWorkflowError(
                        "SOURCE_UNAVAILABLE",
                        f"Official revision is not materialized: {prompt_id}:{revision_id}",
                    )
                normalized = relative.replace("\\", "/")
                if normalized in seen_paths:
                    raise BackupWorkflowError("BACKUP_PLAN_INVALID", f"Duplicate revision source path: {normalized}")
                seen_paths.add(normalized)
                path = self._safe_source(self.project_root, relative, logical=f"{prompt_id}:{revision_id}")
                actual = sha256_path(path)
                if actual != expected:
                    raise BackupWorkflowError(
                        "SOURCE_HASH_CHANGED",
                        f"Official revision SHA mismatch: {prompt_id}:{revision_id}",
                    )
                entries.append(
                    BackupEntryPlan(
                        path=normalized,
                        logical_type="PROMPT_REVISION",
                        size=path.stat().st_size,
                        sha256=actual,
                        source_path=normalized,
                    )
                )
        return entries

    def plan_backup(self) -> BackupPlan:
        if self.release_journals.inspect_pending() is not None:
            raise BackupWorkflowError("RELEASE_TRANSACTION_ACTIVE", "Resolve STEP 10 release transaction before backup")
        if self.backup_journals.inspect_pending() is not None:
            raise BackupWorkflowError("BACKUP_RECOVERY_REQUIRED", "Resolve existing backup transaction first")

        state = self.version_repository.load()
        report = self.version_repository.validate(state)
        if not report.is_valid:
            raise BackupWorkflowError("CANONICAL_INVALID", "Canonical data is invalid before backup planning")
        document = state.document
        snapshot = next(
            (item for item in document.get("snapshots", []) if item.get("id") == state.active_snapshot),
            None,
        )
        if not isinstance(snapshot, dict):
            raise BackupWorkflowError("CANONICAL_INVALID", "Active Snapshot is missing")
        if snapshot.get("status") != "BACKUP_REQUIRED":
            raise BackupWorkflowError(
                "SNAPSHOT_NOT_BACKUP_REQUIRED",
                f"STEP 11 requires BACKUP_REQUIRED; found {snapshot.get('status')!r}",
            )
        if snapshot.get("backup_id") is not None:
            raise BackupWorkflowError("CANONICAL_INVALID", "BACKUP_REQUIRED Snapshot must not already point to a backup")

        prompt_composition = {
            str(prompt_id): str(revision_id)
            for prompt_id, revision_id in snapshot.get("prompt_state", {}).items()
        }
        if set(prompt_composition) != set(document.get("prompts", {})):
            raise BackupWorkflowError("CANONICAL_INVALID", "Snapshot prompt composition is incomplete")

        entries = self._verify_revision_sources(document)
        required_files = (
            ("data/version_history.json", "CANONICAL_METADATA"),
            ("docs/CHANGELOG.md", "CHANGELOG"),
            ("docs/VERSIONING_RULES.md", "RECOVERY_GUIDE"),
        )
        for relative, logical_type in required_files:
            entries.append(self._entry_from_file(self.project_root, relative, logical_type))
        baseline = self.project_root / "BASELINE.json"
        if baseline.is_file() and not baseline.is_symlink():
            entries.append(self._entry_from_file(self.project_root, "BASELINE.json", "LEGACY_BASELINE"))

        schema_marker = {
            "backup_schema": "prompt-action-backup/v1",
            "canonical_schema_version": document.get("schema_version"),
            "app_version": document.get("app_version"),
            "system": state.active_system,
            "snapshot": state.active_snapshot,
        }
        schema_text = json.dumps(schema_marker, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        entries.append(self._entry_from_text("backup/schema.json", "SCHEMA_MARKER", schema_text))

        # Deterministic path set, with the manifest itself written separately.
        entries = sorted(entries, key=lambda item: item.path)
        paths = [item.path for item in entries]
        if len(paths) != len(set(paths)):
            raise BackupWorkflowError("BACKUP_PLAN_INVALID", "Backup entry paths are not unique")

        transaction_id = self._transaction_id_factory()
        created_at = self._now().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        backup_id = allocate_backup([str(item.get("id")) for item in document.get("backups", []) if isinstance(item, dict)])
        primary = self.backup_repository.primary_paths(state.active_system, state.active_snapshot)
        secondary = self.backup_repository.secondary_paths(state.active_system, state.active_snapshot)
        for target in (*primary.values(), *secondary.values()):
            if target.name in {"", ".", ".."}:
                raise BackupWorkflowError("PATH_POLICY_BLOCKED", "Invalid backup target")
        for target in (primary["zip"], primary["sha256"], primary["record"], secondary["zip"], secondary["sha256"], secondary["record"]):
            if target.exists():
                raise BackupWorkflowError("BACKUP_TARGET_EXISTS", f"Historical backup target already exists: {target}")

        canonical_sha = sha256_path(self.project_root / "data/version_history.json")
        manifest: dict[str, Any] = {
            "manifest_schema": "prompt-action-backup/v1",
            "system_version": state.active_system,
            "snapshot_id": state.active_snapshot,
            "snapshot_status_at_start": "BACKUP_REQUIRED",
            "created_at_utc": created_at,
            "app_version": state.app_version,
            "canonical_metadata_sha256": canonical_sha,
            "entries": [item.to_dict() for item in entries],
            "prompt_composition": prompt_composition,
            "excluded_classes": [
                ".git",
                ".venv",
                "runtime_logs_temp_cache",
                "generated_cache",
                "credentials_secrets",
                "second_copy_root",
            ],
            "verification_policy": "reopen+entry-sha+safe-extract+canonical-parse+utf8-prompts+secondary-independent-sha",
            "transaction_id": transaction_id,
        }

        scan_inputs: list[tuple[str, bytes]] = []
        for item in entries:
            scan_inputs.append((item.path, item.payload_bytes(self.project_root)))
        manifest_text = json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        scan_inputs.append(("backup/manifest.json", manifest_text.encode("utf-8")))
        scan_sources(scan_inputs)

        estimated = sum(item.size for item in entries) + len(manifest_text.encode("utf-8"))
        self.backup_repository.require_free_space(estimated_payload_bytes=estimated)

        return BackupPlan(
            transaction_id=transaction_id,
            backup_id=backup_id,
            expected_app_data_revision=state.app_data_revision,
            expected_canonical_sha256=canonical_sha,
            app_version=state.app_version,
            system=state.active_system,
            snapshot_id=state.active_snapshot,
            snapshot_status_at_start="BACKUP_REQUIRED",
            created_at_utc=created_at,
            entries=tuple(entries),
            prompt_composition=prompt_composition,
            manifest=manifest,
            primary_zip=self.backup_repository.display_path(primary["zip"]),
            primary_sha256=self.backup_repository.display_path(primary["sha256"]),
            primary_record=self.backup_repository.display_path(primary["record"]),
            secondary_zip=self.backup_repository.display_path(secondary["zip"]),
            secondary_sha256=self.backup_repository.display_path(secondary["sha256"]),
            secondary_record=self.backup_repository.display_path(secondary["record"]),
            estimated_payload_bytes=estimated,
        )
