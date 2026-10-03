from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LatestChange:
    snapshot_id: str | None = None
    display_title: str = "Belum ada perubahan"
    occurred_at: str | None = None
    primary_change: dict[str, Any] | None = None
    sync_changes: tuple[dict[str, Any], ...] = ()
    reason_summary: str = ""
    can_open_snapshot: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "display_title": self.display_title,
            "occurred_at": self.occurred_at,
            "primary_change": self.primary_change,
            "sync_changes": [dict(item) for item in self.sync_changes],
            "reason_summary": self.reason_summary,
            "can_open_snapshot": self.can_open_snapshot,
        }


@dataclass(frozen=True, slots=True)
class ActivePromptItem:
    prompt_id: str
    short_label: str
    display_name: str
    active_revision_label: str
    status: str
    file_available: bool
    integrity_state: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "short_label": self.short_label,
            "display_name": self.display_name,
            "active_revision_label": self.active_revision_label,
            "status": self.status,
            "file_available": self.file_available,
            "integrity_state": self.integrity_state,
        }


@dataclass(frozen=True, slots=True)
class BackupChecklistItem:
    key: str
    label: str
    ok: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "label": self.label, "ok": self.ok, "detail": self.detail}


@dataclass(frozen=True, slots=True)
class ActionCapabilities:
    can_download_full_backup: bool = False
    can_open_backup_page: bool = True
    can_request_backup: bool = False
    backup_engine_available: bool = False
    can_open_prompt: bool = True
    can_open_latest_change: bool = False
    backup_download_path: str | None = None
    reason_if_disabled: str = "Backup engine final tersedia pada STEP 11."

    def to_dict(self) -> dict[str, Any]:
        return {
            "can_download_full_backup": self.can_download_full_backup,
            "can_open_backup_page": self.can_open_backup_page,
            "can_request_backup": self.can_request_backup,
            "backup_engine_available": self.backup_engine_available,
            "can_open_prompt": self.can_open_prompt,
            "can_open_latest_change": self.can_open_latest_change,
            "backup_download_path": self.backup_download_path,
            "reason_if_disabled": self.reason_if_disabled,
        }


@dataclass(frozen=True, slots=True)
class DashboardState:
    load_state: str = "loading"
    system_label: str = "—"
    snapshot_label: str = "—"
    active_prompt_count: int = 0
    backup_health: str = "UNKNOWN"
    latest_change: LatestChange = field(default_factory=LatestChange)
    active_prompts: tuple[ActivePromptItem, ...] = ()
    backup_checklist: tuple[BackupChecklistItem, ...] = ()
    recovery_health: str = "UNKNOWN"
    action_capabilities: ActionCapabilities = field(default_factory=ActionCapabilities)
    diagnostics: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "load_state": self.load_state,
            "system_label": self.system_label,
            "snapshot_label": self.snapshot_label,
            "active_prompt_count": self.active_prompt_count,
            "backup_health": self.backup_health,
            "latest_change": self.latest_change.to_dict(),
            "active_prompts": [item.to_dict() for item in self.active_prompts],
            "backup_checklist": [item.to_dict() for item in self.backup_checklist],
            "recovery_health": self.recovery_health,
            "action_capabilities": self.action_capabilities.to_dict(),
            "diagnostics": list(self.diagnostics),
        }

    @classmethod
    def loading(cls) -> "DashboardState":
        return cls(load_state="loading")

    @classmethod
    def empty(cls, message: str = "Belum ada data sistem aktif.") -> "DashboardState":
        return cls(load_state="empty", diagnostics=(message,))

    @classmethod
    def invalid(cls, diagnostics: list[str] | tuple[str, ...]) -> "DashboardState":
        return cls(load_state="invalid", backup_health="ERROR", recovery_health="ERROR", diagnostics=tuple(diagnostics))

    @classmethod
    def error(cls, message: str) -> "DashboardState":
        return cls(load_state="error", backup_health="ERROR", recovery_health="ERROR", diagnostics=(message,))
