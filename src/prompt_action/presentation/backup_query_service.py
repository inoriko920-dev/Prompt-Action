from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from prompt_action.data.repository import VersionRepository


class BackupRecoveryQueryService:
    def __init__(self, project_root: Path):
        self.root = Path(project_root)
        self.repository = VersionRepository(self.root)

    def _real_file(self, value: Any) -> Path | None:
        if not value or not isinstance(value, str):
            return None
        p = Path(value)
        if p.is_absolute() or ".." in p.parts:
            return None
        resolved = (self.root / p).resolve()
        try:
            resolved.relative_to(self.root.resolve())
        except ValueError:
            return None
        return resolved if resolved.is_file() else None

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def _backup_projection(self, raw: dict[str, Any]) -> dict[str, Any]:
        zip_path = self._real_file(raw.get("file") or raw.get("zip") or raw.get("path"))
        sha_path = self._real_file(raw.get("sha256_file") or raw.get("checksum_file"))
        second_path = self._real_file(raw.get("second_copy") or raw.get("second_copy_path"))
        expected = raw.get("sha256")
        hash_ok = bool(zip_path and expected and self._sha256(zip_path).lower() == str(expected).lower())
        verified = bool(raw.get("verified") is True or raw.get("verify_status") in {"PASS", "VALID"}) and hash_ok
        second_ok = bool(second_path)
        valid = bool(zip_path and hash_ok and verified and second_ok)
        return {
            "id": str(raw.get("id") or ""),
            "snapshot": str(raw.get("snapshot") or raw.get("snapshot_id") or ""),
            "system": str(raw.get("system") or raw.get("system_id") or ""),
            "file_name": zip_path.name if zip_path else str(raw.get("file_name") or "Backup belum tersedia"),
            "file_path": str(zip_path.relative_to(self.root)) if zip_path else None,
            "sha256": expected,
            "sha256_file": str(sha_path.relative_to(self.root)) if sha_path else None,
            "hash_valid": hash_ok,
            "verified": verified,
            "second_copy": second_ok,
            "second_copy_path": str(second_path.relative_to(self.root)) if second_path else None,
            "valid": valid,
            "size_bytes": zip_path.stat().st_size if zip_path else None,
            "created_at": raw.get("created_at"),
        }

    def read(self) -> dict[str, Any]:
        try:
            state = self.repository.load()
            report = self.repository.validate(state)
        except Exception as exc:
            return {"load_state": "error", "diagnostics": [str(exc)], "checklist": [], "history": [], "latest_backup": None, "actions": {}}
        if not report.is_valid:
            return {"load_state": "invalid", "diagnostics": [i.message for i in report.issues], "checklist": [], "history": [], "latest_backup": None, "actions": {}}

        doc = state.document
        active_snapshot_id = doc.get("active_snapshot")
        snapshots = doc.get("snapshots", [])
        active_snapshot = next((s for s in snapshots if s.get("id") == active_snapshot_id), None)
        prompts = doc.get("prompts", {})
        backups = [self._backup_projection(b) for b in doc.get("backups", []) if isinstance(b, dict)]
        active_backup = None
        if active_snapshot:
            backup_id = active_snapshot.get("backup_id")
            active_backup = next((b for b in backups if (backup_id and b["id"] == backup_id) or b["snapshot"] == active_snapshot_id), None)

        active_prompt_files_ok = True
        all_revision_files_ok = True
        revision_count = 0
        for prompt in prompts.values():
            revisions = prompt.get("revisions", {}) if isinstance(prompt, dict) else {}
            active_id = prompt.get("active_revision") if isinstance(prompt, dict) else None
            for rid, rev in revisions.items():
                revision_count += 1
                materialized = bool(rev.get("file_available") and self._real_file(rev.get("file")))
                all_revision_files_ok = all_revision_files_ok and materialized
                if rid == active_id:
                    active_prompt_files_ok = active_prompt_files_ok and materialized

        version_data_ok = (self.root / "data/version_history.json").is_file()
        changelog_ok = any((self.root / p).is_file() for p in ["CHANGELOG.md", "docs/CHANGELOG.md"])
        full_ok = bool(active_backup and active_backup["file_path"])
        sha_ok = bool(active_backup and active_backup["hash_valid"])
        verify_ok = bool(active_backup and active_backup["verified"])
        second_ok = bool(active_backup and active_backup["second_copy"])
        checklist = [
            {"key": "active_prompts", "label": "Prompt aktif tersimpan", "ok": active_prompt_files_ok, "detail": "Semua prompt aktif termaterialisasi" if active_prompt_files_ok else "File prompt aktif belum lengkap"},
            {"key": "revisions", "label": "Revision lama tersimpan", "ok": all_revision_files_ok, "detail": f"{revision_count} revision terdeteksi" if all_revision_files_ok else "Revision masih history-only / belum termaterialisasi"},
            {"key": "version_data", "label": "VERSION_DATA tersimpan", "ok": version_data_ok, "detail": "data/version_history.json tersedia" if version_data_ok else "Metadata canonical tidak tersedia"},
            {"key": "changelog", "label": "Changelog tersimpan", "ok": changelog_ok, "detail": "Changelog tersedia" if changelog_ok else "Changelog final belum tersedia"},
            {"key": "full_backup", "label": "Full Backup ZIP", "ok": full_ok, "detail": active_backup["file_name"] if full_ok else "Belum tersedia"},
            {"key": "sha256", "label": "SHA256", "ok": sha_ok, "detail": "VALID" if sha_ok else "Belum valid"},
            {"key": "zip_verified", "label": "ZIP terverifikasi", "ok": verify_ok, "detail": "PASS" if verify_ok else "Belum terverifikasi"},
            {"key": "second_copy", "label": "Salinan kedua", "ok": second_ok, "detail": "Tersedia" if second_ok else "Belum tersedia"},
        ]
        safe = all(item["ok"] for item in checklist)

        history = []
        for snap in snapshots:
            sid = str(snap.get("id") or "")
            bid = snap.get("backup_id")
            b = next((item for item in backups if (bid and item["id"] == bid) or item["snapshot"] == sid), None)
            status = "VALID" if b and b["valid"] else "FAILED" if b else "REQUIRED"
            history.append({"snapshot": sid, "system": snap.get("system"), "status": status, "active": sid == active_snapshot_id, "backup_id": b["id"] if b else None})

        can_create = active_prompt_files_ok and all_revision_files_ok and version_data_ok
        actions = {
            "can_download_backup": bool(active_backup and active_backup["valid"] and active_backup["file_path"]),
            "can_download_sha256": bool(active_backup and active_backup["sha256_file"]),
            "can_verify_backup": bool(active_backup and active_backup["file_path"]),
            "can_open_folder": bool(active_backup and active_backup["file_path"]),
            "can_open_recovery_guide": (self.root / "docs/VERSIONING_RULES.md").is_file(),
            "can_create_backup": can_create,
            "can_restore_backup": False,
            "disabled_reason_create": "Source prompt/revision belum termaterialisasi lengkap." if not can_create else "Backup writer final belum diaktifkan pada STEP 07.",
            "disabled_reason_restore": "Restore writer belum tersedia pada STEP 07.",
        }
        if can_create:
            actions["can_create_backup"] = False

        return {
            "load_state": "ready",
            "active_system": doc.get("active_system"),
            "active_snapshot": active_snapshot_id,
            "snapshot_status": active_snapshot.get("status") if active_snapshot else None,
            "recovery_health": "SAFE" if safe else "REQUIRED",
            "recovery_label": "AMAN" if safe else "BELUM AMAN",
            "recovery_message": f"Snapshot {active_snapshot_id} sudah memiliki backup terverifikasi." if safe else f"Snapshot {active_snapshot_id} belum memenuhi seluruh syarat recovery.",
            "checklist": checklist,
            "latest_backup": active_backup,
            "history": history,
            "actions": actions,
            "diagnostics": [],
        }
