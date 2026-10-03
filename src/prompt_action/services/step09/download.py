from __future__ import annotations

"""Read-only export service for verified Prompt Action artifacts.

Sources are resolved only from canonical stable IDs and are restricted to the
Prompt Action project roots (prompts, backups, docs). Arbitrary source paths
from UI input are never accepted.
"""

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import uuid
from typing import Any, Callable

from prompt_action.data.repository import VersionRepository

from .errors import DownloadError, PathSafetyError
from .models import CancelToken, DownloadPlan, DownloadResult
from .path_safety import FilenamePolicy, PathSafetyPolicy


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


class DownloadService:
    def __init__(self, project_root: Path, *, document: dict[str, Any] | None = None, allowed_roots: tuple[Path, ...] | None = None, chunk_size: int = 1024 * 1024):
        self.project_root = Path(project_root).resolve()
        self._document_override = deepcopy(document) if document is not None else None
        self.path_policy = PathSafetyPolicy(self.project_root)
        roots = allowed_roots or (self.project_root / "prompts", self.project_root / "backups", self.project_root / "docs")
        self.allowed_roots = tuple(Path(root).resolve(strict=False) for root in roots)
        self.chunk_size = max(4096, int(chunk_size))

    def _document(self) -> dict[str, Any]:
        if self._document_override is not None:
            return deepcopy(self._document_override)
        repository = VersionRepository(self.project_root)
        state = repository.load()
        report = repository.validate(state)
        if not report.is_valid:
            raise DownloadError("DOWNLOAD_CANONICAL_INVALID", "Canonical data tidak valid; download diblokir.")
        return deepcopy(state.document)

    def _ensure_allowed(self, path: Path) -> Path:
        candidate = Path(path).resolve(strict=True)
        for root in self.allowed_roots:
            if not root.exists():
                continue
            try:
                candidate.relative_to(root.resolve(strict=True))
                return candidate
            except ValueError:
                continue
        raise DownloadError("PATH_ESCAPE", "File sumber berada di luar allowed roots.")

    def _resolve_project_source(self, relative_value: str) -> Path:
        try:
            path = self.path_policy.resolve_source(self.project_root, relative_value)
        except PathSafetyError as exc:
            raise DownloadError(exc.code, exc.user_message, exc.details) from exc
        return self._ensure_allowed(path)

    @staticmethod
    def _verify_hash(path: Path, expected: str | None) -> str:
        actual = sha256_file(path)
        if expected is not None and actual.lower() != str(expected).lower():
            raise DownloadError("DOWNLOAD_HASH_MISMATCH", "Integritas file sumber tidak cocok; download diblokir.", {"expected": expected, "actual": actual})
        return actual

    @staticmethod
    def _prompt_record(document: dict[str, Any], prompt_id: str, revision_id: str | None = None) -> tuple[str, dict[str, Any]]:
        prompts = document.get("prompts", {})
        prompt = prompts.get(prompt_id) if isinstance(prompts, dict) else None
        if not isinstance(prompt, dict):
            raise DownloadError("DOWNLOAD_SOURCE_MISSING", f"Prompt {prompt_id} tidak ditemukan.")
        rid = revision_id or str(prompt.get("active_revision") or "")
        revisions = prompt.get("revisions", {})
        record = revisions.get(rid) if isinstance(revisions, dict) else None
        if not isinstance(record, dict):
            raise DownloadError("DOWNLOAD_SOURCE_MISSING", f"Revision {rid} tidak ditemukan untuk {prompt_id}.")
        return rid, record

    def prepare(self, entity_ref: dict[str, Any]) -> DownloadPlan:
        document = self._document()
        entity_type = str(entity_ref.get("type") or "").lower()
        if entity_type in {"prompt_revision", "active_prompt"}:
            prompt_id = str(entity_ref.get("prompt_id") or "")
            revision_id = None if entity_type == "active_prompt" else str(entity_ref.get("revision_id") or "")
            rid, record = self._prompt_record(document, prompt_id, revision_id)
            file_value = record.get("file")
            if record.get("file_available") is not True or not isinstance(file_value, str) or not file_value:
                raise DownloadError("DOWNLOAD_SOURCE_MISSING", f"File sumber {prompt_id} {rid} tidak tersedia.")
            source = self._resolve_project_source(file_value)
            expected = record.get("sha256")
            actual = self._verify_hash(source, expected if isinstance(expected, str) else None)
            filename = FilenamePolicy.sanitize(Path(file_value).name or f"{prompt_id}_{rid}.txt")
            return DownloadPlan(entity_type, f"{prompt_id}:{rid}", source, filename, actual)
        if entity_type in {"backup", "sha256"}:
            backup_id = str(entity_ref.get("backup_id") or "")
            record = next((x for x in document.get("backups", []) if isinstance(x, dict) and str(x.get("id") or x.get("backup_id") or "") == backup_id), None)
            if not isinstance(record, dict):
                raise DownloadError("DOWNLOAD_SOURCE_MISSING", "Artifact backup tidak tersedia.")
            field = "sha256_file" if entity_type == "sha256" else "file"
            file_value = record.get(field)
            if not isinstance(file_value, str) or not file_value:
                raise DownloadError("DOWNLOAD_SOURCE_MISSING", "Artifact yang diminta tidak tersedia.")
            source = self._resolve_project_source(file_value)
            expected = record.get("sha256") if entity_type == "backup" else record.get("sha256_file_sha256")
            actual = self._verify_hash(source, expected if isinstance(expected, str) else None)
            return DownloadPlan(entity_type, backup_id, source, FilenamePolicy.sanitize(Path(file_value).name), actual)
        if entity_type in {"changelog", "recovery_guide"}:
            stable_id = str(entity_ref.get("id") or "")
            approved = entity_ref.get("approved_file")
            if not stable_id or not isinstance(approved, str) or not approved:
                raise DownloadError("DOWNLOAD_SOURCE_MISSING", "Dokumen sumber terverifikasi tidak tersedia.")
            source = self._resolve_project_source(approved)
            expected = entity_ref.get("sha256")
            actual = self._verify_hash(source, expected if isinstance(expected, str) else None)
            return DownloadPlan(entity_type, stable_id, source, FilenamePolicy.sanitize(Path(approved).name), actual)
        raise DownloadError("DOWNLOAD_ENTITY_UNSUPPORTED", "Jenis file ini belum didukung untuk download.")

    def execute(self, plan: DownloadPlan, destination_dir: Path, *, conflict_policy: str = "cancel", cancel_token: CancelToken | None = None, replace_func: Callable[[str | os.PathLike[str], str | os.PathLike[str]], None] = os.replace, before_chunk: Callable[[int], None] | None = None) -> DownloadResult:
        try:
            destination_root = self.path_policy.ensure_destination_dir(Path(destination_dir))
        except PathSafetyError as exc:
            raise DownloadError(exc.code, exc.user_message, exc.details) from exc
        filename = FilenamePolicy.sanitize(plan.filename)
        final_path = destination_root / filename
        try:
            self.path_policy.validate_final_path(final_path)
        except PathSafetyError as exc:
            raise DownloadError(exc.code, exc.user_message, exc.details) from exc
        policy = str(conflict_policy).lower().strip()
        if final_path.exists():
            if policy == "cancel":
                return DownloadResult("CANCELLED", None, None, 0, "DOWNLOAD_DEST_EXISTS")
            if policy == "keep_both":
                final_path = FilenamePolicy.keep_both(final_path)
            elif policy != "replace":
                raise DownloadError("DOWNLOAD_CONFLICT_POLICY", "Pilihan conflict tidak dikenali.")
        source_actual = self._verify_hash(plan.source_path, plan.sha256)
        temp_path: Path | None = destination_root / f".tmp-{uuid.uuid4().hex}-{filename}"
        copied = 0
        try:
            with plan.source_path.open("rb") as source, temp_path.open("xb") as target:
                while True:
                    if cancel_token is not None and cancel_token.cancelled:
                        return DownloadResult("CANCELLED", None, None, copied, "DOWNLOAD_CANCELLED")
                    chunk = source.read(self.chunk_size)
                    if not chunk:
                        break
                    if before_chunk is not None:
                        before_chunk(copied)
                    target.write(chunk)
                    copied += len(chunk)
                target.flush()
                os.fsync(target.fileno())
            temp_hash = sha256_file(temp_path)
            if temp_hash != source_actual:
                raise DownloadError("DOWNLOAD_COPY_HASH_MISMATCH", "Hash hasil copy tidak sama dengan source.")
            replace_func(temp_path, final_path)
            temp_path = None
            if plan.verify_destination:
                final_hash = sha256_file(final_path)
                if final_hash != source_actual:
                    final_path.unlink(missing_ok=True)
                    raise DownloadError("DOWNLOAD_DEST_HASH_MISMATCH", "Verifikasi file tujuan gagal.")
            return DownloadResult("SUCCESS", final_path, source_actual, copied, "OK")
        except DownloadError:
            raise
        except OSError as exc:
            raise DownloadError("DOWNLOAD_COPY_FAILED", "Copy gagal; file partial dibersihkan.", {"exception": type(exc).__name__}) from exc
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def copy_exact(self, entity_ref: dict[str, Any], destination_dir: Path, **kwargs: Any) -> DownloadResult:
        return self.execute(self.prepare(entity_ref), destination_dir, **kwargs)
