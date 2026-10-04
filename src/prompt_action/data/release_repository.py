from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import shutil
from typing import Iterator

from prompt_action.domain.errors import ReleaseWorkflowError


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ReleaseRepository:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.lock_path = self.project_root / "release_txn" / ".release.lock"
        self.canonical_path = self.project_root / "data/version_history.json"

    def canonical_sha256(self) -> str:
        return sha256_path(self.canonical_path)

    def safe_project_path(self, relative: str) -> Path:
        if not isinstance(relative, str) or not relative or "\x00" in relative:
            raise ReleaseWorkflowError("PATH_POLICY_BLOCKED", "Invalid project-relative path")
        path = (self.project_root / relative).resolve()
        try:
            path.relative_to(self.project_root)
        except ValueError as exc:
            raise ReleaseWorkflowError("PATH_POLICY_BLOCKED", f"Path escapes project root: {relative}") from exc
        return path

    @staticmethod
    def prompt_label(display_name: str) -> str:
        label = display_name.strip().replace(" ", "-")
        if not label or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in label):
            raise ReleaseWorkflowError("PATH_POLICY_BLOCKED", f"Unsafe prompt display name: {display_name!r}")
        return label

    def target_revision_path(self, *, system: str, display_name: str, revision: str) -> tuple[str, Path]:
        label = self.prompt_label(display_name)
        relative = f"prompts/{system}/{label}/{label}_{system}_{revision}.txt"
        return relative, self.safe_project_path(relative)

    def require_free_space(self, required_bytes: int) -> None:
        free = shutil.disk_usage(self.project_root).free
        reserve = max(1024 * 1024, required_bytes * 3)
        if free < reserve:
            raise ReleaseWorkflowError("INSUFFICIENT_SPACE", f"Need at least {reserve} free bytes, only {free} available")

    def place_new_file(self, target: Path, payload: bytes, expected_sha256: str) -> None:
        target = target.resolve()
        try:
            target.relative_to(self.project_root)
        except ValueError as exc:
            raise ReleaseWorkflowError("PATH_POLICY_BLOCKED", "Revision target escapes project root") from exc
        if target.exists():
            raise ReleaseWorkflowError("REVISION_TARGET_EXISTS", f"Revision target already exists: {target}")
        if sha256_bytes(payload) != expected_sha256:
            raise ReleaseWorkflowError("HASH_MISMATCH", "Staged bytes do not match release plan")
        target.parent.mkdir(parents=True, exist_ok=True)
        # O_BINARY is required on Windows. Without it, CRT text translation can
        # turn LF bytes into CRLF during os.write(), violating byte-exact release
        # semantics even though the in-memory payload hash is correct.
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        fd = os.open(target, flags, 0o644)
        try:
            view = memoryview(payload)
            while view:
                written = os.write(fd, view)
                view = view[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
        if sha256_path(target) != expected_sha256:
            try:
                target.unlink(missing_ok=True)
            finally:
                raise ReleaseWorkflowError("HASH_MISMATCH", f"Placed revision failed hash verification: {target}")

    def remove_if_exact(self, target: Path, expected_sha256: str) -> bool:
        if not target.is_file():
            return False
        if sha256_path(target) != expected_sha256:
            raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Cannot roll back changed file: {target}")
        target.unlink()
        return True

    @contextmanager
    def exclusive_lock(self, txn_id: str) -> Iterator[None]:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError as exc:
            raise ReleaseWorkflowError("RELEASE_BUSY", "Another release transaction holds the exclusive lock") from exc
        try:
            os.write(fd, (txn_id + "\n").encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)
        try:
            yield
        finally:
            try:
                current = self.lock_path.read_text(encoding="utf-8").strip()
                if current == txn_id:
                    self.lock_path.unlink(missing_ok=True)
            except OSError:
                pass

    def clear_stale_lock(self, expected_txn_id: str | None = None) -> bool:
        if not self.lock_path.exists():
            return False
        if expected_txn_id is not None:
            try:
                if self.lock_path.read_text(encoding="utf-8").strip() != expected_txn_id:
                    raise ReleaseWorkflowError("RELEASE_BUSY", "Release lock belongs to another transaction")
            except OSError as exc:
                raise ReleaseWorkflowError("RECOVERY_REQUIRED", f"Cannot inspect release lock: {exc}") from exc
        self.lock_path.unlink(missing_ok=True)
        return True
