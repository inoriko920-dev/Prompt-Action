from __future__ import annotations

from copy import deepcopy
import hashlib
from typing import Any

FIXTURE_SCHEMA = "step02-corruption-v1"


def is_corruption_descriptor(value: Any) -> bool:
    return isinstance(value, dict) and value.get("fixture_schema") == FIXTURE_SCHEMA and isinstance(value.get("mutation"), str)


def build_corruption_fixture(descriptor: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    if not is_corruption_descriptor(descriptor):
        raise ValueError("Not a STEP 02 corruption fixture descriptor")
    mutation = descriptor["mutation"]
    doc = deepcopy(baseline)

    if mutation == "missing-parent-snapshot":
        child = _append_release(doc, primary="P3")
        child["parent_snapshot"] = "S999"
    elif mutation == "snapshot-cycle":
        child = _append_release(doc, primary="P3")
        doc["snapshots"][0]["parent_snapshot"] = child["id"]
    elif mutation == "revision-cycle":
        _append_release(doc, primary="P3")
        doc["prompts"]["P3"]["revisions"]["R1"]["parent"] = "R2"
    elif mutation == "undeclared-sync-change":
        child = _append_release(doc, primary="P3")
        child["primary_change"] = None
        child["sync_changes"] = []
    elif mutation == "missing-active-file":
        rev = doc["prompts"]["P3"]["revisions"]["R1"]
        rev["file"] = "prompts/V1/Prompt-3/DOES_NOT_EXIST.txt"
        rev["file_available"] = True
    elif mutation == "sha-mismatch":
        rev = doc["prompts"]["P3"]["revisions"]["R1"]
        rev["file"] = "data/fixtures/hash-target.txt"
        rev["sha256"] = "0" * 64
        rev["file_available"] = True
    elif mutation == "complete-without-backup":
        doc["snapshots"][0]["status"] = "COMPLETE"
        doc["snapshots"][0]["backup_id"] = None
    elif mutation == "absolute-path-leak":
        rev = doc["prompts"]["P3"]["revisions"]["R1"]
        rev["file"] = r"C:\Users\developer\Prompt-3.txt"
        rev["file_available"] = False
    elif mutation == "schema-version-unsupported":
        doc["schema_version"] = 99
    else:
        raise ValueError(f"Unknown corruption fixture mutation: {mutation}")
    return doc


def _append_release(document: dict[str, Any], *, primary: str) -> dict[str, Any]:
    parent = document["active_snapshot"]
    parent_snapshot = next(item for item in document["snapshots"] if item["id"] == parent)
    child_state = deepcopy(parent_snapshot["prompt_state"])
    prompt = document["prompts"][primary]
    from_revision = prompt["active_revision"]
    to_revision = f"R{max(int(value[1:]) for value in prompt['revisions']) + 1}"
    prompt["revisions"][from_revision]["status"] = "SUPERSEDED"
    prompt["revisions"][to_revision] = {
        "parent": from_revision,
        "snapshot": "S002",
        "status": "ACTIVE",
        "file": None,
        "sha256": hashlib.sha256(f"{primary}-S002".encode()).hexdigest(),
        "file_available": False,
        "change_role": "PRIMARY",
        "summary": ["corruption fixture"],
        "reason": "corruption fixture",
    }
    prompt["active_revision"] = to_revision
    child_state[primary] = to_revision
    child = {
        "id": "S002",
        "system": document["active_system"],
        "parent_snapshot": parent,
        "status": "BACKUP_REQUIRED",
        "primary_change": {"prompt_id": primary, "from": from_revision, "to": to_revision},
        "sync_changes": [],
        "prompt_state": child_state,
        "backup_id": None,
    }
    document["snapshots"].append(child)
    document["active_snapshot"] = "S002"
    document["systems"][0]["latest_snapshot"] = "S002"
    return child
