from __future__ import annotations

import hashlib
from pathlib import Path, PureWindowsPath
import re
from typing import Any

from prompt_action.data.repository import VersionRepository
from prompt_action.domain.errors import CanonicalDataError
from .per_prompt_models import FileState, INTEGRITY_DEGRADED_CODES


class PerPromptQueryService:
    """Read-only canonical projection for STEP 06 Per Prompt."""

    def __init__(self, project_root: Path, *, repository: VersionRepository | None = None):
        self.project_root = Path(project_root).resolve()
        self.repository = repository or VersionRepository(self.project_root)

    def read(self, selected_prompt_id: str | None = None, selected_revision_id: str | None = None) -> dict[str, Any]:
        try:
            state = self.repository.load()
        except (CanonicalDataError, OSError) as exc:
            return self._error(f"Canonical data tidak dapat dibaca: {exc}")

        report = self.repository.validate(state)
        all_issues = report.blocking_issues + report.errors + report.warnings
        hard_issues = [issue for issue in report.blocking_issues + report.errors if issue.code not in INTEGRITY_DEGRADED_CODES]
        if hard_issues:
            return self._invalid([f"{item.code}: {item.message}" for item in hard_issues])

        document = state.document
        prompts = document.get("prompts", {}) if isinstance(document.get("prompts"), dict) else {}
        if not prompts:
            return self._empty()

        snapshots = {
            str(item.get("id")): item
            for item in document.get("snapshots", [])
            if isinstance(item, dict) and item.get("id")
        }
        active_snapshot_id = str(document.get("active_snapshot") or "")
        active_snapshot = snapshots.get(active_snapshot_id, {})
        active_prompt_state = active_snapshot.get("prompt_state", {}) if isinstance(active_snapshot, dict) else {}

        prompt_ids = list(prompts.keys())
        prompt_id = selected_prompt_id if selected_prompt_id in prompts else prompt_ids[0]
        prompt = prompts[prompt_id] if isinstance(prompts.get(prompt_id), dict) else {}
        revisions = prompt.get("revisions", {}) if isinstance(prompt.get("revisions"), dict) else {}
        if not revisions:
            return self._invalid([f"Prompt {prompt_id} tidak memiliki official revision."])

        active_revision_id = str(active_prompt_state.get(prompt_id) or prompt.get("active_revision") or "")
        if active_revision_id not in revisions:
            return self._invalid([f"Active revision {active_revision_id!r} untuk {prompt_id} tidak ada di revision graph."])

        drafts, draft_issues = self._draft_nodes(prompt.get("drafts"), revisions)
        if draft_issues:
            return self._invalid(draft_issues)
        draft_by_id = {item["id"]: item for item in drafts}

        selected_id = selected_revision_id or active_revision_id
        if selected_id not in revisions and selected_id not in draft_by_id:
            selected_id = active_revision_id

        official_nodes = [
            self._revision_node(prompt_id, revision_id, revisions[revision_id], active_revision_id, selected_id)
            for revision_id in sorted(revisions, key=self._revision_sort_key)
        ]
        for draft in drafts:
            draft["selected"] = draft["id"] == selected_id

        if selected_id in revisions:
            detail = self._official_detail(document, prompt_id, prompt, selected_id, revisions[selected_id], snapshots, active_revision_id)
        else:
            detail = self._draft_detail(prompt_id, prompt, draft_by_id[selected_id], active_revision_id)

        active_node = next(item for item in official_nodes if item["id"] == active_revision_id)
        selected_file = self._file_projection(detail)
        active_file = self._file_projection(active_node)
        capabilities = self._capabilities(detail, active_file, selected_file)
        prompt_items = []
        for pid, record in prompts.items():
            record = record if isinstance(record, dict) else {}
            active_for_prompt = str(active_prompt_state.get(pid) or record.get("active_revision") or "")
            prompt_items.append({
                "id": pid,
                "display_name": str(record.get("display_name") or pid),
                "active_revision": active_for_prompt,
                "selected": pid == prompt_id,
            })

        issue_payload = [item.to_dict() for item in all_issues]
        load_state = "degraded" if any(item.code in INTEGRITY_DEGRADED_CODES for item in report.blocking_issues + report.errors) else "ready"
        return {
            "load_state": load_state,
            "prompts": prompt_items,
            "selected_prompt_id": prompt_id,
            "selected_prompt_name": str(prompt.get("display_name") or prompt_id),
            "active_revision_id": active_revision_id,
            "selected_revision_id": selected_id,
            "official_revisions": official_nodes,
            "drafts": drafts,
            "selected_revision": detail,
            "available_files": [
                {"kind": "ACTIVE", "label": "Prompt Aktif", **active_file},
                {"kind": "SELECTED", "label": "Revision Dipilih", **selected_file},
            ],
            "capabilities": capabilities,
            "active_system": str(document.get("active_system") or ""),
            "active_snapshot": active_snapshot_id,
            "issues": issue_payload,
            "diagnostics": [],
        }

    @staticmethod
    def _revision_sort_key(revision_id: str) -> tuple[int, str]:
        match = re.fullmatch(r"R([1-9][0-9]*)", str(revision_id))
        return (int(match.group(1)), str(revision_id)) if match else (10**9, str(revision_id))

    def _revision_node(self, prompt_id: str, revision_id: str, revision: Any, active_revision_id: str, selected_id: str) -> dict[str, Any]:
        record = revision if isinstance(revision, dict) else {}
        file_info = self._file_info(record)
        return {
            "id": revision_id,
            "prompt_id": prompt_id,
            "parent": record.get("parent"),
            "snapshot": record.get("snapshot"),
            "status": str(record.get("status") or "UNKNOWN"),
            "active": revision_id == active_revision_id,
            "selected": revision_id == selected_id,
            "change_role": str(record.get("change_role") or "UNKNOWN"),
            "summary": [str(item) for item in record.get("summary", []) if isinstance(item, str)],
            "reason": str(record.get("reason") or ""),
            **file_info,
        }

    def _official_detail(self, document: dict[str, Any], prompt_id: str, prompt: dict[str, Any], revision_id: str, revision: dict[str, Any], snapshots: dict[str, dict[str, Any]], active_revision_id: str) -> dict[str, Any]:
        snapshot_id = str(revision.get("snapshot") or "")
        snapshot = snapshots.get(snapshot_id, {})
        primary = snapshot.get("primary_change") if isinstance(snapshot.get("primary_change"), dict) else None
        sync = [item for item in snapshot.get("sync_changes", []) if isinstance(item, dict)] if isinstance(snapshot, dict) else []
        changed_items: list[dict[str, Any]] = []
        if primary:
            changed_items.append({"role": "PRIMARY", **dict(primary)})
        changed_items.extend({"role": "SYNC", **dict(item)} for item in sync)
        selected_change = next((item for item in changed_items if str(item.get("prompt_id")) == prompt_id), None)
        role = str(selected_change.get("role")) if selected_change else str(revision.get("change_role") or "BASELINE")
        affected = [str(item.get("prompt_id")) for item in changed_items if item.get("prompt_id")]
        sync_impacts = [item for item in changed_items if str(item.get("prompt_id")) != prompt_id]
        file_info = self._file_info(revision)
        return {
            "id": revision_id,
            "prompt_id": prompt_id,
            "prompt_name": str(prompt.get("display_name") or prompt_id),
            "parent": revision.get("parent"),
            "snapshot": snapshot_id,
            "status": str(revision.get("status") or "UNKNOWN"),
            "active": revision_id == active_revision_id,
            "selected": True,
            "is_draft": False,
            "change_role": role,
            "change_item": dict(selected_change) if isinstance(selected_change, dict) else None,
            "affected_prompts": affected,
            "sync_impacts": sync_impacts,
            "summary": [str(item) for item in revision.get("summary", []) if isinstance(item, str)],
            "reason": str(revision.get("reason") or ""),
            "prompt_state_at_snapshot": dict(snapshot.get("prompt_state") or {}) if isinstance(snapshot, dict) else {},
            **file_info,
        }

    def _draft_nodes(self, raw: Any, revisions: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
        if raw is None:
            return [], []
        entries: list[tuple[str, dict[str, Any]]] = []
        issues: list[str] = []
        if isinstance(raw, dict):
            for draft_id, value in raw.items():
                if not isinstance(value, dict):
                    issues.append(f"Draft {draft_id} harus berupa object.")
                    continue
                entries.append((str(draft_id), value))
        elif isinstance(raw, list):
            seen: set[str] = set()
            for index, value in enumerate(raw):
                if not isinstance(value, dict) or not value.get("id"):
                    issues.append(f"Draft index {index} tidak memiliki stable draft ID.")
                    continue
                draft_id = str(value["id"])
                if draft_id in seen:
                    issues.append(f"Duplicate draft ID: {draft_id}")
                    continue
                seen.add(draft_id)
                entries.append((draft_id, value))
        else:
            return [], ["Container drafts harus object/list."]

        draft_ids = {draft_id for draft_id, _ in entries}
        nodes: list[dict[str, Any]] = []
        parents: dict[str, str | None] = {}
        for draft_id, value in entries:
            if re.fullmatch(r"R[1-9][0-9]*", draft_id):
                issues.append(f"Draft {draft_id} tidak boleh memakai nomor R resmi.")
            parent = value.get("parent")
            if parent is not None and parent not in revisions and str(parent) not in draft_ids:
                issues.append(f"Draft {draft_id} menunjuk parent yang tidak ada: {parent}")
            parents[draft_id] = str(parent) if parent is not None else None
            nodes.append({
                "id": draft_id,
                "title": str(value.get("title") or draft_id),
                "parent": parent,
                "status": "DRAFT",
                "active": False,
                "selected": False,
                "snapshot": value.get("snapshot"),
                "summary": [str(item) for item in value.get("summary", []) if isinstance(item, str)],
                "reason": str(value.get("reason") or ""),
                **self._file_info(value),
            })
        for start in draft_ids:
            seen: set[str] = set()
            current: str | None = start
            while current is not None and current in draft_ids:
                if current in seen:
                    issues.append(f"Draft graph cycle terdeteksi dari {start}.")
                    break
                seen.add(current)
                current = parents.get(current)
        return nodes, issues

    def _draft_detail(self, prompt_id: str, prompt: dict[str, Any], draft: dict[str, Any], active_revision_id: str) -> dict[str, Any]:
        return {
            "id": draft["id"],
            "prompt_id": prompt_id,
            "prompt_name": str(prompt.get("display_name") or prompt_id),
            "parent": draft.get("parent"),
            "snapshot": draft.get("snapshot"),
            "status": "DRAFT",
            "active": False,
            "selected": True,
            "is_draft": True,
            "change_role": "DRAFT",
            "change_item": None,
            "affected_prompts": [],
            "sync_impacts": [],
            "summary": list(draft.get("summary") or []),
            "reason": str(draft.get("reason") or ""),
            "prompt_state_at_snapshot": {},
            "active_revision_id": active_revision_id,
            **self._file_projection(draft),
        }

    def _file_info(self, revision: dict[str, Any]) -> dict[str, Any]:
        file_value = revision.get("file")
        sha_value = revision.get("sha256")
        available = revision.get("file_available")
        relative_path: str | None = None
        candidate: Path | None = None
        if isinstance(file_value, str) and file_value:
            path = Path(file_value)
            if not path.is_absolute() and not PureWindowsPath(file_value).is_absolute():
                resolved = (self.project_root / path).resolve()
                try:
                    resolved.relative_to(self.project_root)
                    candidate = resolved
                    relative_path = str(path).replace("\\", "/")
                except ValueError:
                    candidate = None
        if available is True:
            if candidate is None or not candidate.is_file():
                state = FileState.MISSING
            elif not isinstance(sha_value, str) or re.fullmatch(r"[0-9a-f]{64}", sha_value) is None:
                state = FileState.UNKNOWN
            else:
                actual = self._sha256(candidate)
                state = FileState.VALID if actual == sha_value else FileState.HASH_MISMATCH
        elif available is False:
            state = FileState.HISTORY_ONLY if isinstance(sha_value, str) and bool(sha_value) else FileState.MISSING
        else:
            state = FileState.UNKNOWN
        return {
            "file_state": state.value,
            "file_path": relative_path,
            "file_name": Path(relative_path).name if relative_path else "Belum dimaterialisasi",
            "sha256": str(sha_value or ""),
            "file_available": available is True,
        }

    @staticmethod
    def _file_projection(value: dict[str, Any]) -> dict[str, Any]:
        return {
            "revision_id": str(value.get("id") or ""),
            "file_state": str(value.get("file_state") or FileState.UNKNOWN.value),
            "file_path": value.get("file_path"),
            "file_name": str(value.get("file_name") or "Belum dimaterialisasi"),
            "sha256": str(value.get("sha256") or ""),
            "file_available": value.get("file_available") is True,
        }

    @staticmethod
    def _capabilities(detail: dict[str, Any], active_file: dict[str, Any], selected_file: dict[str, Any]) -> dict[str, Any]:
        parent = detail.get("parent")
        snapshot = detail.get("snapshot")
        return {
            "can_download_active": active_file.get("file_state") == FileState.VALID.value and bool(active_file.get("file_path")),
            "can_download_selected": selected_file.get("file_state") == FileState.VALID.value and bool(selected_file.get("file_path")),
            "can_compare": False,
            "can_view_snapshot": bool(snapshot),
            "can_view_changelog": False,
            "can_add_revision": False,
            "active_download_path": active_file.get("file_path"),
            "selected_download_path": selected_file.get("file_path"),
            "compare_parent": parent,
            "disabled_reason_active_download": "File Prompt aktif belum tersedia/terverifikasi." if active_file.get("file_state") != FileState.VALID.value else "",
            "disabled_reason_selected_download": "File revision dipilih belum tersedia/terverifikasi." if selected_file.get("file_state") != FileState.VALID.value else "",
            "disabled_reason_compare": "Engine perbandingan final belum tersedia pada STEP 06." if parent else "Revision baseline tidak memiliki parent untuk dibandingkan.",
            "disabled_reason_changelog": "View changelog final belum tersedia pada STEP 06.",
            "disabled_reason_add_revision": "Tambah Revisi baru tersedia pada STEP 10.",
        }

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _base(load_state: str, diagnostics: list[str] | None = None) -> dict[str, Any]:
        return {
            "load_state": load_state,
            "prompts": [],
            "selected_prompt_id": "",
            "selected_prompt_name": "",
            "active_revision_id": "",
            "selected_revision_id": "",
            "official_revisions": [],
            "drafts": [],
            "selected_revision": {},
            "available_files": [],
            "capabilities": {},
            "active_system": "",
            "active_snapshot": "",
            "issues": [],
            "diagnostics": diagnostics or [],
        }

    @classmethod
    def _error(cls, message: str) -> dict[str, Any]:
        return cls._base("error", [message])

    @classmethod
    def _invalid(cls, messages: list[str]) -> dict[str, Any]:
        return cls._base("invalid", messages)

    @classmethod
    def _empty(cls) -> dict[str, Any]:
        return cls._base("empty")
