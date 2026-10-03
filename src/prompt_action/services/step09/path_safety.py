from __future__ import annotations

from pathlib import Path, PurePath
import re
import tempfile

from .errors import PathSafetyError

_WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
_ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class FilenamePolicy:
    @staticmethod
    def sanitize(name: str, *, max_length: int = 180) -> str:
        candidate = _ILLEGAL.sub("_", str(name)).strip().rstrip(". ")
        if not candidate:
            raise PathSafetyError("PATH_INVALID_NAME", "Nama file tujuan tidak valid.")
        path = Path(candidate)
        stem = path.stem
        suffix = path.suffix
        if stem.upper() in _WINDOWS_RESERVED:
            stem = f"_{stem}"
        allowed_stem = max(1, max_length - len(suffix))
        stem = stem[:allowed_stem]
        result = f"{stem}{suffix}"
        if not result:
            raise PathSafetyError("PATH_INVALID_NAME", "Nama file tujuan tidak valid.")
        return result

    @staticmethod
    def keep_both(destination: Path) -> Path:
        if not destination.exists():
            return destination
        stem, suffix = destination.stem, destination.suffix
        for index in range(2, 10000):
            candidate = destination.with_name(f"{stem} ({index}){suffix}")
            if not candidate.exists():
                return candidate
        raise PathSafetyError("PATH_COLLISION_LIMIT", "Terlalu banyak file dengan nama yang sama.")


class PathSafetyPolicy:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()

    @staticmethod
    def _reject_raw_escape(value: str) -> None:
        raw = str(value).replace("\\", "/")
        pure = PurePath(raw)
        if Path(raw).is_absolute() or re.match(r"^[A-Za-z]:", raw):
            raise PathSafetyError("PATH_ABSOLUTE_SOURCE", "Source harus berasal dari stable entity, bukan absolute path UI.")
        if any(part == ".." for part in pure.parts) or raw.startswith("../") or "/../" in raw:
            raise PathSafetyError("PATH_ESCAPE", "Path source mencoba keluar dari root yang diizinkan.")

    @staticmethod
    def assert_resolved_within(root: Path, resolved: Path, *, escape_code: str = "PATH_SYMLINK_ESCAPE") -> Path:
        real_root = Path(root).resolve(strict=False)
        candidate = Path(resolved).resolve(strict=False)
        try:
            candidate.relative_to(real_root)
        except ValueError as exc:
            raise PathSafetyError(escape_code, "Resolved source berada di luar root yang diizinkan.") from exc
        return candidate

    def resolve_source(self, root: Path, relative_value: str, *, must_exist: bool = True) -> Path:
        self._reject_raw_escape(relative_value)
        real_root = Path(root).resolve()
        candidate = self.assert_resolved_within(real_root, real_root / relative_value, escape_code="PATH_ESCAPE")
        if must_exist:
            if not candidate.exists():
                raise PathSafetyError("PATH_SOURCE_MISSING", "File sumber tidak tersedia.", {"source": relative_value})
            if not candidate.is_file():
                raise PathSafetyError("PATH_NOT_REGULAR_FILE", "Source bukan regular file.")
            resolved_existing = candidate.resolve(strict=True)
            self.assert_resolved_within(real_root, resolved_existing, escape_code="PATH_SYMLINK_ESCAPE")
            candidate = resolved_existing
        return candidate

    @staticmethod
    def ensure_destination_dir(directory: Path) -> Path:
        target = Path(directory).expanduser().resolve(strict=False)
        if not target.exists() or not target.is_dir():
            raise PathSafetyError("DOWNLOAD_DEST_UNWRITABLE", "Folder tujuan tidak tersedia. Pilih folder lain.")
        try:
            with tempfile.NamedTemporaryFile(prefix=".prompt-action-write-probe-", dir=target, delete=True) as handle:
                handle.write(b"ok")
                handle.flush()
        except OSError as exc:
            raise PathSafetyError("DOWNLOAD_DEST_UNWRITABLE", "Folder tujuan tidak dapat ditulis. Pilih folder lain.") from exc
        return target

    @staticmethod
    def validate_final_path(path: Path, *, max_length: int = 245) -> None:
        if len(str(path)) > max_length:
            raise PathSafetyError("PATH_TOO_LONG", "Path tujuan terlalu panjang. Pilih folder atau nama yang lebih pendek.")

    @staticmethod
    def safe_open_folder_target(path: Path) -> Path:
        target = Path(path).resolve(strict=False)
        folder = target if target.is_dir() else target.parent
        if not folder.exists() or not folder.is_dir():
            raise PathSafetyError("PATH_FOLDER_MISSING", "Folder tidak tersedia.")
        return folder
