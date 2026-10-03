from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from prompt_action.data.repository import VersionRepository
from prompt_action.domain.errors import CanonicalDataError, ValidationBlockedError
from prompt_action.domain.validation import sha256_file
from prompt_action.services.version_engine import VersionEngine

from .dashboard_models import (
    ActionCapabilities,
    ActivePromptItem,
    BackupChecklistItem,
    DashboardState,
    LatestChange,
)

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


class DashboardQueryService:
    """Read-only adapter from canonical VersionEngine state to DashboardState."""

    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.repository = VersionRepository(self.project_root)
        self.engine = VersionEngine(self.repository)

    def read(self) -> DashboardState:
        try:
            state = self.repository.load()
        except CanonicalDataError as exc:
            return DashboardState.error(f"Canonical data tidak dapat dibaca: {exc}")
        except OSError as exc:
            return DashboardState.error(f"I/O canonical data gagal: {exc}")

        report = self.repository.validate(state)
        if not report.is_valid:
            diagnostics = [f"{item.code}: {item.message}" for item in report.blocking_issues + report.errors]
            return DashboardState.invalid(diagnostics or ["Canonical data tidak valid."])

        document = state.document
        if not document.get("systems") or not document.get("snapshots") or not document.get("prompts"):
            return DashboardState.empty()

        try:
            context = self.engine.get_active_context()
        except ValidationBlockedError as exc:
            return DashboardState.invalid([str(exc)])
        except Exception as exc:  # defensive presentation boundary
            return DashboardState.error(f"Gagal membaca konteks aktif: {exc}")

        snapshot = context["snapshot"]
        system = context["system"]
        prompt_items, prompt_diagnostics = self._active_prompts(document, snapshot)
        latest = self._latest_change(system, snapshot)
        backup_health, recovery_health, checklist, capabilities, backup_diagnostics = self._backup_state(document, snapshot)
        diagnostics = prompt_diagnostics + backup_diagnostics

        degraded = any(item.integrity_state in {"MISSING_SOURCE", "INTEGRITY_WARNING", "ERROR"} for item in prompt_items)
        load_state = "degraded" if degraded else "ready"
        return DashboardState(
            load_state=load_state,
            system_label=str(system.get("id") or "—"),
            snapshot_label=str(snapshot.get("id") or "—"),
            active_prompt_count=len(prompt_items),
            backup_health=backup_health,
            latest_change=latest,
            active_prompts=tuple(prompt_items),
            backup_checklist=tuple(checklist),
            recovery_health=recovery_health,
            action_capabilities=capabilities,
            diagnostics=tuple(diagnostics),
        )

    def _active_prompts(self, document: dict[str, Any], snapshot: dict[str, Any]) -> tuple[list[ActivePromptItem], list[str]]:
        items: list[ActivePromptItem] = []
        diagnostics: list[str] = []
        prompt_state = snapshot.get("prompt_state", {})
        protected = document.get("integrity", {}).get("protected_prompt_hashes", {})
        baseline_verified = document.get("integrity", {}).get("baseline_verification") == "STEP_00_PASS"

        for prompt_id, revision_id in prompt_state.items():
            prompt = document.get("prompts", {}).get(prompt_id, {})
            revision = prompt.get("revisions", {}).get(revision_id, {})
            file_available = revision.get("file_available") is True
            integrity_state = "MISSING_SOURCE"
            if file_available:
                file_value = revision.get("file")
                expected = revision.get("sha256")
                if isinstance(file_value, str) and isinstance(expected, str):
                    path = (self.project_root / file_value).resolve()
                    try:
                        path.relative_to(self.project_root)
                        integrity_state = "VERIFIED_FILE" if path.is_file() and sha256_file(path) == expected else "ERROR"
                    except ValueError:
                        integrity_state = "ERROR"
            else:
                expected = revision.get("sha256")
                protected_hash = protected.get(prompt_id)
                if (
                    revision.get("change_role") == "BASELINE"
                    and baseline_verified
                    and isinstance(expected, str)
                    and _SHA_RE.fullmatch(expected)
                    and protected_hash == expected
                ):
                    integrity_state = "VERIFIED_BASELINE"

            if integrity_state in {"MISSING_SOURCE", "ERROR"}:
                diagnostics.append(f"{prompt_id} {revision_id}: sumber aktif belum terverifikasi penuh.")

            display_name = str(prompt.get("display_name") or prompt_id)
            items.append(
                ActivePromptItem(
                    prompt_id=str(prompt_id),
                    short_label=str(prompt_id).replace("P", "Prompt ", 1),
                    display_name=display_name,
                    active_revision_label=str(revision_id),
                    status=str(revision.get("status") or "UNKNOWN"),
                    file_available=file_available,
                    integrity_state=integrity_state,
                )
            )
        return items, diagnostics

    @staticmethod
    def _latest_change(system: dict[str, Any], snapshot: dict[str, Any]) -> LatestChange:
        snapshot_id = snapshot.get("id")
        primary = snapshot.get("primary_change")
        sync_changes = snapshot.get("sync_changes") if isinstance(snapshot.get("sync_changes"), list) else []
        occurred_at = snapshot.get("occurred_at") or snapshot.get("created_at")

        if isinstance(primary, dict):
            prompt_id = primary.get("prompt_id", "Prompt")
            from_revision = primary.get("from", "—")
            to_revision = primary.get("to", "—")
            title = f"{prompt_id}: {from_revision} → {to_revision}"
            reason = str(snapshot.get("reason") or f"Perubahan PRIMARY pada {snapshot_id}.")
        else:
            title = "Baseline sistem aktif"
            reason = str(
                snapshot.get("reason")
                or system.get("generation_reason")
                or "Snapshot baseline tanpa perubahan PRIMARY palsu."
            )

        return LatestChange(
            snapshot_id=str(snapshot_id) if snapshot_id else None,
            display_title=title,
            occurred_at=str(occurred_at) if occurred_at else None,
            primary_change=dict(primary) if isinstance(primary, dict) else None,
            sync_changes=tuple(dict(item) for item in sync_changes if isinstance(item, dict)),
            reason_summary=reason,
            can_open_snapshot=bool(snapshot_id),
        )

    def _backup_state(
        self, document: dict[str, Any], snapshot: dict[str, Any]
    ) -> tuple[str, str, list[BackupChecklistItem], ActionCapabilities, list[str]]:
        diagnostics: list[str] = []
        backup_id = snapshot.get("backup_id")
        backups = {
            item.get("id"): item
            for item in document.get("backups", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        backup = backups.get(backup_id) if isinstance(backup_id, str) else None

        full_backup = isinstance(backup, dict)
        sha_ok = bool(full_backup and isinstance(backup.get("sha256"), str) and _SHA_RE.fullmatch(backup["sha256"]))
        zip_verified = bool(full_backup and backup.get("verified") is True)
        second_copy = bool(full_backup and backup.get("second_copy_verified") is True)
        checklist = [
            BackupChecklistItem("full_backup", "Full Backup", full_backup, "Backup record tersedia" if full_backup else "Belum tersedia"),
            BackupChecklistItem("sha256", "SHA256", sha_ok, "Checksum valid" if sha_ok else "Belum tervalidasi"),
            BackupChecklistItem("zip_verified", "Verifikasi ZIP", zip_verified, "ZIP terverifikasi" if zip_verified else "Belum terverifikasi"),
            BackupChecklistItem("second_copy", "Salinan Kedua", second_copy, "Salinan kedua terverifikasi" if second_copy else "Belum tersedia"),
        ]

        snapshot_status = str(snapshot.get("status") or "UNKNOWN")
        if snapshot_status == "COMPLETE" and full_backup and backup.get("status") == "VALID" and zip_verified and second_copy:
            backup_health = "AMAN"
            recovery_health = "READY"
        elif snapshot_status in {"BACKUP_REQUIRED", "BACKUP_FAILED"}:
            backup_health = "PERLU BACKUP"
            recovery_health = "REQUIRED"
        elif snapshot_status == "COMPLETE":
            backup_health = "ERROR"
            recovery_health = "ERROR"
            diagnostics.append("Snapshot COMPLETE tidak memiliki evidence backup/recovery yang lengkap.")
        else:
            backup_health = "UNKNOWN"
            recovery_health = "UNKNOWN"

        download_path = self._resolve_backup_download_path(backup)
        can_download = download_path is not None
        capabilities = ActionCapabilities(
            can_download_full_backup=can_download,
            can_open_backup_page=True,
            can_request_backup=False,
            backup_engine_available=False,
            can_open_prompt=True,
            can_open_latest_change=bool(snapshot.get("id")),
            backup_download_path=str(download_path.relative_to(self.project_root)).replace("\\", "/") if download_path else None,
            reason_if_disabled="Backup engine final belum tersedia pada STEP 04; gunakan halaman Backup & Recovery untuk melihat status.",
        )
        return backup_health, recovery_health, checklist, capabilities, diagnostics

    def _resolve_backup_download_path(self, backup: dict[str, Any] | None) -> Path | None:
        if not isinstance(backup, dict) or backup.get("status") != "VALID" or backup.get("verified") is not True:
            return None
        for key in ("file", "path", "archive", "archive_path"):
            value = backup.get(key)
            if not isinstance(value, str) or not value:
                continue
            candidate = (self.project_root / value).resolve()
            try:
                candidate.relative_to(self.project_root)
            except ValueError:
                continue
            if candidate.is_file():
                return candidate
        return None
