from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from prompt_action.data.fixtures import build_corruption_fixture, is_corruption_descriptor


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def baseline(project_root: Path) -> dict:
    return json.loads((project_root / "data/version_history.json").read_text(encoding="utf-8"))


@pytest.fixture
def project_factory(tmp_path: Path, baseline: dict):
    def make(document: dict | None = None, name: str = "project") -> Path:
        root = tmp_path / name
        (root / "data").mkdir(parents=True)
        (root / "data/version_history.json").write_text(
            json.dumps(document or baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (root / "data/fixtures").mkdir(parents=True, exist_ok=True)
        (root / "data/fixtures/hash-target.txt").write_text("fixture-bytes\n", encoding="utf-8")
        return root
    return make


@pytest.fixture
def load_fixture(project_root: Path, baseline: dict):
    def load(name: str) -> dict:
        value=json.loads((project_root / "data/fixtures" / name).read_text(encoding="utf-8"))
        if is_corruption_descriptor(value):
            return build_corruption_fixture(value, baseline)
        return value
    return load


def add_release(document: dict, primary: str = "P3", *, status: str = "BACKUP_REQUIRED", file_available: bool = False) -> dict:
    doc=deepcopy(document)
    parent=doc["active_snapshot"]
    parent_snapshot=next(x for x in doc["snapshots"] if x["id"]==parent)
    system=doc["active_system"]
    snapshot_id="S002"
    prompt=doc["prompts"][primary]
    old=prompt["active_revision"]
    new="R2"
    prompt["revisions"][old]["status"]="SUPERSEDED"
    prompt["revisions"][new]={
        "parent":old,"snapshot":snapshot_id,"status":"ACTIVE","file":None,
        "sha256":hashlib.sha256(f"{primary}-{new}".encode()).hexdigest(),
        "file_available":file_available,"change_role":"PRIMARY","summary":["test"],"reason":"test",
    }
    prompt["active_revision"]=new
    prompt_state=deepcopy(parent_snapshot["prompt_state"]); prompt_state[primary]=new
    child={
        "id":snapshot_id,"system":system,"parent_snapshot":parent,"status":status,
        "primary_change":{"prompt_id":primary,"from":old,"to":new},"sync_changes":[],
        "prompt_state":prompt_state,"backup_id":None,
    }
    doc["snapshots"].append(child); doc["active_snapshot"]=snapshot_id
    next(x for x in doc["systems"] if x["id"]==system)["latest_snapshot"]=snapshot_id
    return doc


def write_candidate(root: Path, prompt_id: str, revision: str, content: str) -> str:
    label={"P1A":"Prompt-1A","P1B":"Prompt-1B","P1B1":"Prompt-1B1","P1B2":"Prompt-1B2","P2":"Prompt-2","P3":"Prompt-3","P4":"Prompt-4","P5":"Prompt-5"}[prompt_id]
    rel=f"prompts/V1/{label}/{label}_V1_{revision}.txt"
    path=root/rel; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(content,encoding="utf-8")
    return rel
