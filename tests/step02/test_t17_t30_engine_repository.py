from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from prompt_action.data.migrations import migrate_document
from prompt_action.data.repository import VersionRepository
from prompt_action.domain.errors import RevisionConflictError
from prompt_action.domain.ids import next_revision_id, next_snapshot_id
from prompt_action.domain.validation import VersionValidator
from prompt_action.services.version_engine import VersionEngine
from conftest import write_candidate


def test_t17_deterministic_p3_release_plan(project_factory):
    root=project_factory(); engine=VersionEngine(VersionRepository(root))
    a=engine.plan_release({"primary":"P3","sync":["P1B2","P4"]}).to_dict()
    b=engine.plan_release({"primary":"P3","sync":["P1B2","P4"]}).to_dict()
    assert a==b and a["snapshot_id"]=="S002" and a["primary"]["to"]=="R2"


def test_t18_independent_p2_release_plan(project_factory):
    root=project_factory(); plan=VersionEngine(VersionRepository(root)).plan_release({"primary":"P2","sync":[]})
    assert plan.primary.prompt_id=="P2" and plan.primary.to_revision=="R2" and plan.system=="V1"


def test_t19_deterministic_next_snapshot_id():
    assert next_snapshot_id(["S001","S003","S002"])=="S004"


def test_t20_revision_next_id_scoped_per_prompt():
    assert next_revision_id(["R1","R3","R2"])=="R4" and next_revision_id(["R1"])=="R2"


def test_t21_atomic_save_success(project_factory, baseline):
    root=project_factory(); repo=VersionRepository(root); doc=deepcopy(baseline)
    doc["app_data_revision"]=2; result=repo.save(doc,expected_revision=1)
    assert result.app_data_revision==2 and repo.load().app_data_revision==2


def test_t22_simulated_save_failure_preserves_old_canonical(project_factory, baseline):
    root=project_factory(); path=root/"data/version_history.json"; before=path.read_bytes(); before_sha=hashlib.sha256(before).hexdigest()
    def fail_replace(src,dst): raise OSError("simulated atomic replace failure")
    repo=VersionRepository(root,replace_func=fail_replace); doc=deepcopy(baseline); doc["app_data_revision"]=2
    with pytest.raises(OSError): repo.save(doc,expected_revision=1)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before_sha and path.read_bytes()==before


def test_t23_expected_revision_conflict_rejected(project_factory, baseline):
    root=project_factory(); repo=VersionRepository(root); doc=deepcopy(baseline); doc["app_data_revision"]=2
    with pytest.raises(RevisionConflictError): repo.save(doc,expected_revision=0)


def test_t24_reload_round_trip_semantic_equality(project_factory, baseline):
    root=project_factory(); repo=VersionRepository(root)
    assert repo.load().document==repo.reload().document==baseline


def test_t25_schema_migration_fixture_valid(project_root):
    source=json.loads((project_root/"data/fixtures/schema0-migration-source.json").read_text(encoding="utf-8"))
    result=migrate_document(source,1)
    assert result.to_schema_version==1 and VersionValidator(project_root).validate(result.document).is_valid


def test_t26_migration_does_not_modify_prompt_bytes(project_root, tmp_path):
    source=json.loads((project_root/"data/fixtures/schema0-migration-source.json").read_text(encoding="utf-8"))
    p=tmp_path/"prompt.txt"; p.write_bytes(b"EXACT\r\nBYTES\n"); before=p.read_bytes()
    migrate_document(source,1)
    assert p.read_bytes()==before


def test_t27_relative_paths_survive_relocation(project_factory, baseline):
    root=project_factory(name="Relocated Project Ω")
    rel=write_candidate(root,"P3","R1","materialized baseline candidate")
    doc=deepcopy(baseline); rev=doc["prompts"]["P3"]["revisions"]["R1"]
    rev["file"]=rel; rev["file_available"]=True; rev["sha256"]=hashlib.sha256((root/rel).read_bytes()).hexdigest()
    (root/"data/version_history.json").write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")
    assert VersionRepository(root).validate(VersionRepository(root).load()).is_valid


def test_t28_complete_without_valid_backup_rejected(project_root, load_fixture):
    report=VersionValidator(project_root).validate(load_fixture("complete-without-backup.json"))
    assert not report.is_valid and any(x.code=="INV-11" for x in report.issues)


def test_t29_app_version_independent_from_system_v_s_r(project_factory):
    root=project_factory(); engine=VersionEngine(VersionRepository(root)); plan=engine.plan_release({"primary":"P3","sync":[]})
    assert plan.app_version=="0.1.0-dev" and plan.system=="V1" and plan.snapshot_id=="S002" and plan.primary.to_revision=="R2"


def test_t30_cli_validator_nonzero_on_blocking_issue(project_root):
    env=os.environ.copy(); env["PYTHONPATH"]=str(project_root/"src")
    proc=subprocess.run([sys.executable,"-m","prompt_action.data","--root",str(project_root),"validate","--file",Path("data/fixtures/missing-parent-snapshot.json")],cwd=project_root,env=env,capture_output=True,text=True)
    assert proc.returncode!=0 and '"valid": false' in proc.stdout.lower()
