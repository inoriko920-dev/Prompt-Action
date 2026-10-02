from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tempfile
from typing import Callable


PROJECT_MARKER = "pyproject.toml"
ROOT_OVERRIDE_ENV = "PROMPT_ACTION_PROJECT_ROOT"
RUNTIME_OVERRIDE_ENV = "PROMPT_ACTION_RUNTIME_ROOT"


class ProjectRootNotFoundError(RuntimeError):
    pass


class RuntimeDirectoryError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AppPaths:
    project_root: Path
    resource_root: Path
    runtime_root: Path
    log_dir: Path
    temp_dir: Path
    docs_root: Path


def discover_project_root(start: Path | None = None) -> Path:
    override = os.environ.get(ROOT_OVERRIDE_ENV)
    if override:
        candidate = Path(override).expanduser().resolve()
        if (candidate / PROJECT_MARKER).is_file():
            return candidate
        raise ProjectRootNotFoundError(
            f"{ROOT_OVERRIDE_ENV} points to a directory without {PROJECT_MARKER}: {candidate}"
        )

    anchor = (start or Path(__file__)).resolve()
    if anchor.is_file():
        anchor = anchor.parent

    for candidate in (anchor, *anchor.parents):
        if (candidate / PROJECT_MARKER).is_file():
            return candidate

    raise ProjectRootNotFoundError(
        f"Could not find project root marker {PROJECT_MARKER!r} from {anchor}"
    )


def resolve_app_paths(start: Path | None = None) -> AppPaths:
    project_root = discover_project_root(start)
    runtime_override = os.environ.get(RUNTIME_OVERRIDE_ENV)
    runtime_root = (
        Path(runtime_override).expanduser().resolve()
        if runtime_override
        else project_root / "runtime"
    )
    return AppPaths(
        project_root=project_root,
        resource_root=project_root / "src" / "prompt_action" / "ui",
        runtime_root=runtime_root,
        log_dir=runtime_root / "logs",
        temp_dir=runtime_root / "temp",
        docs_root=project_root / "docs",
    )


def _default_write_probe(directory: Path) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", prefix=".prompt-action-write-probe-", dir=directory, delete=True
    ) as handle:
        handle.write("ok")
        handle.flush()


def ensure_runtime_directories(
    paths: AppPaths,
    *,
    write_probe: Callable[[Path], None] = _default_write_probe,
) -> None:
    try:
        paths.runtime_root.mkdir(parents=True, exist_ok=True)
        paths.log_dir.mkdir(parents=True, exist_ok=True)
        paths.temp_dir.mkdir(parents=True, exist_ok=True)
        write_probe(paths.log_dir)
        write_probe(paths.temp_dir)
    except OSError as exc:
        raise RuntimeDirectoryError(
            f"Runtime directory is not writable: {paths.runtime_root}: {exc}"
        ) from exc
