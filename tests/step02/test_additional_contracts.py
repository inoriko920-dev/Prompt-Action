from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import pytest

from prompt_action.data.migrations import migrate_repository
from prompt_action.data.repository import VersionRepository
from prompt_action.domain.errors import ReleasePlanError, ValidationBlockedError
from prompt_action.services.version_engine import VersionEngine
from conftest import add_release, write_candidate


def test_commit_release_creates_backup_required(project_factory):
    root=project_factory(); rel=write_candidate(root,"P3","R2","new prompt 3 bytes\n")
    repo=VersionRepository(root); engine=VersionEngine(repo)
    plan=engine.plan_release({"primary":{"prompt_id":"P3","file":rel},"sync":[]})
    result=engine.commit_release(plan); doc=repo.load().document
    assert result.app_data_revision==2 and doc["active_snapshot"]=="S002"
    assert doc["snapshots"][-1]["status"]=="BACKUP_REQUIRED" and doc["snapshots"][-1]["backup_id"] is None
    assert doc["app_version"]=="0.1.0-dev" and doc["active_system"]=="V1"


def test_new_snapshot_cannot_start_complete(project_factory, baseline):
    root=project_factory(); repo=VersionRepository(root); doc=add_release(baseline,status="COMPLETE")
    # Add a valid backup so domain validation is otherwise capable of accepting COMPLETE.
    doc["snapshots"][-1]["backup_id"]="BKP-V1-S002"
    doc["backups"].append({"id":"BKP-V1-S002","status":"VALID","verified":True,"second_copy_verified":True})
    doc["app_data_revision"]=2
    with pytest.raises(ValidationBlockedError): repo.save(doc,expected_revision=1)


def test_migration_operation_creates_metadata_backup_and_preserves_prompt_bytes(project_factory, project_root):
    source=json.loads((project_root/"data/fixtures/schema0-migration-source.json").read_text(encoding="utf-8"))
    root=project_factory(source); prompt=root/"external-prompt-proof.txt"; prompt.write_bytes(b"DO NOT TOUCH\r\n")
    before=prompt.read_bytes(); repo=VersionRepository(root)
    applied=migrate_repository(repo,1)
    assert applied.saved_revision==1 and applied.backup_path
    assert (root/applied.backup_path).is_file() and prompt.read_bytes()==before


def test_plan_release_rejects_unavailable_nonbaseline_active_source(project_factory, baseline):
    doc=add_release(baseline,"P3",file_available=False); root=project_factory(doc)
    engine=VersionEngine(VersionRepository(root))
    with pytest.raises(ReleasePlanError, match="not materialized"):
        engine.plan_release({"primary":"P3","sync":[]})
