from __future__ import annotations

import re

_SYSTEM_RE = re.compile(r"^V([1-9][0-9]*)$")
_SNAPSHOT_RE = re.compile(r"^S([0-9]{3})$")
_REVISION_RE = re.compile(r"^R([1-9][0-9]*)$")


def _parse(pattern: re.Pattern[str], value: str, label: str) -> int:
    match = pattern.fullmatch(value)
    if not match:
        raise ValueError(f"Invalid {label} id: {value!r}")
    return int(match.group(1))


def parse_system_id(value: str) -> int:
    return _parse(_SYSTEM_RE, value, "System")


def parse_snapshot_id(value: str) -> int:
    return _parse(_SNAPSHOT_RE, value, "Snapshot")


def parse_revision_id(value: str) -> int:
    return _parse(_REVISION_RE, value, "Revision")


def next_snapshot_id(existing: list[str]) -> str:
    number = max((parse_snapshot_id(value) for value in existing), default=0) + 1
    if number > 999:
        raise ValueError("Snapshot ID space exhausted for 3-digit policy")
    return f"S{number:03d}"


def next_revision_id(existing: list[str]) -> str:
    number = max((parse_revision_id(value) for value in existing), default=0) + 1
    return f"R{number}"
