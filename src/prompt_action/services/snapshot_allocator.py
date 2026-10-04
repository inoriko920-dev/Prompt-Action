from __future__ import annotations

from prompt_action.domain.ids import parse_snapshot_id
from prompt_action.domain.errors import ReleaseWorkflowError


def allocate_snapshot(existing: list[str] | tuple[str, ...] | set[str]) -> str:
    """Allocate max official S + 1 using the locked 3-digit policy."""
    try:
        number = max((parse_snapshot_id(value) for value in existing), default=0) + 1
    except ValueError as exc:
        raise ReleaseWorkflowError("SNAPSHOT_ID_INVALID", str(exc)) from exc
    if number > 999:
        raise ReleaseWorkflowError("SNAPSHOT_ID_EXHAUSTED", "Snapshot ID space exhausted for S001-S999 policy")
    return f"S{number:03d}"
