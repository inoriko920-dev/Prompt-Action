from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import shutil
from typing import Iterator

from prompt_action.domain.errors import BackupWorkflowError


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class BackupRepository:
    def __init__(
        self,
        project_root: Path,
        *,
        primary_root: Path | None = None,
        second_root: Path | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.primary_root = (primary_root or (self.project_root / "backups")).resolve()
        self.second_root = (second_root or (self.project_root / "backups-second-copy")).resolve()
        self.lock_path = self.project_root / "backup_txn" / ".backup.lock"
        self._validate_destination_pair()

    @staticmethod
    def _is_within(child: Path, parent: Path) -> bool:
        try:
            child.resolve().relative_to(parent.resolve())
            return True
        except ValueError:
            return False

    def _validate_destination_pair(self) -> None:
        primary = self.primary_root.resolve()
        secondary = self.second_root.resolve()
        if primary == secondary:
            raise BackupWorkflowError("SECOND_COPY_ALIAS", "Primary and second-copy roots must be different")
        # A second copy nested inside the primary tree can accidentally become
        # part of a future backup or be deleted with the primary tree.
        if self._is_within(secondary, primary) or self._is_within(primary, secondary):
            raise BackupWorkflowError("SECOND_COPY_ALIAS", "Primary and second-copy roots must not contain each other")
        for root, label in ((primary, "primary"), (secondary, "second-copy")):
            if root.exists() and root.is_symlink():
                raise BackupWorkflowError("PATH_POLICY_BLOCKED", f"{label} backup root cannot be a symlink")

    @staticmethod
    def artifact_name(system: str, snapshot: str) -> str:
        return f"Prompt-Action-{system}-{snapshot}-FULL-BACKUP.zip"

    def primary_paths(self, system: str, snapshot: str) -> dict[str, Path]:
        folder = self.primary_root / system / snapshot
        name = self.artifact_name(system, snapshot)
        zip_path = folder / name
        return {
            "folder": folder,
            "zip": zip_path,
            "sha256": zip_path.with_suffix(zip_path.suffix + ".sha256"),
            "record": folder / f"Prompt-Action-{system}-{snapshot}-backup-record.json",
        }

    def secondary_paths(self, system: str, snapshot: str) -> dict[str, Path]:
        folder = self.second_root / system / snapshot
        name = self.artifact_name(system, snapshot)
        zip_path = folder / name
        return {
            "folder": folder,
            "zip": zip_path,
            "sha256": zip_path.with_suffix(zip_path.suffix + ".sha256"),
            "record": folder / f"Prompt-Action-{system}-{snapshot}-backup-record.json",
        }

    def display_path(self, path: Path) -> str:
        path = path.resolve()
        try:
            return str(path.relative_to(self.project_root)).replace("\\", "/")
        except ValueError:
            return str(path)

    def require_free_space(self, *, estimated_payload_bytes: int) -> None:
        reserve = max(4 * 1024 * 1024, estimated_payload_bytes * 4)
        for root, label in ((self.primary_root, "primary"), (self.second_root, "second-copy")):
            probe = root
            while not probe.exists() and probe.parent != probe:
                probe = probe.parent
            try:
                free = shutil.disk_usage(probe).free
            except OSError as exc:
                raise BackupWorkflowError("DESTINATION_UNAVAILABLE", f"Cannot inspect {label} destination: {exc}") from exc
            if free < reserve:
                raise BackupWorkflowError("INSUFFICIENT_SPACE", f"{label} destination needs at least {reserve} free bytes; found {free}")

    @staticmethod
    def _fsync_file(path: Path) -> None:
        with path.open("rb") as handle:
            os.fsync(handle.fileno())

    @staticmethod
    def _fsync_parent(path: Path) -> None:
        if hasattr(os, "O_DIRECTORY"):
            try:
                fd = os.open(path.parent, os.O_DIRECTORY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            except OSError:
                pass

    def promote_new(self, partial: Path, final: Path) -> None:
        if final.exists():
            raise BackupWorkflowError("BACKUP_TARGET_EXISTS", f"Refusing silent overwrite: {final}")
        final.parent.mkdir(parents=True, exist_ok=True)
        self._fsync_file(partial)
        os.replace(partial, final)
        self._fsync_parent(final)

    def write_sidecar(self, path: Path, digest: str, artifact_name: str, txn_id: str) -> Path:
        final = path
        if final.exists():
            raise BackupWorkflowError("BACKUP_TARGET_EXISTS", f"Refusing silent overwrite: {final}")
        final.parent.mkdir(parents=True, exist_ok=True)
        partial = final.with_name(final.name + f".partial-{txn_id}")
        payload = f"{digest}  {artifact_name}\n".encode("utf-8")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        fd = os.open(partial, flags, 0o644)
        try:
            view = memoryview(payload)
            while view:
                written = os.write(fd, view)
                view = view[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
        self.promote_new(partial, final)
        return final

    def copy_secondary(self, source: Path, target: Path, *, txn_id: str) -> str:
        if target.exists():
            raise BackupWorkflowError("BACKUP_TARGET_EXISTS", f"Refusing silent overwrite: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.name + f".partial-{txn_id}")
        if partial.exists():
            partial.unlink()
        source_digest = hashlib.sha256()
        with source.open("rb") as reader, partial.open("xb") as writer:
            for chunk in iter(lambda: reader.read(1024 * 1024), b""):
                source_digest.update(chunk)
                writer.write(chunk)
            writer.flush()
            os.fsync(writer.fileno())
        self.promote_new(partial, target)
        # Independent destination read; never trust the streaming source hash as
        # proof that the second copy reached storage intact.
        destination_digest = sha256_path(target)
        if destination_digest != source_digest.hexdigest():
            raise BackupWorkflowError("SECOND_COPY_HASH_MISMATCH", "Second-copy SHA-256 differs from source bytes")
        return destination_digest

    def remove_owned_partial(self, path: Path) -> None:
        try:
            if path.is_file():
                path.unlink()
        except OSError as exc:
            raise BackupWorkflowError("BACKUP_RECOVERY_REQUIRED", f"Cannot remove partial artifact: {path}: {exc}") from exc

    @contextmanager
    def exclusive_lock(self, txn_id: str) -> Iterator[None]:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        try:
            fd = os.open(self.lock_path, flags, 0o644)
        except FileExistsError as exc:
            raise BackupWorkflowError("BACKUP_BUSY", "Another backup transaction holds the exclusive lock") from exc
        try:
            os.write(fd, (txn_id + "\n").encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)
        try:
            yield
        finally:
            try:
                if self.lock_path.read_text(encoding="utf-8").strip() == txn_id:
                    self.lock_path.unlink(missing_ok=True)
            except OSError:
                pass

    def clear_stale_lock(self, expected_txn_id: str | None = None) -> bool:
        if not self.lock_path.exists():
            return False
        if expected_txn_id is not None:
            try:
                owner = self.lock_path.read_text(encoding="utf-8").strip()
            except OSError as exc:
                raise BackupWorkflowError("BACKUP_RECOVERY_REQUIRED", f"Cannot inspect backup lock: {exc}") from exc
            if owner != expected_txn_id:
                raise BackupWorkflowError("BACKUP_BUSY", "Backup lock belongs to another transaction")
        self.lock_path.unlink(missing_ok=True)
        return True
