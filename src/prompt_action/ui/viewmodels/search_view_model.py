from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot

from prompt_action.services.step09 import CancelToken, GlobalSearchService, SearchError


class SearchViewModel(QObject):
    stateChanged = Signal()
    navigationRequested = Signal(str, str, str)

    def __init__(self, project_root: Path, *, service: GlobalSearchService | None = None, debounce_ms: int = 170):
        super().__init__()
        self._service = service or GlobalSearchService(Path(project_root).resolve())
        self._debounce_ms = max(0, int(debounce_ms))
        self._generation = 0
        self._pending_query = ""
        self._cancel_token = CancelToken()
        self._selected_index = -1
        self._state: dict[str, Any] = {
            "state": "IDLE", "query": "", "results": [], "message": "",
            "generation": 0, "selected_index": -1, "service_ready": self._service.ready,
        }

    @Property("QVariant", notify=stateChanged)
    def state(self) -> dict[str, Any]:
        return dict(self._state)

    def _publish(self, page: dict[str, Any], *, selected_index: int | None = None) -> None:
        self._selected_index = selected_index if selected_index is not None else (-1 if not page.get("results") else 0)
        self._state = dict(page)
        self._state["selected_index"] = self._selected_index
        self._state["service_ready"] = self._service.ready
        self.stateChanged.emit()

    @Slot(str)
    def setQuery(self, query: str) -> None:
        self._generation += 1
        generation = self._generation
        self._cancel_token.cancel()
        self._cancel_token = CancelToken()
        self._pending_query = str(query)
        if not str(query).strip():
            self._publish(self._service.search("", generation=generation).to_dict())
            return
        previous = list(self._state.get("results", []))
        self._state = {
            "state": "SEARCHING", "query": str(query), "results": previous,
            "message": "Mencari…", "generation": generation,
            "selected_index": self._selected_index, "service_ready": self._service.ready,
        }
        self.stateChanged.emit()
        QTimer.singleShot(self._debounce_ms, lambda: self._run_generation(generation))

    def _run_generation(self, generation: int) -> None:
        if generation != self._generation:
            return
        try:
            page = self._service.search(self._pending_query, self._cancel_token, generation=generation)
        except TypeError:
            page = self._service.search(self._pending_query, cancel_token=self._cancel_token, generation=generation)
        except SearchError as exc:
            self._publish({"state": "ERROR", "query": self._pending_query, "results": [], "message": exc.user_message, "generation": generation})
            return
        if generation != self._generation:
            return
        self._publish(page.to_dict())

    @Slot()
    def forceSearch(self) -> None:
        self._generation += 1
        generation = self._generation
        self._cancel_token.cancel()
        self._cancel_token = CancelToken()
        try:
            page = self._service.search(self._pending_query, cancel_token=self._cancel_token, generation=generation)
        except SearchError as exc:
            self._publish({"state": "ERROR", "query": self._pending_query, "results": [], "message": exc.user_message, "generation": generation})
            return
        self._publish(page.to_dict())

    @Slot(int)
    def moveSelection(self, delta: int) -> None:
        results = self._state.get("results", [])
        if not results:
            self._selected_index = -1
            return
        self._selected_index = max(0, min(len(results) - 1, self._selected_index + int(delta)))
        self._state["selected_index"] = self._selected_index
        self.stateChanged.emit()

    @Slot(int)
    def activate(self, index: int) -> None:
        results = self._state.get("results", [])
        if not isinstance(results, list) or not results:
            return
        resolved_index = int(index)
        if resolved_index < 0:
            resolved_index = self._selected_index
        if not 0 <= resolved_index < len(results):
            return
        item = results[resolved_index]
        self.navigationRequested.emit(str(item.get("route") or "dashboard"), str(item.get("route_entity_id") or ""), str(item.get("route_sub_id") or ""))

    @Slot()
    def activateSelected(self) -> None:
        self.activate(self._selected_index)

    @Slot()
    def closeResults(self) -> None:
        self._generation += 1
        self._cancel_token.cancel()
        self._publish({"state": "IDLE", "query": self._pending_query, "results": [], "message": "", "generation": self._generation}, selected_index=-1)
