from __future__ import annotations

from prompt_action.domain.ids import parse_revision_id
from prompt_action.domain.errors import ReleaseWorkflowError


def allocate_revision(existing: list[str] | tuple[str, ...] | set[str]) -> str:
    """Allocate max official R + 1; never reuse gaps."""
    try:
        number = max((parse_revision_id(value) for value in existing), default=0) + 1
    except ValueError as exc:
        raise ReleaseWorkflowError("REVISION_ID_INVALID", str(exc)) from exc
    return f"R{number}"
