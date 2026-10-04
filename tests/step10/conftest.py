from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def project(tmp_path: Path, repo_root: Path) -> Path:
    root = tmp_path / "project"
    (root / "data").mkdir(parents=True)
    shutil.copy2(repo_root / "data/version_history.json", root / "data/version_history.json")
    shutil.copytree(repo_root / "prompts", root / "prompts")
    return root


@pytest.fixture
def canonical(project: Path) -> dict:
    return json.loads((project / "data/version_history.json").read_text(encoding="utf-8"))


@pytest.fixture
def changed_p3(project: Path, canonical: dict) -> Path:
    active = canonical["prompts"]["P3"]["active_revision"]
    rel = canonical["prompts"]["P3"]["revisions"][active]["file"]
    raw = (project / rel).read_bytes()
    path = project / "incoming/P3-next.txt"
    path.parent.mkdir(parents=True)
    path.write_bytes(raw + b"\n# STEP 10 candidate\n")
    return path


@pytest.fixture
def changed_p4(project: Path, canonical: dict) -> Path:
    active = canonical["prompts"]["P4"]["active_revision"]
    rel = canonical["prompts"]["P4"]["revisions"][active]["file"]
    raw = (project / rel).read_bytes()
    path = project / "incoming/P4-next.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw + b"\n# STEP 10 sync candidate\n")
    return path
