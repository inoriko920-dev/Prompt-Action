from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from prompt_action.data.release_repository import ReleaseRepository, sha256_path
from prompt_action.data.repository import VersionRepository
from prompt_action.data.transaction_journal import TransactionJournalStore
from prompt_action.domain.errors import ReleaseWorkflowError
from prompt_action.services.revision_allocator import allocate_revision
from prompt_action.services.snapshot_allocator import allocate_snapshot


@dataclass(frozen=True, slots=True)
class ReleaseChange:
    prompt_id: str
    role: str
    from_revision: str
    to_revision: str
    source_path: str
    target_relative: str
    source_sha256: str
    source_size: int
    summary: tuple[str, ...]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "role": self.role,
            "from_revision": self.from_revision,
            "to_revision": self.to_revision,
            "source_path": self.source_path,
            "target_relative": self.target_relative,
            "source_sha256": self.source_sha256,
            "source_size": self.source_size,
            "summary": list(self.summary),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class ReleasePlan:
    expected_app_data_revision: int
    expected_canonical_sha256: str
    app_version: str
    system: str
    parent_snapshot: str
    snapshot_id: str
    primary: ReleaseChange
    sync: tuple[ReleaseChange, ...]
    prompt_state: dict[str, str]
    warnings: tuple[str, ...]
    confirmation_token: str
    resulting_status: str = "BACKUP_REQUIRED"

    @property
    def changes(self) -> tuple[ReleaseChange, ...]:
        return (self.primary, *self.sync)

    def to_dict(self, *, include_confirmation_token: bool = True) -> dict[str, Any]:
        value: dict[str, Any] = {
            "expected_app_data_revision": self.expected_app_data_revision,
            "expected_canonical_sha256": self.expected_canonical_sha256,
            "app_version": self.app_version,
            "system": self.system,
            "parent_snapshot": self.parent_snapshot,
            "snapshot_id": self.snapshot_id,
            "primary": self.primary.to_dict(),
            "sync": [item.to_dict() for item in self.sync],
            "prompt_state": dict(self.prompt_state),
            "warnings": list(self.warnings),
            "resulting_status": self.resulting_status,
        }
        if include_confirmation_token:
            value["confirmation_token"] = self.confirmation_token
        return value


class ReleasePlanner:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.version_repository = VersionRepository(self.project_root)
        self.release_repository = ReleaseRepository(self.project_root)
        self.journals = TransactionJournalStore(self.project_root)

    @staticmethod
    def _canonical_token(payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _normalize_for_semantic_warning(text: str) -> str:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        return " ".join(normalized.split())

    def _verify_active_sources(self, document: dict[str, Any]) -> None:
        try:
            snapshot = next(item for item in document["snapshots"] if item["id"] == document["active_snapshot"])
            prompt_state = snapshot["prompt_state"]
        except (KeyError, StopIteration, TypeError) as exc:
            raise ReleaseWorkflowError("RECOVERY_REQUIRED", "Canonical active snapshot graph is not readable") from exc
        for prompt_id, revision_id in prompt_state.items():
            try:
                revision = document["prompts"][prompt_id]["revisions"][revision_id]
            except (KeyError, TypeError) as exc:
                raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Active revision graph is incomplete: {prompt_id}:{revision_id}") from exc
            relative = revision.get("file")
            expected = revision.get("sha256")
            if revision.get("file_available") is not True or not isinstance(relative, str) or not isinstance(expected, str):
                raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Active source is not materialized: {prompt_id}:{revision_id}")
            path = self.release_repository.safe_project_path(relative)
            if not path.is_file() or path.is_symlink():
                raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Active source file is missing/unsafe: {prompt_id}:{revision_id}")
            if sha256_path(path) != expected:
                raise ReleaseWorkflowError("HASH_MISMATCH", f"Active source hash mismatch: {prompt_id}:{revision_id}")

    @staticmethod
    def _normalize_sync(sync: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:
        if sync is None:
            return []
        result = list(sync)
        if any(not isinstance(item, dict) for item in result):
            raise ReleaseWorkflowError("INVALID_SYNC", "Every SYNC entry must be an object")
        return result

    def _candidate(self, value: str | Path, *, prompt_id: str) -> tuple[Path, bytes, str]:
        path = Path(value).expanduser().resolve()
        if not path.is_file() or path.is_symlink():
            raise ReleaseWorkflowError("PATH_POLICY_BLOCKED", f"Candidate must be a regular file: {prompt_id}")
        if path.suffix.lower() != ".txt":
            raise ReleaseWorkflowError("PATH_POLICY_BLOCKED", f"Candidate must be .txt: {prompt_id}")
        raw = path.read_bytes()
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ReleaseWorkflowError("PATH_POLICY_BLOCKED", f"Candidate must be UTF-8 text: {prompt_id}") from exc
        return path, raw, hashlib.sha256(raw).hexdigest()

    def plan_release(
        self,
        *,
        primary_prompt_id: str,
        primary_source: str | Path,
        sync: Iterable[dict[str, Any]] | None = None,
        reason: str,
        summary: Iterable[str] | None = None,
    ) -> ReleasePlan:
        if self.journals.inspect_pending() is not None:
            raise ReleaseWorkflowError("RECOVERY_REQUIRED", "An unresolved release transaction must be recovered first")
        state = self.version_repository.load()
        document = state.document
        try:
            active_snapshot = next(item for item in document["snapshots"] if item["id"] == document["active_snapshot"])
        except (KeyError, StopIteration, TypeError) as exc:
            raise ReleaseWorkflowError("RECOVERY_REQUIRED", "Canonical active snapshot cannot be resolved") from exc
        if active_snapshot.get("status") != "COMPLETE":
            raise ReleaseWorkflowError("PREVIOUS_BACKUP_INCOMPLETE", "Active snapshot must be COMPLETE before a new release")

        # Verify byte-level integrity before the broad canonical gate so an
        # active-file tamper is classified precisely as HASH_MISMATCH rather
        # than being flattened into RECOVERY_REQUIRED by the validator.
        self._verify_active_sources(document)
        report = self.version_repository.validate(state)
        if not report.is_valid:
            raise ReleaseWorkflowError("RECOVERY_REQUIRED", "Canonical state is invalid before release planning")

        if primary_prompt_id not in document["prompts"]:
            raise ReleaseWorkflowError("NO_OP_PRIMARY", f"Unknown PRIMARY prompt: {primary_prompt_id}")
        sync_items = self._normalize_sync(sync)
        sync_ids = [item.get("prompt_id") for item in sync_items]
        if any(not isinstance(pid, str) or pid not in document["prompts"] for pid in sync_ids):
            raise ReleaseWorkflowError("INVALID_SYNC", "SYNC contains an unknown prompt")
        if primary_prompt_id in sync_ids or len(set(sync_ids)) != len(sync_ids):
            raise ReleaseWorkflowError("INVALID_SYNC", "PRIMARY/SYNC prompt IDs must be unique")
        if not reason.strip():
            raise ReleaseWorkflowError("PATH_POLICY_BLOCKED", "Release reason is required")

        system = document["active_system"]
        snapshot_id = allocate_snapshot([item["id"] for item in document["snapshots"] if item.get("system") == system])
        if any(item.get("id") == snapshot_id for item in document["snapshots"]):
            raise ReleaseWorkflowError("SNAPSHOT_ID_CONFLICT", f"Snapshot already exists: {snapshot_id}")
        next_state = deepcopy(active_snapshot["prompt_state"])
        warnings: list[str] = []
        default_summary = tuple(str(item).strip() for item in (summary or ()) if str(item).strip())

        def build_change(prompt_id: str, role: str, source: str | Path, item_reason: str | None = None, item_summary: Iterable[str] | None = None) -> ReleaseChange:
            prompt = document["prompts"][prompt_id]
            from_revision = prompt["active_revision"]
            active = prompt["revisions"][from_revision]
            source_path, raw, digest = self._candidate(source, prompt_id=prompt_id)
            if digest == active.get("sha256"):
                code = "NO_OP_PRIMARY" if role == "PRIMARY" else "INVALID_SYNC"
                raise ReleaseWorkflowError(code, f"{prompt_id} bytes are unchanged from active {from_revision}")
            to_revision = allocate_revision(list(prompt["revisions"]))
            target_relative, target = self.release_repository.target_revision_path(
                system=system, display_name=prompt["display_name"], revision=to_revision
            )
            if target.exists():
                raise ReleaseWorkflowError("REVISION_TARGET_EXISTS", f"Revision target already exists: {target_relative}")
            historical = [rid for rid, rev in prompt["revisions"].items() if rid != from_revision and rev.get("sha256") == digest]
            if historical:
                warnings.append(f"{prompt_id}: candidate bytes match historical revision(s) {', '.join(sorted(historical))}.")
            active_path = self.release_repository.safe_project_path(active["file"])
            active_text = active_path.read_text(encoding="utf-8")
            candidate_text = raw.decode("utf-8")
            if self._normalize_for_semantic_warning(active_text) == self._normalize_for_semantic_warning(candidate_text):
                warnings.append(f"{prompt_id}: change appears limited to whitespace/line endings; explicit reason is required.")
            next_state[prompt_id] = to_revision
            chosen_summary = tuple(str(x).strip() for x in (item_summary or default_summary) if str(x).strip())
            if not chosen_summary:
                chosen_summary = (f"{role} revision released in {snapshot_id}.",)
            return ReleaseChange(
                prompt_id=prompt_id,
                role=role,
                from_revision=from_revision,
                to_revision=to_revision,
                source_path=str(source_path),
                target_relative=target_relative,
                source_sha256=digest,
                source_size=len(raw),
                summary=chosen_summary,
                reason=(item_reason or reason).strip(),
            )

        primary = build_change(primary_prompt_id, "PRIMARY", primary_source)
        sync_changes: list[ReleaseChange] = []
        for item in sync_items:
            source = item.get("source") or item.get("file")
            if not isinstance(source, (str, Path)):
                raise ReleaseWorkflowError("INVALID_SYNC", f"SYNC source missing for {item.get('prompt_id')}")
            sync_changes.append(
                build_change(
                    item["prompt_id"], "SYNC", source,
                    item_reason=item.get("reason") if isinstance(item.get("reason"), str) else None,
                    item_summary=item.get("summary") if isinstance(item.get("summary"), list) else None,
                )
            )

        facts = {
            "expected_app_data_revision": state.app_data_revision,
            "expected_canonical_sha256": self.release_repository.canonical_sha256(),
            "app_version": document["app_version"],
            "system": system,
            "parent_snapshot": document["active_snapshot"],
            "snapshot_id": snapshot_id,
            "primary": primary.to_dict(),
            "sync": [item.to_dict() for item in sync_changes],
            "prompt_state": next_state,
            "warnings": warnings,
            "resulting_status": "BACKUP_REQUIRED",
        }
        token = self._canonical_token(facts)
        return ReleasePlan(
            expected_app_data_revision=state.app_data_revision,
            expected_canonical_sha256=facts["expected_canonical_sha256"],
            app_version=document["app_version"],
            system=system,
            parent_snapshot=document["active_snapshot"],
            snapshot_id=snapshot_id,
            primary=primary,
            sync=tuple(sync_changes),
            prompt_state=next_state,
            warnings=tuple(warnings),
            confirmation_token=token,
        )
