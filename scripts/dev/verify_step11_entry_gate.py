from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any

from prompt_action.data.release_repository import ReleaseRepository, sha256_path
from prompt_action.data.repository import VersionRepository
from prompt_action.data.transaction_journal import TransactionJournalStore
from prompt_action.settings.repository import SettingsRepository

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
BACKUP_TERMINAL_PHASES = {"COMPLETE", "FAILED", "CANCELLED"}
MIN_FREE_BYTES = 64 * 1024 * 1024


def _pass_report(path: Path) -> bool:
    try:
        return "Status: **PASS**" in path.read_text(encoding="utf-8")
    except OSError:
        return False


def _nearest_existing(path: Path) -> Path | None:
    current = path
    while True:
        if current.exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _is_nested(a: Path, b: Path) -> bool:
    return a == b or a in b.parents or b in a.parents


def _destination_probe(root: Path, value: str) -> dict[str, Any]:
    configured = Path(value)
    path = (configured if configured.is_absolute() else root / configured).resolve(strict=False)
    existing = _nearest_existing(path)
    writable = bool(existing and existing.is_dir() and os.access(existing, os.W_OK))
    free_bytes = None
    if existing is not None:
        try:
            free_bytes = shutil.disk_usage(existing).free
        except OSError:
            free_bytes = None
    return {
        "configured": value,
        "resolved": str(path),
        "existing_probe_root": str(existing) if existing else None,
        "writable": writable,
        "free_bytes": free_bytes,
    }


def _backup_journal_unresolved(root: Path) -> list[dict[str, Any]]:
    journal_root = root / "backup_txn"
    if not journal_root.exists():
        return []
    unresolved: list[dict[str, Any]] = []
    for child in sorted(journal_root.iterdir()):
        if not child.is_dir():
            continue
        journal = child / "journal.json"
        if not journal.is_file():
            continue
        try:
            value = json.loads(journal.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            unresolved.append({"txn_id": child.name, "phase": "INVALID", "error": type(exc).__name__})
            continue
        phase = value.get("phase") if isinstance(value, dict) else None
        if phase not in BACKUP_TERMINAL_PHASES:
            unresolved.append({"txn_id": child.name, "phase": phase or "UNKNOWN"})
    return unresolved


def evaluate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    reasons: list[str] = []

    evidence = {
        "step09_5_pass": _pass_report(root / "docs/implementation/STEP_09_5_SOL_EXECUTION_REPORT.md"),
        "step10_pass": _pass_report(root / "docs/implementation/STEP_10_SOL_EXECUTION_REPORT.md"),
    }
    if not evidence["step09_5_pass"] or not evidence["step10_pass"]:
        reasons.append("PREREQUISITE_EVIDENCE_MISSING")

    repository = VersionRepository(root)
    try:
        state = repository.load()
        validation = repository.validate(state)
    except Exception as exc:
        return {
            "status": "BLOCKED",
            "reasons": ["CANONICAL_LOAD_FAILED"],
            "error": f"{type(exc).__name__}: {exc}",
            "evidence": evidence,
        }

    canonical_valid = validation.is_valid
    if not canonical_valid:
        reasons.append("CANONICAL_INVALID")

    document = state.document
    active_snapshot_id = document.get("active_snapshot")
    snapshots = {item.get("id"): item for item in document.get("snapshots", []) if isinstance(item, dict)}
    snapshot = snapshots.get(active_snapshot_id)
    snapshot_status = snapshot.get("status") if isinstance(snapshot, dict) else None
    if snapshot is None:
        reasons.append("ACTIVE_SNAPSHOT_MISSING")
    elif snapshot_status != "BACKUP_REQUIRED":
        reasons.append("SNAPSHOT_NOT_BACKUP_REQUIRED")

    release_pending: dict[str, Any] | None = None
    release_error: str | None = None
    try:
        release_pending = TransactionJournalStore(root).inspect_pending()
    except Exception as exc:
        release_error = f"{type(exc).__name__}: {exc}"
    release_clear = release_pending is None and release_error is None
    if not release_clear:
        reasons.append("RELEASE_TRANSACTION_UNRESOLVED")

    backup_pending = _backup_journal_unresolved(root)
    backup_clear = not backup_pending
    if not backup_clear:
        reasons.append("BACKUP_TRANSACTION_UNRESOLVED")

    prompt_results: dict[str, Any] = {}
    prompt_hashes_match = True
    if isinstance(snapshot, dict):
        release_repo = ReleaseRepository(root)
        for prompt_id, revision_id in snapshot.get("prompt_state", {}).items():
            revision = document.get("prompts", {}).get(prompt_id, {}).get("revisions", {}).get(revision_id)
            if not isinstance(revision, dict):
                prompt_results[prompt_id] = {"revision": revision_id, "status": "MISSING_REVISION"}
                prompt_hashes_match = False
                continue
            rel = revision.get("file")
            expected = revision.get("sha256")
            if not isinstance(rel, str) or not isinstance(expected, str):
                prompt_results[prompt_id] = {"revision": revision_id, "status": "INVALID_METADATA"}
                prompt_hashes_match = False
                continue
            try:
                path = release_repo.safe_project_path(rel)
                actual = sha256_path(path) if path.is_file() else None
            except Exception as exc:
                prompt_results[prompt_id] = {
                    "revision": revision_id,
                    "status": "PATH_ERROR",
                    "error": f"{type(exc).__name__}: {exc}",
                }
                prompt_hashes_match = False
                continue
            ok = actual == expected
            prompt_results[prompt_id] = {
                "revision": revision_id,
                "file": rel,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "status": "PASS" if ok else "HASH_MISMATCH_OR_MISSING",
            }
            prompt_hashes_match = prompt_hashes_match and ok
    else:
        prompt_hashes_match = False
    if not prompt_hashes_match:
        reasons.append("ACTIVE_PROMPT_HASH_MISMATCH")

    settings_load = SettingsRepository(root).load()
    settings = settings_load.settings
    primary = _destination_probe(root, settings.general.backup_dir)
    secondary_value = settings.backup.second_copy_dir or ""
    secondary = _destination_probe(root, secondary_value) if secondary_value else {
        "configured": None,
        "resolved": None,
        "existing_probe_root": None,
        "writable": False,
        "free_bytes": None,
    }
    destination_distinct = False
    if primary.get("resolved") and secondary.get("resolved"):
        destination_distinct = not _is_nested(Path(primary["resolved"]), Path(secondary["resolved"]))
    destination_writable = bool(primary.get("writable") and secondary.get("writable"))

    payload_bytes = sum(p.stat().st_size for p in (root / "prompts").rglob("*") if p.is_file())
    canonical_path = root / "data/version_history.json"
    if canonical_path.is_file():
        payload_bytes += canonical_path.stat().st_size
    conservative_required = max(MIN_FREE_BYTES, payload_bytes * 4)
    free_values = [value for value in (primary.get("free_bytes"), secondary.get("free_bytes")) if isinstance(value, int)]
    destination_space_ok = len(free_values) == 2 and all(value >= conservative_required for value in free_values)

    if not destination_distinct:
        reasons.append("BACKUP_DESTINATIONS_NOT_DISTINCT")
    if not destination_writable:
        reasons.append("BACKUP_DESTINATION_NOT_WRITABLE")
    if not destination_space_ok:
        reasons.append("BACKUP_SPACE_INSUFFICIENT_OR_UNKNOWN")

    status = "READY" if not reasons else "BLOCKED"
    return {
        "status": status,
        "reasons": reasons,
        "active_system": document.get("active_system"),
        "active_snapshot": active_snapshot_id,
        "snapshot_status": snapshot_status,
        "app_data_revision": document.get("app_data_revision"),
        "canonical_valid": canonical_valid,
        "validation_issue_count": len(validation.issues),
        "evidence": evidence,
        "active_prompt_hashes_match": prompt_hashes_match,
        "active_prompts": prompt_results,
        "release_transaction_clear": release_clear,
        "release_transaction": release_pending,
        "release_transaction_error": release_error,
        "backup_transaction_clear": backup_clear,
        "backup_transactions": backup_pending,
        "settings_source": settings_load.source,
        "settings_degraded": settings_load.degraded,
        "primary_destination": primary,
        "secondary_destination": secondary,
        "destinations_distinct": destination_distinct,
        "destinations_writable": destination_writable,
        "estimated_payload_bytes": payload_bytes,
        "conservative_required_free_bytes": conservative_required,
        "destination_space_ok": destination_space_ok,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only STEP 11 entry-gate verifier")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="return exit code 2 when the gate is BLOCKED; default mode reports BLOCKED as a valid observed state",
    )
    args = parser.parse_args(argv)
    payload = evaluate(args.root)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    if args.require_ready and payload.get("status") != "READY":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
