from __future__ import annotations

from typing import Any

from .ids import parse_snapshot_id, parse_system_id
from .models import Severity, ValidationReport

ROOT_REQUIRED = {
    "schema_version", "app_data_revision", "app_version", "active_system", "active_snapshot",
    "legacy_sources", "systems", "snapshots", "prompts", "backups", "release_policy", "integrity",
}
PROMPT_IDS = {"P1A", "P1B", "P1B1", "P1B2", "P2", "P3", "P4", "P5"}


def validate_schema(document: dict[str, Any], report: ValidationReport) -> None:
    for key in sorted(ROOT_REQUIRED - set(document)):
        report.add("SCHEMA-MISSING-FIELD", Severity.BLOCKING, "root", key, f"Required canonical field is missing: {key}")

    expected_types: dict[str, type | tuple[type, ...]] = {
        "schema_version": int,
        "app_data_revision": int,
        "app_version": str,
        "active_system": str,
        "active_snapshot": str,
        "legacy_sources": list,
        "systems": list,
        "snapshots": list,
        "prompts": dict,
        "backups": list,
        "release_policy": dict,
        "integrity": dict,
    }
    for key, expected in expected_types.items():
        if key in document and not isinstance(document[key], expected):
            report.add("SCHEMA-TYPE", Severity.BLOCKING, "root", key, f"Field {key} has invalid type {type(document[key]).__name__}; expected {expected}.")

    if isinstance(document.get("schema_version"), int) and document["schema_version"] != 1:
        report.add("SCHEMA-UNSUPPORTED", Severity.BLOCKING, "root", "schema_version", f"Unsupported schema_version={document['schema_version']}; supported=1.")
    if isinstance(document.get("app_data_revision"), int) and document["app_data_revision"] < 1:
        report.add("SCHEMA-REVISION", Severity.BLOCKING, "root", "app_data_revision", "app_data_revision must be >= 1.")

    active_system = document.get("active_system")
    if isinstance(active_system, str):
        try:
            parse_system_id(active_system)
        except ValueError as exc:
            report.add("SCHEMA-SYSTEM-ID", Severity.BLOCKING, active_system, "active_system", str(exc))
    active_snapshot = document.get("active_snapshot")
    if isinstance(active_snapshot, str):
        try:
            parse_snapshot_id(active_snapshot)
        except ValueError as exc:
            report.add("SCHEMA-SNAPSHOT-ID", Severity.BLOCKING, active_snapshot, "active_snapshot", str(exc))

    prompts = document.get("prompts")
    if isinstance(prompts, dict):
        for prompt_id in sorted(set(prompts) - PROMPT_IDS):
            report.add("SCHEMA-PROMPT-ID", Severity.BLOCKING, prompt_id, f"prompts.{prompt_id}", "Unknown prompt stable ID.")
