from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

pytest.importorskip("PySide6")

from prompt_action.bootstrap.app_paths import resolve_app_paths
from prompt_action.bootstrap.qml_boot import create_application, load_qml
from prompt_action.main import run


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _env_for(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    env["QT_QPA_PLATFORM"] = "offscreen"
    return env


def test_t03_t04_qml_load_and_title(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    paths = resolve_app_paths()
    app = create_application([])
    engine = load_qml(paths.resource_root / "qml" / "App.qml")
    assert engine.rootObjects()
    assert engine.rootObjects()[0].property("title") == "Prompt Action"
    engine.deleteLater()
    app.processEvents()


def test_t05_invalid_qml_returns_nonzero_and_logs(tmp_path, monkeypatch):
    monkeypatch.setenv("PROMPT_ACTION_RUNTIME_ROOT", str(tmp_path / "runtime"))
    missing = tmp_path / "missing.qml"
    code = run(["--qml", str(missing), "--smoke-test-ms", "1"])
    assert code == 21
    logs = list((tmp_path / "runtime" / "logs").glob("prompt-action-*.log"))
    assert logs
    assert "qml.file_missing" in logs[0].read_text(encoding="utf-8")


def test_t02_t13_module_entrypoint_and_repeated_start():
    root = _repo_root()
    cmd = [sys.executable, "-m", "prompt_action", "--smoke-test-ms", "50"]
    for _ in range(2):
        result = subprocess.run(cmd, cwd=root.parent, env=_env_for(root), capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr


def test_t09_t14_relocation_from_unrelated_cwd(tmp_path):
    source = _repo_root()
    relocated = tmp_path / "Relocated Prompt Action Ω"
    shutil.copytree(
        source,
        relocated,
        ignore=shutil.ignore_patterns(".venv", ".git", "__pycache__", ".pytest_cache", "logs", "temp"),
    )
    unrelated = tmp_path / "different cwd"
    unrelated.mkdir()
    runtime = relocated / "runtime"
    env = _env_for(relocated)
    env["PROMPT_ACTION_RUNTIME_ROOT"] = str(runtime)
    result = subprocess.run(
        [sys.executable, "-m", "prompt_action", "--smoke-test-ms", "50"],
        cwd=unrelated,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    logs = list((runtime / "logs").glob("prompt-action-*.log"))
    assert logs
    log_text = logs[0].read_text(encoding="utf-8")
    assert str(relocated.resolve()) in log_text
