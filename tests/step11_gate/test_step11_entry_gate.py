from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/dev/verify_step11_entry_gate.py"


def _run(root: Path, *extra: str) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *extra],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.stdout.strip(), result.stderr
    return result.returncode, json.loads(result.stdout)


def _fixture(tmp_path: Path, *, backup_required: bool) -> Path:
    root = tmp_path / "project"
    (root / "data").mkdir(parents=True)
    shutil.copy2(ROOT / "data/version_history.json", root / "data/version_history.json")
    shutil.copytree(ROOT / "prompts", root / "prompts")
    (root / "docs/implementation").mkdir(parents=True)
    for name in ("STEP_09_5_SOL_EXECUTION_REPORT.md", "STEP_10_SOL_EXECUTION_REPORT.md"):
        shutil.copy2(ROOT / "docs/implementation" / name, root / "docs/implementation" / name)

    if backup_required:
        path = root / "data/version_history.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        active = doc["active_snapshot"]
        snapshot = next(item for item in doc["snapshots"] if item["id"] == active)
        snapshot["status"] = "BACKUP_REQUIRED"
        snapshot["backup_id"] = None
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return root


def test_live_repository_is_truthfully_blocked_before_real_release() -> None:
    code, payload = _run(ROOT)
    assert code == 0
    assert payload["status"] == "BLOCKED"
    assert payload["active_snapshot"] == "S001"
    assert payload["snapshot_status"] == "COMPLETE"
    assert "SNAPSHOT_NOT_BACKUP_REQUIRED" in payload["reasons"]
    assert payload["canonical_valid"] is True
    assert payload["active_prompt_hashes_match"] is True
    assert payload["release_transaction_clear"] is True
    assert payload["backup_transaction_clear"] is True


def test_require_ready_fails_closed_on_live_blocked_state() -> None:
    code, payload = _run(ROOT, "--require-ready")
    assert code == 2
    assert payload["status"] == "BLOCKED"


def test_synthetic_valid_backup_required_fixture_becomes_ready(tmp_path: Path) -> None:
    root = _fixture(tmp_path, backup_required=True)
    code, payload = _run(root, "--require-ready")
    assert code == 0
    assert payload["status"] == "READY"
    assert payload["snapshot_status"] == "BACKUP_REQUIRED"
    assert payload["canonical_valid"] is True
    assert payload["active_prompt_hashes_match"] is True
    assert payload["destinations_distinct"] is True
    assert payload["destinations_writable"] is True
    assert payload["destination_space_ok"] is True


def test_unresolved_release_transaction_blocks_ready_fixture(tmp_path: Path) -> None:
    root = _fixture(tmp_path, backup_required=True)
    journal = root / "release_txn/txn-test/journal.json"
    journal.parent.mkdir(parents=True)
    journal.write_text(json.dumps({"txn_id": "txn-test", "phase": "PREPARING"}) + "\n", encoding="utf-8")

    code, payload = _run(root, "--require-ready")
    assert code == 2
    assert payload["status"] == "BLOCKED"
    assert "RELEASE_TRANSACTION_UNRESOLVED" in payload["reasons"]
