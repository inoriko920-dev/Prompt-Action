from __future__ import annotations

from copy import deepcopy
import difflib
import hashlib
from pathlib import Path
from typing import Any

from prompt_action.data.repository import VersionRepository

from .errors import CompareError, PathSafetyError
from .models import RevisionCompareResult, SnapshotCompareResult
from .path_safety import PathSafetyPolicy


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sync_prompt_id(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return str(item.get("prompt_id") or item.get("id") or "")
    return ""


class _CanonicalReader:
    def __init__(self, project_root: Path, document: dict[str, Any] | None = None):
        self.project_root = Path(project_root).resolve()
        self._document_override = deepcopy(document) if document is not None else None

    def document(self) -> dict[str, Any]:
        if self._document_override is not None:
            return deepcopy(self._document_override)
        repository = VersionRepository(self.project_root)
        state = repository.load()
        report = repository.validate(state)
        if not report.is_valid:
            raise CompareError("COMPARE_CANONICAL_INVALID", "Canonical data tidak valid; compare diblokir.")
        return deepcopy(state.document)


class RevisionCompareService(_CanonicalReader):
    def __init__(self, project_root: Path, *, document: dict[str, Any] | None = None):
        super().__init__(project_root, document)
        self.path_policy = PathSafetyPolicy(self.project_root)

    def _record(self, document: dict[str, Any], prompt_id: str, revision_id: str) -> dict[str, Any]:
        prompts = document.get("prompts", {})
        prompt = prompts.get(prompt_id) if isinstance(prompts, dict) else None
        if not isinstance(prompt, dict):
            raise CompareError("COMPARE_PROMPT_UNKNOWN", f"Prompt {prompt_id} tidak ditemukan.")
        revisions = prompt.get("revisions", {})
        record = revisions.get(revision_id) if isinstance(revisions, dict) else None
        if not isinstance(record, dict):
            raise CompareError("COMPARE_REVISION_UNKNOWN", f"Revision {revision_id} tidak ditemukan untuk {prompt_id}.")
        return record

    def _verified_text(self, record: dict[str, Any], prompt_id: str, revision_id: str) -> tuple[Path, str, str]:
        file_value = record.get("file")
        if record.get("file_available") is not True or not isinstance(file_value, str) or not file_value.strip():
            raise CompareError("COMPARE_FILE_MISSING", f"File {prompt_id} {revision_id} tidak tersedia.")
        try:
            path = self.path_policy.resolve_source(self.project_root, file_value)
        except PathSafetyError as exc:
            raise CompareError("COMPARE_PATH_INVALID", exc.user_message, exc.details) from exc
        expected = record.get("sha256")
        actual = _sha256(path)
        if not isinstance(expected, str) or actual.lower() != expected.lower():
            raise CompareError("COMPARE_HASH_MISMATCH", f"Integritas file {prompt_id} {revision_id} tidak cocok.", {"expected": expected, "actual": actual})
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise CompareError("COMPARE_NOT_TEXT", "File revision bukan teks UTF-8 yang dapat dibandingkan.") from exc
        return path, text, actual

    def compare(self, prompt_id: str, left_revision_id: str, right_revision_id: str) -> RevisionCompareResult:
        return self.compare_refs(prompt_id, left_revision_id, prompt_id, right_revision_id)

    def compare_refs(self, left_prompt_id: str, left_revision_id: str, right_prompt_id: str, right_revision_id: str) -> RevisionCompareResult:
        if left_prompt_id != right_prompt_id:
            raise CompareError("COMPARE_CROSS_PROMPT", "Compare Revision hanya boleh untuk Prompt yang sama.")
        document = self.document()
        left_record = self._record(document, left_prompt_id, left_revision_id)
        right_record = self._record(document, right_prompt_id, right_revision_id)
        _, left_text, left_sha = self._verified_text(left_record, left_prompt_id, left_revision_id)
        _, right_text, right_sha = self._verified_text(right_record, right_prompt_id, right_revision_id)

        eol_only = left_text != right_text and left_text.splitlines() == right_text.splitlines()
        left_lines = left_text.splitlines()
        right_lines = right_text.splitlines()
        whitespace_only = False
        if not eol_only and left_text != right_text:
            normalize = lambda lines: [" ".join(line.split()) for line in lines]
            whitespace_only = normalize(left_lines) == normalize(right_lines)

        diff_lines = list(difflib.unified_diff(
            left_lines,
            right_lines,
            fromfile=f"{left_prompt_id}-{left_revision_id}",
            tofile=f"{right_prompt_id}-{right_revision_id}",
            lineterm="",
        ))
        changed = sum(1 for line in diff_lines if (line.startswith("+") or line.startswith("-")) and not line.startswith("+++") and not line.startswith("---"))
        if eol_only:
            diff_text = "[EOL-ONLY CHANGE] Line endings berbeda; isi baris sama."
        elif whitespace_only and not diff_lines:
            diff_text = "[WHITESPACE-ONLY CHANGE]"
        else:
            diff_text = "\n".join(diff_lines)
        return RevisionCompareResult(
            status="SAME" if left_text == right_text else "OK",
            prompt_id=left_prompt_id,
            left_revision=left_revision_id,
            right_revision=right_revision_id,
            left_sha256=left_sha,
            right_sha256=right_sha,
            unified_diff=diff_text,
            changed_lines=changed,
            whitespace_only=whitespace_only,
            eol_only=eol_only,
            metadata={
                "left_snapshot": left_record.get("snapshot"),
                "right_snapshot": right_record.get("snapshot"),
                "left_role": left_record.get("change_role"),
                "right_role": right_record.get("change_role"),
                "left_summary": deepcopy(left_record.get("summary", [])),
                "right_summary": deepcopy(right_record.get("summary", [])),
            },
        )


class SnapshotCompareService(_CanonicalReader):
    @staticmethod
    def _snapshot(document: dict[str, Any], snapshot_id: str) -> dict[str, Any]:
        item = next((x for x in document.get("snapshots", []) if isinstance(x, dict) and x.get("id") == snapshot_id), None)
        if item is None:
            raise CompareError("COMPARE_SNAPSHOT_UNKNOWN", f"Snapshot {snapshot_id} tidak ditemukan.")
        return item

    @staticmethod
    def _backup(document: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any] | None:
        backup_id = snapshot.get("backup_id")
        if not backup_id:
            return None
        return deepcopy(next((x for x in document.get("backups", []) if isinstance(x, dict) and (x.get("id") == backup_id or x.get("backup_id") == backup_id)), None))

    def compare(self, left_snapshot_id: str, right_snapshot_id: str) -> SnapshotCompareResult:
        document = self.document()
        left = self._snapshot(document, left_snapshot_id)
        right = self._snapshot(document, right_snapshot_id)
        left_state = left.get("prompt_state", {}) if isinstance(left.get("prompt_state"), dict) else {}
        right_state = right.get("prompt_state", {}) if isinstance(right.get("prompt_state"), dict) else {}
        primary = right.get("primary_change") if isinstance(right.get("primary_change"), dict) else None
        primary_id = str(primary.get("prompt_id") or "") if primary else ""
        sync_ids = {_sync_prompt_id(x) for x in right.get("sync_changes", []) if _sync_prompt_id(x)}

        changed: list[dict[str, Any]] = []
        unchanged_count = 0
        for prompt_id in sorted(set(left_state) | set(right_state)):
            before = left_state.get(prompt_id)
            after = right_state.get(prompt_id)
            if before == after:
                unchanged_count += 1
                continue
            role = "PRIMARY" if prompt_id == primary_id else "SYNC" if prompt_id in sync_ids else "CHANGE"
            changed.append({"prompt_id": prompt_id, "from": before, "to": after, "role": role})

        primary_delta = next((dict(item) for item in changed if item["role"] == "PRIMARY"), None)
        sync_deltas = tuple(dict(item) for item in changed if item["role"] == "SYNC")
        left_system = str(left.get("system") or "")
        right_system = str(right.get("system") or "")
        cross = left_system != right_system
        if left_snapshot_id == right_snapshot_id:
            summary = f"{left_snapshot_id} dibandingkan dengan dirinya sendiri; tidak ada perubahan."
            status = "SAME"
        else:
            summary = f"{len(changed)} Prompt berubah, {unchanged_count} tetap."
            status = "OK"
        return SnapshotCompareResult(
            status=status,
            left_snapshot=left_snapshot_id,
            right_snapshot=right_snapshot_id,
            left_system=left_system,
            right_system=right_system,
            cross_system_warning=cross,
            changed=tuple(changed),
            unchanged_count=unchanged_count,
            primary_delta=primary_delta,
            sync_deltas=sync_deltas,
            backup_delta={"left": self._backup(document, left), "right": self._backup(document, right)},
            summary=summary,
        )
