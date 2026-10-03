from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ._graph_validation import validate_references_graph_domain
from ._integrity_validation import validate_file_integrity, validate_policy
from ._schema_validation import validate_schema
from .models import Severity, ValidationReport


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_json_text(text: str) -> tuple[dict[str, Any] | None, ValidationReport]:
    report = ValidationReport()
    try:
        value = json.loads(text)
    except (UnicodeError, json.JSONDecodeError) as exc:
        report.add("SYNTAX-JSON", Severity.BLOCKING, "root", "$", f"Canonical JSON cannot be parsed: {exc}")
        return None, report
    if not isinstance(value, dict):
        report.add("SCHEMA-ROOT-TYPE", Severity.BLOCKING, "root", "$", "Canonical JSON root must be an object.")
        return None, report
    return value, report


class VersionValidator:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()

    def validate_json_text(self, text: str) -> ValidationReport:
        document, report = parse_json_text(text)
        if document is None:
            return report
        report.issues.extend(self.validate(document).issues)
        return report

    def validate(self, document: dict[str, Any]) -> ValidationReport:
        report = ValidationReport()
        validate_schema(document, report)
        if report.blocking_issues:
            containers_ok = all(
                isinstance(document.get(key), expected)
                for key, expected in {
                    "systems": list, "snapshots": list, "prompts": dict, "backups": list,
                    "legacy_sources": list, "release_policy": dict, "integrity": dict,
                }.items()
            )
            if not containers_ok:
                return report
        validate_references_graph_domain(document, report)
        validate_file_integrity(self.project_root, document, report)
        validate_policy(document, report)
        return report
