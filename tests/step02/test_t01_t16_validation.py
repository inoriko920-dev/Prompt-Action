from __future__ import annotations

from copy import deepcopy
import json

from prompt_action.domain.validation import VersionValidator, parse_json_text
from conftest import add_release


def codes(report): return {issue.code for issue in report.issues}


def test_t01_parse_valid_canonical_json(project_root, baseline):
    text=(project_root/"data/version_history.json").read_text(encoding="utf-8")
    doc, syntax=parse_json_text(text)
    assert doc and syntax.is_valid
    assert VersionValidator(project_root).validate(doc).is_valid


def test_t02_reject_malformed_json():
    doc, report=parse_json_text('{"bad":')
    assert doc is None and not report.is_valid and "SYNTAX-JSON" in codes(report)


def test_t03_reject_schema_missing_fields(project_root, baseline):
    doc=deepcopy(baseline); del doc["active_system"]
    report=VersionValidator(project_root).validate(doc)
    assert not report.is_valid and "SCHEMA-MISSING-FIELD" in codes(report)


def test_t04_one_active_system(project_root, baseline):
    doc=deepcopy(baseline); doc["systems"].append({**deepcopy(doc["systems"][0]),"id":"V2","first_snapshot":"S001","latest_snapshot":"S001"})
    report=VersionValidator(project_root).validate(doc)
    assert not report.is_valid and "INV-01" in codes(report)


def test_t05_reject_missing_active_snapshot(project_root, baseline):
    doc=deepcopy(baseline); doc["active_snapshot"]="S999"
    report=VersionValidator(project_root).validate(doc)
    assert not report.is_valid and "INV-02" in codes(report)


def test_t06_reject_missing_snapshot_parent(project_root, load_fixture):
    report=VersionValidator(project_root).validate(load_fixture("missing-parent-snapshot.json"))
    assert not report.is_valid and "INV-03" in codes(report)


def test_t07_reject_snapshot_cycle(project_root, load_fixture):
    report=VersionValidator(project_root).validate(load_fixture("snapshot-cycle.json"))
    assert not report.is_valid and "GRAPH-SNAPSHOT-CYCLE" in codes(report)


def test_t08_reject_revision_cycle(project_root, load_fixture):
    report=VersionValidator(project_root).validate(load_fixture("revision-cycle.json"))
    assert not report.is_valid and ("GRAPH-REVISION-CYCLE" in codes(report) or "INV-05" in codes(report))


def test_t09_reject_active_revision_mismatch(project_root, baseline):
    doc=deepcopy(baseline); doc["prompts"]["P3"]["active_revision"]="R999"
    report=VersionValidator(project_root).validate(doc)
    assert not report.is_valid and ("REF-ACTIVE-REVISION" in codes(report) or "INV-06" in codes(report))


def test_t10_detect_undeclared_revision_change(project_root, load_fixture):
    report=VersionValidator(project_root).validate(load_fixture("undeclared-sync-change.json"))
    assert not report.is_valid and "INV-09" in codes(report)


def test_t11_incorrect_primary_from_to(project_root, baseline):
    doc=add_release(baseline); doc["snapshots"][-1]["primary_change"]["from"]="R9"
    report=VersionValidator(project_root).validate(doc)
    assert not report.is_valid and "INV-07" in codes(report)


def test_t12_incorrect_sync_from_to(project_root, baseline):
    doc=add_release(baseline,"P3")
    # Add P4 R2 and declare as sync with intentionally wrong from value.
    p4=doc["prompts"]["P4"]; p4["revisions"]["R1"]["status"]="SUPERSEDED"
    p4["revisions"]["R2"]={"parent":"R1","snapshot":"S002","status":"ACTIVE","file":None,"sha256":"1"*64,"file_available":False,"change_role":"SYNC","summary":["test"],"reason":"test"}
    p4["active_revision"]="R2"; doc["snapshots"][-1]["prompt_state"]["P4"]="R2"
    doc["snapshots"][-1]["sync_changes"]=[{"prompt_id":"P4","from":"R9","to":"R2"}]
    report=VersionValidator(project_root).validate(doc)
    assert not report.is_valid and "INV-07" in codes(report)


def test_t13_missing_available_file_is_blocking(project_root, load_fixture):
    report=VersionValidator(project_root).validate(load_fixture("missing-active-file.json"))
    assert not report.is_valid and "INV-10" in codes(report)


def test_t14_sha_mismatch_is_blocking(project_root, load_fixture):
    report=VersionValidator(project_root).validate(load_fixture("sha-mismatch.json"))
    assert not report.is_valid and "INV-10-SHA-MISMATCH" in codes(report)


def test_t15_materialized_baseline_files_are_valid(project_root, baseline):
    assert VersionValidator(project_root).validate(baseline).is_valid
    for prompt in baseline["prompts"].values():
        revision = prompt["revisions"][prompt["active_revision"]]
        assert revision["file_available"] is True
        assert revision["file"]


def test_t16_draft_does_not_alter_active_state(project_root, baseline):
    doc=deepcopy(baseline)
    child={"id":"S002","system":"V1","parent_snapshot":"S001","status":"DRAFT","primary_change":None,"sync_changes":[],"prompt_state":deepcopy(doc["snapshots"][0]["prompt_state"]),"backup_id":None}
    doc["snapshots"].append(child); doc["systems"][0]["latest_snapshot"]="S002"
    report=VersionValidator(project_root).validate(doc)
    assert report.is_valid and doc["active_snapshot"]=="S001"
