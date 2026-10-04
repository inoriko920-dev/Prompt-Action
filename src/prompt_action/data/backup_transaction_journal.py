from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from prompt_action.data.atomic_writer import atomic_write_json
from prompt_action.domain.errors import BackupWorkflowError

TERMINAL_PHASES = {"COMPLETE", "FAILED", "CANCELLED"}
ALLOWED_PHASES = {
    "PLANNING",
    "WRITING_ZIP",
    "ZIP_WRITTEN",
    "WRITING_HASH",
    "VERIFYING_PRIMARY",
    "COPYING_SECONDARY",
    "VERIFYING_SECONDARY",
    "COMMITTING_METADATA",
    "COMPLETE",
    "FAILED",
    "CANCELLED",
    "RECOVERY_REQUIRED",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class BackupTransactionJournalStore:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.root = self.project_root / "backup_txn"

    @staticmethod
    def _validate_id(txn_id: str) -> None:
        if not txn_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in txn_id):
            raise BackupWorkflowError("PATH_POLICY_BLOCKED", "Unsafe backup transaction id")

    def txn_dir(self, txn_id: str) -> Path:
        self._validate_id(txn_id)
        return self.root / txn_id

    def journal_path(self, txn_id: str) -> Path:
        return self.txn_dir(txn_id) / "journal.json"

    def create(self, txn_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        path = self.journal_path(txn_id)
        if path.exists():
            raise BackupWorkflowError("BACKUP_BUSY", f"Backup transaction already exists: {txn_id}")
        doc = deepcopy(payload)
        now = _now()
        doc.update({"txn_id": txn_id, "phase": "PLANNING", "created_at": now, "updated_at": now})
        atomic_write_json(path, doc)
        return doc

    def load(self, txn_id: str) -> dict[str, Any]:
        path = self.journal_path(txn_id)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BackupWorkflowError("BACKUP_RECOVERY_REQUIRED", f"Cannot read backup transaction journal {txn_id}: {exc}") from exc
        if not isinstance(value, dict):
            raise BackupWorkflowError("BACKUP_RECOVERY_REQUIRED", f"Invalid backup journal root: {txn_id}")
        phase = value.get("phase")
        if phase not in ALLOWED_PHASES:
            raise BackupWorkflowError("BACKUP_RECOVERY_REQUIRED", f"Unknown backup journal phase: {phase!r}")
        return value

    def update(self, txn_id: str, phase: str, **fields: Any) -> dict[str, Any]:
        if phase not in ALLOWED_PHASES:
            raise BackupWorkflowError("BACKUP_RECOVERY_REQUIRED", f"Unknown backup transaction phase: {phase}")
        doc = self.load(txn_id)
        doc.update(fields)
        doc["phase"] = phase
        doc["updated_at"] = _now()
        atomic_write_json(self.journal_path(txn_id), doc)
        return doc

    def list_all(self) -> list[dict[str, Any]]:
        if not self.root.exists():
            return []
        result: list[dict[str, Any]] = []
        for child in sorted(self.root.iterdir()):
            if child.is_dir() and (child / "journal.json").is_file():
                result.append(self.load(child.name))
        return result

    def unresolved(self) -> list[dict[str, Any]]:
        return [item for item in self.list_all() if item.get("phase") not in TERMINAL_PHASES]

    def inspect_pending(self) -> dict[str, Any] | None:
        unresolved = self.unresolved()
        if not unresolved:
            return None
        if len(unresolved) > 1:
            raise BackupWorkflowError("BACKUP_RECOVERY_REQUIRED", "Multiple unresolved backup transactions exist")
        return unresolved[0]
