from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata
from typing import Any, Iterable

from prompt_action.data.repository import VersionRepository

from .errors import SearchError
from .models import CancelToken, NavigationTarget, SearchEntity, SearchResult, SearchResultPage

_ENTITY_ORDER = {"PROMPT": 0, "REVISION": 1, "SNAPSHOT": 2, "SYSTEM": 3, "BACKUP": 4, "CHANGELOG": 5}


def _norm(value: object) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value)).casefold().split())


def _flatten(values: Iterable[object]) -> str:
    return " ".join(_norm(value) for value in values if value is not None)


@dataclass(frozen=True, slots=True)
class ParsedQuery:
    normalized: str
    tokens: tuple[str, ...]
    quoted: tuple[str, ...]


class SearchQueryParser:
    _quoted = re.compile(r'"([^"]+)"')

    def parse(self, query: str) -> ParsedQuery:
        normalized = _norm(query)
        quoted = tuple(_norm(x) for x in self._quoted.findall(query) if _norm(x))
        remainder = self._quoted.sub(" ", query)
        tokens = tuple(x for x in _norm(remainder).split() if x)
        return ParsedQuery(normalized=normalized, tokens=tokens, quoted=quoted)


class SearchIndexer:
    def build(self, document: dict[str, Any]) -> tuple[SearchEntity, ...]:
        if not isinstance(document, dict) or not isinstance(document.get("prompts"), dict):
            raise SearchError("SEARCH_INDEX_INVALID", "Index search tidak dapat dibangun dari canonical data.")
        entities: list[SearchEntity] = []
        prompts = document["prompts"]
        for prompt_id in sorted(prompts):
            prompt = prompts[prompt_id]
            if not isinstance(prompt, dict):
                continue
            name = str(prompt.get("display_name") or prompt_id)
            revision_records = prompt.get("revisions", {}) if isinstance(prompt.get("revisions"), dict) else {}
            active = str(prompt.get("active_revision") or "")
            prompt_context = f"Revision aktif {active}" if active else "Prompt"
            entities.append(SearchEntity(
                "PROMPT", prompt_id, name, prompt_context, "prompt", prompt_id,
                primary_text=_flatten((prompt_id, name)),
                secondary_text=_flatten((prompt_context,)),
                source_state="VALID" if active else "UNKNOWN",
            ))
            for revision_id in sorted(revision_records, key=lambda value: int(str(value)[1:]) if str(value).startswith("R") and str(value)[1:].isdigit() else 999999):
                record = revision_records[revision_id]
                if not isinstance(record, dict):
                    continue
                summary = " ".join(str(x) for x in record.get("summary", []) if x is not None) if isinstance(record.get("summary"), list) else str(record.get("summary") or "")
                reason = str(record.get("reason") or "")
                filename = str(record.get("file") or "")
                state = "VALID" if record.get("file_available") is True and filename else "HISTORY_ONLY"
                stable = f"{prompt_id}:{revision_id}"
                entities.append(SearchEntity(
                    "REVISION", stable, f"{name} • {revision_id}", summary or reason or "Revision",
                    "prompt", prompt_id, str(revision_id),
                    primary_text=_flatten((stable, revision_id, name, prompt_id)),
                    secondary_text=_flatten((summary, reason, filename, record.get("snapshot"))),
                    source_state=state,
                    metadata={"prompt_id": prompt_id, "revision_id": revision_id, "snapshot": record.get("snapshot"), "file_available": bool(record.get("file_available"))},
                ))
        for system in document.get("systems", []):
            if not isinstance(system, dict) or not system.get("id"):
                continue
            sid = str(system["id"])
            label = f"System {sid}"
            context = str(system.get("status") or "")
            entities.append(SearchEntity("SYSTEM", sid, label, context, "system_history", sid, primary_text=_flatten((sid, label)), secondary_text=_flatten((context, system.get("generation_reason")))))
        for snapshot in document.get("snapshots", []):
            if not isinstance(snapshot, dict) or not snapshot.get("id"):
                continue
            sid = str(snapshot["id"])
            system = str(snapshot.get("system") or "")
            primary = snapshot.get("primary_change")
            sync = snapshot.get("sync_changes", [])
            primary_text = _flatten((sid, f"Snapshot {sid}", system))
            secondary = _flatten((snapshot.get("status"), primary, sync, snapshot.get("parent_snapshot")))
            entities.append(SearchEntity(
                "SNAPSHOT", sid, f"Snapshot {sid}", f"System {system} • {snapshot.get('status', '')}",
                "system_history", sid, primary_text=primary_text, secondary_text=secondary,
                metadata={"system": system, "status": snapshot.get("status")},
            ))
        for backup in document.get("backups", []):
            if not isinstance(backup, dict):
                continue
            bid = str(backup.get("id") or backup.get("backup_id") or backup.get("snapshot") or "")
            if not bid:
                continue
            snapshot_id = str(backup.get("snapshot") or backup.get("snapshot_id") or "")
            filename = str(backup.get("filename") or backup.get("file") or "")
            state = "VALID" if backup.get("verified") is True and filename else "MISSING"
            entities.append(SearchEntity(
                "BACKUP", bid, filename or f"Backup {bid}", f"Snapshot {snapshot_id} • {backup.get('status', '')}",
                "backup", snapshot_id, primary_text=_flatten((bid, filename, snapshot_id)), secondary_text=_flatten((backup.get("status"), backup.get("sha256"))), source_state=state,
                metadata={"snapshot_id": snapshot_id, "filename": filename},
            ))
        return tuple(entities)


class SearchRanker:
    @staticmethod
    def score(entity: SearchEntity, parsed: ParsedQuery) -> tuple[int, str] | None:
        q = parsed.normalized
        if not q:
            return None
        stable = _norm(entity.stable_id)
        label = _norm(entity.label)
        primary = entity.primary_text or _flatten((entity.stable_id, entity.label))
        secondary = entity.secondary_text or _norm(entity.context)
        id_parts = {_norm(part) for part in re.split(r"[:/•\s]+", entity.stable_id) if part}
        if q == stable or q in id_parts:
            return 100, "exact_id"
        if q == label:
            return 90, "exact_label"
        if stable.startswith(q) or label.startswith(q) or any(token.startswith(q) for token in primary.split()):
            return 80, "prefix"
        if parsed.quoted and all(phrase in f"{primary} {secondary}" for phrase in parsed.quoted):
            return 75, "quoted_phrase"
        if q in primary:
            return 70, "phrase"
        if parsed.tokens and all(token in f"{primary} {secondary}" for token in parsed.tokens):
            return 65, "tokens"
        if q in secondary:
            return 60, "secondary"
        return None


class NavigationResolver:
    def resolve(self, entity: SearchEntity | dict[str, Any]) -> NavigationTarget:
        if isinstance(entity, SearchEntity):
            return NavigationTarget(entity.route, entity.route_entity_id, entity.route_sub_id)
        return NavigationTarget(str(entity.get("route") or "dashboard"), str(entity.get("route_entity_id") or ""), str(entity.get("route_sub_id") or ""))


class GlobalSearchService:
    def __init__(self, project_root: Path, *, document: dict[str, Any] | None = None, result_cap: int = 50):
        self.project_root = Path(project_root).resolve()
        self.result_cap = max(1, int(result_cap))
        self.parser = SearchQueryParser()
        self.ranker = SearchRanker()
        self.resolver = NavigationResolver()
        self._document_override = document
        self._entities: tuple[SearchEntity, ...] = ()
        self._index_error: SearchError | None = None
        self.rebuild()

    def _document(self) -> dict[str, Any]:
        if self._document_override is not None:
            return self._document_override
        repository = VersionRepository(self.project_root)
        state = repository.load()
        report = repository.validate(state)
        if not report.is_valid:
            raise SearchError("SEARCH_INDEX_INVALID", "Canonical data tidak valid; search masuk mode degraded.")
        return state.document

    def rebuild(self) -> None:
        try:
            self._entities = SearchIndexer().build(self._document())
            self._index_error = None
        except SearchError as exc:
            self._entities = ()
            self._index_error = exc
        except Exception as exc:
            self._entities = ()
            self._index_error = SearchError("SEARCH_INDEX_INVALID", "Index search gagal dibangun.", {"exception": type(exc).__name__})

    @property
    def ready(self) -> bool:
        return self._index_error is None

    @property
    def entities(self) -> tuple[SearchEntity, ...]:
        return self._entities

    def search(self, query: str, filters: set[str] | None = None, cancel_token: CancelToken | None = None, *, generation: int = 0, result_cap: int | None = None) -> SearchResultPage:
        parsed = self.parser.parse(query)
        if not parsed.normalized:
            return SearchResultPage("IDLE", "", (), "", generation)
        if self._index_error is not None:
            return SearchResultPage("ERROR", parsed.normalized, (), self._index_error.user_message, generation)
        if cancel_token is not None and cancel_token.cancelled:
            raise SearchError("SEARCH_CANCELLED", "Pencarian dibatalkan.")
        allowed = {x.upper() for x in filters} if filters else None
        scored: list[SearchResult] = []
        for entity in self._entities:
            if cancel_token is not None and cancel_token.cancelled:
                raise SearchError("SEARCH_CANCELLED", "Pencarian dibatalkan.")
            if allowed and entity.entity_type not in allowed:
                continue
            score = self.ranker.score(entity, parsed)
            if score is not None:
                scored.append(SearchResult(entity, score[0], score[1]))
        scored.sort(key=lambda item: (-item.score, _ENTITY_ORDER.get(item.entity.entity_type, 99), _norm(item.entity.stable_id), _norm(item.entity.label)))
        cap = max(1, min(int(result_cap or self.result_cap), 200))
        results = tuple(scored[:cap])
        if not results:
            return SearchResultPage("EMPTY", parsed.normalized, (), "Tidak ditemukan. Coba ubah kata pencarian.", generation)
        return SearchResultPage("RESULTS", parsed.normalized, results, f"{len(results)} hasil", generation)
