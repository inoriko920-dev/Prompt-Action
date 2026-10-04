from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from prompt_action.data.atomic_writer import atomic_write_json
from prompt_action.domain.errors import ReleaseWorkflowError

TERMINAL_PHASES = {"COMMITTED", "ABORTED"}
ALLOWED_PHASES = {
    "PREPARING", "STAGED", "PLACING_FILES", "FILES_PLACED",
    "COMMITTING_METADATA", "COMMITTED", "ABORTED", "RECOVERY_REQUIRED",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class TransactionJournalStore:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.root = self.project_root / "release_txn"

    def txn_dir(self, txn_id: str) -> Path:
        if not txn_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in txn_id):
            raise ReleaseWorkflowError("PATH_POLICY_BLOCKED", "Unsafe transaction id")
        return self.root / txn_id

    def journal_path(self, txn_id: str) -> Path:
        return self.txn_dir(txn_id) / "journal.json"

    def create(self, txn_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        path = self.journal_path(txn_id)
        if path.exists():
            raise ReleaseWorkflowError("RELEASE_BUSY", f"Transaction already exists: {txn_id}")
        doc = deepcopy(payload)
        doc.update({"txn_id": txn_id, "phase": "PREPARING", "created_at": _now(), "updated_at": _now()})
        atomic_write_json(path, doc)
        return doc

    def load(self, txn_id: str) -> dict[str, Any]:
        path = self.journal_path(txn_id)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Cannot read transaction journal {txn_id}: {exc}") from exc
        if not isinstance(value, dict):
            raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Invalid transaction journal root: {txn_id}")
        return value

    def update(self, txn_id: str, phase: str, **fields: Any) -> dict[str, Any]:
        if phase not in ALLOWED_PHASES:
            raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Unknown transaction phase: {phase}")
        doc = self.load(txn_id)
        doc.update(fields)
        doc["phase"] = phase
        doc["updated_at"] = _now()
        atomic_write_json(self.journal_path(txn_id), doc)
        return doc

    def list_all(self) -> list[dict[str, Any]]:
        if not self.root.exists():
            return []
        items: list[dict[str, Any]] = []
        for child in sorted(self.root.iterdir()):
            if not child.is_dir() or not (child / "journal.json").is_file():
                continue
            items.append(self.load(child.name))
        return items

    def unresolved(self) -> list[dict[str, Any]]:
        return [item for item in self.list_all() if item.get("phase") not in TERMINAL_PHASES]

    def inspect_pending(self) -> dict[str, Any] | None:
        unresolved = self.unresolved()
        if not unresolved:
            return None
        if len(unresolved) > 1:
            raise ReleaseWorkflowError("RECOVERY_REQUIRED", "Multiple unresolved release transactions exist")
        return unresolved[0]
