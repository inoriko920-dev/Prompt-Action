from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Callable

from prompt_action.domain.errors import CanonicalDataError, RevisionConflictError, ValidationBlockedError
from prompt_action.domain.models import ValidationReport, VersionState
from prompt_action.domain.validation import VersionValidator


@dataclass(frozen=True, slots=True)
class SaveResult:
    path: Path
    app_data_revision: int
    sha256: str


class VersionRepository:
    def __init__(self, project_root: Path, *, relative_path: str = "data/version_history.json", replace_func: Callable[[str | os.PathLike[str], str | os.PathLike[str]], None] = os.replace) -> None:
        self.project_root = project_root.resolve()
        self.path = (self.project_root / relative_path).resolve()
        try:
            self.path.relative_to(self.project_root)
        except ValueError as exc:
            raise CanonicalDataError("Canonical path must remain inside project root") from exc
        self.validator = VersionValidator(self.project_root)
        self.replace_func = replace_func

    @staticmethod
    def _validate_state_transitions(current: dict, proposed: dict) -> None:
        old = {item.get("id"): item for item in current.get("snapshots", []) if isinstance(item, dict)}
        new = {item.get("id"): item for item in proposed.get("snapshots", []) if isinstance(item, dict)}
        allowed = {
            "DRAFT": {"DRAFT", "BACKUP_REQUIRED"},
            "BACKUP_REQUIRED": {"BACKUP_REQUIRED", "BACKUP_FAILED", "COMPLETE"},
            "BACKUP_FAILED": {"BACKUP_FAILED", "COMPLETE"},
            "COMPLETE": {"COMPLETE"},
        }
        for snapshot_id, new_item in new.items():
            new_status = new_item.get("status")
            if snapshot_id not in old:
                if new_status not in {"DRAFT", "BACKUP_REQUIRED"}:
                    raise ValidationBlockedError(
                        f"New snapshot {snapshot_id} cannot start in status {new_status!r}; it must start as DRAFT or BACKUP_REQUIRED."
                    )
                continue
            old_status = old[snapshot_id].get("status")
            if old_status != new_status and new_status not in allowed.get(str(old_status), set()):
                raise ValidationBlockedError(f"Illegal snapshot state transition {snapshot_id}: {old_status} -> {new_status}")

    def load(self) -> VersionState:
        try:
            text = self.path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CanonicalDataError(f"Cannot read canonical history: {self.path}: {exc}") from exc
        try:
            document = json.loads(text)
        except json.JSONDecodeError as exc:
            raise CanonicalDataError(f"Malformed canonical JSON: {exc}") from exc
        if not isinstance(document, dict):
            raise CanonicalDataError("Canonical JSON root must be an object")
        return VersionState(document=document)

    def reload(self) -> VersionState:
        return self.load()

    def validate(self, state: VersionState | dict) -> ValidationReport:
        document = state.document if isinstance(state, VersionState) else state
        return self.validator.validate(document)

    def save(self, state: VersionState | dict, expected_revision: int) -> SaveResult:
        document = deepcopy(state.document if isinstance(state, VersionState) else state)
        current = self.load()
        if current.app_data_revision != expected_revision:
            raise RevisionConflictError(f"Expected app_data_revision={expected_revision}, current={current.app_data_revision}")
        target_revision = document.get("app_data_revision")
        if target_revision != expected_revision + 1:
            raise RevisionConflictError(
                "New state must increment app_data_revision exactly once: "
                f"expected {expected_revision + 1}, got {target_revision!r}"
            )
        self._validate_state_transitions(current.document, document)
        report = self.validator.validate(document)
        if not report.is_valid:
            raise ValidationBlockedError(
                "Canonical save blocked by validation issues: "
                + ", ".join(issue.code for issue in report.blocking_issues + report.errors)
            )

        self.path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n", prefix=f".{self.path.name}.", suffix=".tmp",
                dir=self.path.parent, delete=False,
            ) as handle:
                temp_path = Path(handle.name)
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())

            temp_document = json.loads(temp_path.read_text(encoding="utf-8"))
            temp_report = self.validator.validate(temp_document)
            if not temp_report.is_valid:
                raise ValidationBlockedError("Temporary canonical payload failed validation before atomic replace")

            self.replace_func(temp_path, self.path)
            temp_path = None
            if hasattr(os, "O_DIRECTORY"):
                try:
                    fd = os.open(self.path.parent, os.O_DIRECTORY)
                    try:
                        os.fsync(fd)
                    finally:
                        os.close(fd)
                except OSError:
                    pass
            digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
            return SaveResult(path=self.path, app_data_revision=int(document["app_data_revision"]), sha256=digest)
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
