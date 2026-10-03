from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from typing import Any


@dataclass(frozen=True, slots=True)
class SearchEntity:
    entity_type: str
    stable_id: str
    label: str
    context: str
    route: str
    route_entity_id: str
    route_sub_id: str = ""
    primary_text: str = ""
    secondary_text: str = ""
    source_state: str = "VALID"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "stable_id": self.stable_id,
            "label": self.label,
            "context": self.context,
            "route": self.route,
            "route_entity_id": self.route_entity_id,
            "route_sub_id": self.route_sub_id,
            "source_state": self.source_state,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class SearchResult:
    entity: SearchEntity
    score: int
    match_kind: str

    def to_dict(self) -> dict[str, Any]:
        data = self.entity.to_dict()
        data.update({"score": self.score, "match_kind": self.match_kind})
        return data


@dataclass(frozen=True, slots=True)
class SearchResultPage:
    state: str
    query: str
    results: tuple[SearchResult, ...] = ()
    message: str = ""
    generation: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "query": self.query,
            "results": [item.to_dict() for item in self.results],
            "message": self.message,
            "generation": self.generation,
        }


@dataclass(frozen=True, slots=True)
class NavigationTarget:
    route: str
    entity_id: str
    sub_id: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"route": self.route, "entity_id": self.entity_id, "sub_id": self.sub_id}


@dataclass(frozen=True, slots=True)
class RevisionCompareResult:
    status: str
    prompt_id: str
    left_revision: str
    right_revision: str
    left_sha256: str
    right_sha256: str
    unified_diff: str
    changed_lines: int
    whitespace_only: bool
    eol_only: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "prompt_id": self.prompt_id,
            "left_revision": self.left_revision,
            "right_revision": self.right_revision,
            "left_sha256": self.left_sha256,
            "right_sha256": self.right_sha256,
            "unified_diff": self.unified_diff,
            "changed_lines": self.changed_lines,
            "whitespace_only": self.whitespace_only,
            "eol_only": self.eol_only,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class SnapshotCompareResult:
    status: str
    left_snapshot: str
    right_snapshot: str
    left_system: str
    right_system: str
    cross_system_warning: bool
    changed: tuple[dict[str, Any], ...]
    unchanged_count: int
    primary_delta: dict[str, Any] | None
    sync_deltas: tuple[dict[str, Any], ...]
    backup_delta: dict[str, Any]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "left_snapshot": self.left_snapshot,
            "right_snapshot": self.right_snapshot,
            "left_system": self.left_system,
            "right_system": self.right_system,
            "cross_system_warning": self.cross_system_warning,
            "changed": [dict(x) for x in self.changed],
            "unchanged_count": self.unchanged_count,
            "primary_delta": dict(self.primary_delta) if self.primary_delta else None,
            "sync_deltas": [dict(x) for x in self.sync_deltas],
            "backup_delta": dict(self.backup_delta),
            "summary": self.summary,
        }


@dataclass(frozen=True, slots=True)
class DownloadPlan:
    entity_type: str
    stable_id: str
    source_path: Path
    filename: str
    sha256: str | None
    verify_destination: bool = True


@dataclass(frozen=True, slots=True)
class DownloadResult:
    status: str
    path: Path | None = None
    sha256: str | None = None
    bytes_copied: int = 0
    code: str = "OK"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "path": str(self.path) if self.path else None,
            "sha256": self.sha256,
            "bytes_copied": self.bytes_copied,
            "code": self.code,
        }


@dataclass(frozen=True, slots=True)
class Capability:
    enabled: bool
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"enabled": self.enabled, "reason": self.reason}


class CancelToken:
    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()
