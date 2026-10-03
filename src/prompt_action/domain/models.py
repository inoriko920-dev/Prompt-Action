from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    BLOCKING = "BLOCKING"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    severity: Severity
    entity: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "entity": self.entity,
            "path": self.path,
            "message": self.message,
        }


@dataclass(slots=True)
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    def add(self, code: str, severity: Severity, entity: str, path: str, message: str) -> None:
        self.issues.append(ValidationIssue(code, severity, entity, path, message))

    @property
    def blocking_issues(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity is Severity.BLOCKING]

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity is Severity.WARNING]

    @property
    def is_valid(self) -> bool:
        return not self.blocking_issues and not self.errors

    def to_dict(self) -> dict[str, Any]:
        counts = {severity.value: 0 for severity in Severity}
        for issue in self.issues:
            counts[issue.severity.value] += 1
        return {
            "valid": self.is_valid,
            "counts": counts,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True, slots=True)
class VersionState:
    document: dict[str, Any]

    @property
    def schema_version(self) -> int:
        return int(self.document["schema_version"])

    @property
    def app_data_revision(self) -> int:
        return int(self.document["app_data_revision"])

    @property
    def app_version(self) -> str:
        return str(self.document["app_version"])

    @property
    def active_system(self) -> str:
        return str(self.document["active_system"])

    @property
    def active_snapshot(self) -> str:
        return str(self.document["active_snapshot"])
