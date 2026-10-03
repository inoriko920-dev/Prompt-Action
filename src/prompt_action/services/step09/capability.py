from __future__ import annotations

from typing import Any

from .models import Capability


class CapabilityService:
    """One registry for Search/Compare/Download and future-owner gates."""

    FUTURE_ACTIONS = {
        "ADD_REVISION": "Tambah Revisi tersedia pada STEP 10.",
        "CREATE_BACKUP": "Buat Backup final tersedia pada STEP 11.",
        "RESTORE": "Restore tersedia pada STEP 12.",
    }

    def __init__(self, *, search_ready: bool = True):
        self.search_ready = bool(search_ready)

    def get(self, action: str, context: dict[str, Any] | None = None) -> Capability:
        action_name = str(action).upper().strip()
        ctx = context or {}
        if action_name in self.FUTURE_ACTIONS:
            return Capability(False, self.FUTURE_ACTIONS[action_name])
        if action_name == "SEARCH":
            return Capability(self.search_ready, "" if self.search_ready else "Search index belum siap.")
        if action_name == "COMPARE_REVISION":
            if not ctx.get("same_prompt", True):
                return Capability(False, "Bandingkan tidak tersedia: revision berasal dari Prompt berbeda.")
            if int(ctx.get("verified_files", 0)) < 2:
                return Capability(False, "Bandingkan tidak tersedia: dua file revision terverifikasi diperlukan.")
            return Capability(True, "")
        if action_name == "COMPARE_SNAPSHOT":
            if not ctx.get("snapshots_valid", False):
                return Capability(False, "Bandingkan Snapshot tidak tersedia: canonical map belum valid.")
            return Capability(True, "")
        if action_name == "DOWNLOAD_PROMPT":
            if not ctx.get("file_verified", False):
                return Capability(False, "Download tidak tersedia: file Prompt terverifikasi tidak tersedia.")
            return Capability(True, "")
        if action_name == "DOWNLOAD_BACKUP":
            if not ctx.get("artifact_exists", False) or not ctx.get("artifact_verified", False):
                return Capability(False, "Download backup tidak tersedia: artifact terverifikasi belum ada.")
            return Capability(True, "")
        if action_name == "DOWNLOAD_SHA":
            if not ctx.get("sidecar_exists", False):
                return Capability(False, "SHA256 sidecar belum tersedia.")
            return Capability(True, "")
        if action_name == "OPEN_CHANGELOG":
            if not ctx.get("ref_exists", False):
                return Capability(False, "Changelog terverifikasi belum tersedia.")
            return Capability(True, "")
        return Capability(False, "Capability tidak tersedia pada STEP 09.")
