from __future__ import annotations

from pathlib import Path

import pytest

from prompt_action.bootstrap.app_paths import (
    AppPaths,
    RuntimeDirectoryError,
    discover_project_root,
    ensure_runtime_directories,
    resolve_app_paths,
)


def _fake_repo(tmp_path: Path, name: str = "Prompt Action Ω") -> Path:
    root = tmp_path / name
    (root / "src" / "prompt_action" / "ui" / "qml").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    return root


def test_t06_root_resolution_ignores_cwd(tmp_path, monkeypatch):
    root = _fake_repo(tmp_path)
    nested = root / "src" / "prompt_action"
    elsewhere = tmp_path / "unrelated cwd"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert discover_project_root(nested) == root.resolve()


def test_t07_t08_spaces_and_unicode_path(tmp_path):
    root = _fake_repo(tmp_path, "Folder With Spaces — Bojonegoro")
    assert discover_project_root(root / "src") == root.resolve()


def test_t10_runtime_directories_are_created(tmp_path, monkeypatch):
    root = _fake_repo(tmp_path)
    monkeypatch.setenv("PROMPT_ACTION_PROJECT_ROOT", str(root))
    paths = resolve_app_paths()
    ensure_runtime_directories(paths)
    assert paths.log_dir.is_dir()
    assert paths.temp_dir.is_dir()


def test_t11_read_only_runtime_simulation(tmp_path):
    root = _fake_repo(tmp_path)
    paths = AppPaths(
        project_root=root,
        resource_root=root / "src" / "prompt_action" / "ui",
        runtime_root=root / "runtime",
        log_dir=root / "runtime" / "logs",
        temp_dir=root / "runtime" / "temp",
        docs_root=root / "docs",
    )

    def deny(_directory: Path) -> None:
        raise PermissionError("simulated read-only runtime")

    with pytest.raises(RuntimeDirectoryError, match="not writable"):
        ensure_runtime_directories(paths, write_probe=deny)
