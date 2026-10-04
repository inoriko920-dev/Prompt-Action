from __future__ import annotations

import hashlib
import json
from pathlib import Path

from prompt_action.data.release_repository import ReleaseRepository, sha256_path
from prompt_action.data.repository import VersionRepository
from prompt_action.data.transaction_journal import TransactionJournalStore

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    report_path = ROOT / "docs/implementation/STEP_09_5_SOL_EXECUTION_REPORT.md"
    if not report_path.is_file() or "Status: **PASS**" not in report_path.read_text(encoding="utf-8"):
        raise SystemExit("STEP 09.5 PASS report is required")
    repo = VersionRepository(ROOT)
    state = repo.load()
    validation = repo.validate(state)
    if not validation.is_valid:
        raise SystemExit(json.dumps(validation.to_dict(), indent=2))
    doc = state.document
    if doc.get("app_data_revision") != 2 or doc.get("active_system") != "V1" or doc.get("active_snapshot") != "S001":
        raise SystemExit("STEP 10 must start from the validated V1/S001 app_data_revision=2 baseline")
    snapshot = next(item for item in doc["snapshots"] if item["id"] == "S001")
    if snapshot.get("status") != "COMPLETE" or snapshot.get("backup_id") != "B001":
        raise SystemExit("S001 must be COMPLETE with B001 before STEP 10")
    pending = TransactionJournalStore(ROOT).inspect_pending()
    if pending is not None:
        raise SystemExit(f"unresolved release transaction exists: {pending.get('txn_id')}")
    release_repo = ReleaseRepository(ROOT)
    active_hashes = {}
    for prompt_id, revision_id in snapshot["prompt_state"].items():
        revision = doc["prompts"][prompt_id]["revisions"][revision_id]
        path = release_repo.safe_project_path(revision["file"])
        actual = sha256_path(path)
        if actual != revision["sha256"]:
            raise SystemExit(f"active hash mismatch: {prompt_id}:{revision_id}")
        active_hashes[prompt_id] = actual
    payload = {
        "status": "PASS",
        "app_data_revision": state.app_data_revision,
        "active_system": state.active_system,
        "active_snapshot": state.active_snapshot,
        "canonical_sha256": hashlib.sha256((ROOT / "data/version_history.json").read_bytes()).hexdigest(),
        "active_prompt_hashes": active_hashes,
        "pending_transaction": None,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
