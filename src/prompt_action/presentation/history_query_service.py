from __future__ import annotations

from pathlib import Path
from typing import Any

from prompt_action.data.repository import VersionRepository
from prompt_action.domain.errors import CanonicalDataError


class SystemHistoryQueryService:
    """Read-only projection of canonical version history for STEP 05."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.repository = VersionRepository(self.project_root)

    def read(self, selected_snapshot_id: str | None = None) -> dict[str, Any]:
        try:
            state = self.repository.load()
        except (CanonicalDataError, OSError) as exc:
            return self._error(f"Canonical data tidak dapat dibaca: {exc}")

        report = self.repository.validate(state)
        if not report.is_valid:
            issues = report.blocking_issues + report.errors
            return self._invalid([f"{item.code}: {item.message}" for item in issues] or ["Canonical data tidak valid."])

        document = state.document
        systems = [dict(item) for item in document.get("systems", []) if isinstance(item, dict)]
        snapshots = [dict(item) for item in document.get("snapshots", []) if isinstance(item, dict)]
        if not systems or not snapshots:
            return self._empty()

        active_system = str(document.get("active_system") or "")
        active_snapshot = str(document.get("active_snapshot") or "")
        legacy = self._legacy_node(document, active_system)
        system_nodes = self._system_nodes(systems, snapshots, active_system, active_snapshot)
        snapshot_ids = {str(item.get("id")) for item in snapshots if item.get("id")}
        selected_id = selected_snapshot_id if selected_snapshot_id in snapshot_ids else active_snapshot
        if selected_id not in snapshot_ids:
            selected_id = str(snapshots[0].get("id") or "")
        selected = next((item for item in snapshots if str(item.get("id")) == selected_id), snapshots[0])
        detail = self._snapshot_detail(document, systems, selected, active_snapshot)

        return {
            "load_state": "ready",
            "legacy": legacy,
            "systems": system_nodes,
            "selected_snapshot_id": str(selected.get("id") or ""),
            "selected_snapshot": detail,
            "active_system": active_system,
            "active_snapshot": active_snapshot,
            "diagnostics": [],
        }

    def _legacy_node(self, document: dict[str, Any], active_system: str) -> dict[str, Any]:
        sources = [item for item in document.get("legacy_sources", []) if isinstance(item, dict)]
        chosen = next((item for item in sources if str(item.get("used_to_seed", "")).startswith(active_system + "/")), sources[0] if sources else None)
        if not chosen:
            return {"available": False, "id": "", "label": "Legacy source tidak tercatat", "verified": False}
        legacy_id = str(chosen.get("id") or "Legacy")
        return {
            "available": True,
            "id": legacy_id,
            "label": f"Legacy {legacy_id}",
            "verified": chosen.get("manifest_verified") is True,
            "file_available": chosen.get("file_available") is True,
            "used_to_seed": str(chosen.get("used_to_seed") or ""),
        }

    def _system_nodes(self, systems: list[dict[str, Any]], snapshots: list[dict[str, Any]], active_system: str, active_snapshot: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for system in systems:
            system_id = str(system.get("id") or "")
            children = []
            for snapshot in snapshots:
                if str(snapshot.get("system") or "") != system_id:
                    continue
                snap_id = str(snapshot.get("id") or "")
                children.append({
                    "id": snap_id,
                    "title": self._snapshot_title(snapshot),
                    "status": str(snapshot.get("status") or "UNKNOWN"),
                    "active": snap_id == active_snapshot,
                    "parent_snapshot": snapshot.get("parent_snapshot"),
                })
            result.append({
                "id": system_id,
                "status": str(system.get("status") or "UNKNOWN"),
                "active": system_id == active_system,
                "created_from_legacy": system.get("created_from_legacy"),
                "generation_reason": system.get("generation_reason"),
                "snapshots": children,
            })
        return result

    @staticmethod
    def _snapshot_title(snapshot: dict[str, Any]) -> str:
        primary = snapshot.get("primary_change")
        if isinstance(primary, dict):
            prompt_id = str(primary.get("prompt_id") or "Prompt")
            return f"Update {prompt_id.replace('P', 'Prompt ', 1) if prompt_id.startswith('P') else prompt_id}"
        return "Baseline"

    def _snapshot_detail(self, document: dict[str, Any], systems: list[dict[str, Any]], snapshot: dict[str, Any], active_snapshot: str) -> dict[str, Any]:
        snapshot_id = str(snapshot.get("id") or "")
        system_id = str(snapshot.get("system") or "")
        system = next((item for item in systems if str(item.get("id")) == system_id), {})
        primary = dict(snapshot["primary_change"]) if isinstance(snapshot.get("primary_change"), dict) else None
        sync = [dict(item) for item in snapshot.get("sync_changes", []) if isinstance(item, dict)]
        changed_prompt_ids: list[str] = []
        if primary and primary.get("prompt_id"):
            changed_prompt_ids.append(str(primary["prompt_id"]))
        for item in sync:
            prompt_id = item.get("prompt_id")
            if prompt_id and str(prompt_id) not in changed_prompt_ids:
                changed_prompt_ids.append(str(prompt_id))

        backups = {item.get("id"): item for item in document.get("backups", []) if isinstance(item, dict) and item.get("id")}
        backup_id = snapshot.get("backup_id")
        backup = backups.get(backup_id) if backup_id else None
        backup_status = "PERLU BACKUP" if str(snapshot.get("status")) == "BACKUP_REQUIRED" else str(backup.get("status") if isinstance(backup, dict) else "BELUM ADA")
        backup_path = self._backup_path(backup)
        parent_snapshot = snapshot.get("parent_snapshot")
        reason = snapshot.get("reason") or (system.get("generation_reason") if primary is None else None) or "Tidak ada alasan perubahan tambahan."

        return {
            "id": snapshot_id,
            "system": system_id,
            "title": self._snapshot_title(snapshot),
            "status": str(snapshot.get("status") or "UNKNOWN"),
            "active": snapshot_id == active_snapshot,
            "parent_snapshot": parent_snapshot,
            "primary_change": primary,
            "sync_changes": sync,
            "changed_prompt_ids": changed_prompt_ids,
            "backup_id": backup_id,
            "backup_status": backup_status,
            "backup_download_path": backup_path,
            "reason": str(reason),
            "prompt_state": dict(snapshot.get("prompt_state") or {}),
            "capabilities": {
                "can_open_detail": True,
                "can_view_changed_prompts": bool(changed_prompt_ids),
                "can_download_snapshot_backup": backup_path is not None,
                "can_compare_previous": bool(parent_snapshot),
                "can_view_changelog": bool(snapshot.get("reason") or primary or sync),
                "disabled_reason_backup": "Backup snapshot tervalidasi belum tersedia." if backup_path is None else "",
                "disabled_reason_compare": "Snapshot baseline tidak memiliki snapshot sebelumnya." if not parent_snapshot else "",
                "disabled_reason_changed_prompts": "Snapshot baseline tidak memiliki PRIMARY/SYNC change." if not changed_prompt_ids else "",
            },
        }

    def _backup_path(self, backup: dict[str, Any] | None) -> str | None:
        if not isinstance(backup, dict) or backup.get("status") != "VALID" or backup.get("verified") is not True:
            return None
        for key in ("file", "path", "archive", "archive_path"):
            value = backup.get(key)
            if not isinstance(value, str) or not value:
                continue
            candidate = (self.project_root / value).resolve()
            try:
                relative = candidate.relative_to(self.project_root)
            except ValueError:
                continue
            if candidate.is_file():
                return str(relative).replace("\\", "/")
        return None

    @staticmethod
    def _error(message: str) -> dict[str, Any]:
        return {"load_state": "error", "legacy": {}, "systems": [], "selected_snapshot_id": "", "selected_snapshot": {}, "active_system": "", "active_snapshot": "", "diagnostics": [message]}

    @staticmethod
    def _invalid(messages: list[str]) -> dict[str, Any]:
        return {"load_state": "invalid", "legacy": {}, "systems": [], "selected_snapshot_id": "", "selected_snapshot": {}, "active_system": "", "active_snapshot": "", "diagnostics": messages}

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {"load_state": "empty", "legacy": {}, "systems": [], "selected_snapshot_id": "", "selected_snapshot": {}, "active_system": "", "active_snapshot": "", "diagnostics": []}
