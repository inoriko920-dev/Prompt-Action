from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from prompt_action.data.release_repository import ReleaseRepository, sha256_path
from prompt_action.data.repository import VersionRepository
from prompt_action.data.transaction_journal import TransactionJournalStore
from prompt_action.domain.errors import ReleaseWorkflowError
from prompt_action.services.release_planner import ReleasePlanner
from prompt_action.services.release_recovery import ReleaseRecoveryService
from prompt_action.services.release_service import ReleaseService, build_candidate_document
from prompt_action.services.revision_allocator import allocate_revision
from prompt_action.services.snapshot_allocator import allocate_snapshot


def plan(project: Path, changed_p3: Path, **kwargs):
    return ReleasePlanner(project).plan_release(
        primary_prompt_id="P3", primary_source=changed_p3,
        reason=kwargs.pop("reason", "STEP 10 test release"),
        summary=kwargs.pop("summary", ["Test release"]),
        **kwargs,
    )


def err_code(exc) -> str:
    return exc.value.code


def active_snapshot(doc: dict) -> dict:
    return next(x for x in doc["snapshots"] if x["id"] == doc["active_snapshot"])


def test_t01_revision_allocator_first(): assert allocate_revision([]) == "R1"
def test_t02_revision_allocator_next(): assert allocate_revision(["R1"]) == "R2"
def test_t03_revision_allocator_gap_not_reused(): assert allocate_revision(["R1", "R3"]) == "R4"
def test_t04_snapshot_allocator_first(): assert allocate_snapshot([]) == "S001"
def test_t05_snapshot_allocator_next(): assert allocate_snapshot(["S001"]) == "S002"
def test_t06_snapshot_allocator_gap_not_reused(): assert allocate_snapshot(["S001", "S003"]) == "S004"
def test_t07_snapshot_allocator_exhaustion():
    with pytest.raises(ReleaseWorkflowError) as exc: allocate_snapshot(["S999"])
    assert err_code(exc) == "SNAPSHOT_ID_EXHAUSTED"

def test_t08_plan_uses_same_system(project, changed_p3): assert plan(project, changed_p3).system == "V1"
def test_t09_plan_parent_is_complete_baseline(project, changed_p3): assert plan(project, changed_p3).parent_snapshot == "S001"
def test_t10_plan_allocates_s002(project, changed_p3): assert plan(project, changed_p3).snapshot_id == "S002"
def test_t11_plan_primary_r2(project, changed_p3):
    p=plan(project, changed_p3); assert p.primary.from_revision == "R1" and p.primary.to_revision == "R2"
def test_t12_plan_status_backup_required(project, changed_p3): assert plan(project, changed_p3).resulting_status == "BACKUP_REQUIRED"
def test_t13_plan_token_is_deterministic(project, changed_p3): assert plan(project, changed_p3).confirmation_token == plan(project, changed_p3).confirmation_token

def test_t14_plan_target_is_canonical(project, changed_p3):
    assert plan(project, changed_p3).primary.target_relative == "prompts/V1/Prompt-3/Prompt-3_V1_R2.txt"

def test_t15_noop_primary_rejected(project, canonical):
    rel=canonical["prompts"]["P3"]["revisions"]["R1"]["file"]
    with pytest.raises(ReleaseWorkflowError) as exc:
        ReleasePlanner(project).plan_release(primary_prompt_id="P3", primary_source=project/rel, reason="noop")
    assert err_code(exc) == "NO_OP_PRIMARY"

def test_t16_previous_backup_incomplete_blocks(project, changed_p3):
    p=project/"data/version_history.json"; d=json.loads(p.read_text()); d["snapshots"][0]["status"]="BACKUP_REQUIRED"; p.write_text(json.dumps(d),encoding="utf-8")
    with pytest.raises(ReleaseWorkflowError) as exc: plan(project, changed_p3)
    assert err_code(exc) == "PREVIOUS_BACKUP_INCOMPLETE"

def test_t17_duplicate_sync_rejected(project, changed_p3, changed_p4):
    sync=[{"prompt_id":"P4","source":changed_p4},{"prompt_id":"P4","source":changed_p4}]
    with pytest.raises(ReleaseWorkflowError) as exc: plan(project, changed_p3, sync=sync)
    assert err_code(exc) == "INVALID_SYNC"

def test_t18_primary_cannot_also_sync(project, changed_p3):
    with pytest.raises(ReleaseWorkflowError) as exc: plan(project, changed_p3, sync=[{"prompt_id":"P3","source":changed_p3}])
    assert err_code(exc) == "INVALID_SYNC"

def test_t19_noop_sync_rejected(project, canonical, changed_p3):
    rel=canonical["prompts"]["P4"]["revisions"]["R1"]["file"]
    with pytest.raises(ReleaseWorkflowError) as exc: plan(project, changed_p3, sync=[{"prompt_id":"P4","source":project/rel}])
    assert err_code(exc) == "INVALID_SYNC"

def test_t20_sync_allocates_r2(project, changed_p3, changed_p4):
    p=plan(project, changed_p3, sync=[{"prompt_id":"P4","source":changed_p4}]); assert p.sync[0].to_revision == "R2"

def test_t21_sync_role_is_sync(project, changed_p3, changed_p4):
    p=plan(project, changed_p3, sync=[{"prompt_id":"P4","source":changed_p4}]); assert p.sync[0].role == "SYNC"

def test_t22_non_txt_candidate_blocked(project, changed_p3):
    bad=project/"incoming/bad.bin"; bad.write_bytes(changed_p3.read_bytes())
    with pytest.raises(ReleaseWorkflowError) as exc:
        ReleasePlanner(project).plan_release(primary_prompt_id="P3",primary_source=bad,reason="bad")
    assert err_code(exc) == "PATH_POLICY_BLOCKED"

def test_t23_invalid_utf8_blocked(project):
    bad=project/"incoming/bad.txt"; bad.parent.mkdir(parents=True,exist_ok=True); bad.write_bytes(b"\xff\xfe")
    with pytest.raises(ReleaseWorkflowError) as exc:
        ReleasePlanner(project).plan_release(primary_prompt_id="P3",primary_source=bad,reason="bad")
    assert err_code(exc) == "PATH_POLICY_BLOCKED"

def test_t24_reason_required(project, changed_p3):
    with pytest.raises(ReleaseWorkflowError) as exc: plan(project, changed_p3, reason="   ")
    assert err_code(exc) == "PATH_POLICY_BLOCKED"

def test_t25_whitespace_only_change_warns(project, canonical):
    rel=canonical["prompts"]["P3"]["revisions"]["R1"]["file"]; raw=(project/rel).read_text(encoding="utf-8")
    candidate=project/"incoming/space.txt"; candidate.parent.mkdir(parents=True,exist_ok=True); candidate.write_text(raw.replace("\n","\r\n"),encoding="utf-8",newline="")
    p=ReleasePlanner(project).plan_release(primary_prompt_id="P3",primary_source=candidate,reason="line ending normalization")
    assert any("whitespace/line endings" in w for w in p.warnings)

def test_t26_active_hash_tamper_blocks(project, canonical, changed_p3):
    rel=canonical["prompts"]["P2"]["revisions"]["R1"]["file"]; (project/rel).write_bytes((project/rel).read_bytes()+b"tamper")
    with pytest.raises(ReleaseWorkflowError) as exc: plan(project, changed_p3)
    assert err_code(exc) == "HASH_MISMATCH"

def test_t27_pending_transaction_blocks_planning(project, changed_p3):
    TransactionJournalStore(project).create("pending-one", {"snapshot_id":"S002","parent_snapshot":"S001","expected_app_data_revision":2})
    with pytest.raises(ReleaseWorkflowError) as exc: plan(project, changed_p3)
    assert err_code(exc) == "RECOVERY_REQUIRED"

def test_t28_validate_plan_is_valid(project, changed_p3): assert ReleaseService(project).validate_plan(plan(project, changed_p3)).is_valid

def test_t29_source_change_after_plan_detected(project, changed_p3):
    p=plan(project, changed_p3); changed_p3.write_bytes(changed_p3.read_bytes()+b"later")
    r=ReleaseService(project).validate_plan(p); assert not r.is_valid and r.blocking_issues[0].code == "HASH_MISMATCH"

def test_t30_canonical_change_after_plan_detected(project, changed_p3):
    p=plan(project, changed_p3); c=project/"data/version_history.json"; c.write_bytes(c.read_bytes()+b"\n")
    r=ReleaseService(project).validate_plan(p); assert not r.is_valid and any(i.code=="STATE_CHANGED_RELOAD_REQUIRED" for i in r.blocking_issues)

def test_t31_target_collision_after_plan_detected(project, changed_p3):
    p=plan(project, changed_p3); target=project/p.primary.target_relative; target.parent.mkdir(parents=True,exist_ok=True); target.write_text("collision",encoding="utf-8")
    r=ReleaseService(project).validate_plan(p); assert not r.is_valid and any(i.code=="REVISION_TARGET_EXISTS" for i in r.blocking_issues)

def test_t32_wrong_confirmation_token_rejected(project, changed_p3):
    p=plan(project, changed_p3)
    with pytest.raises(ReleaseWorkflowError) as exc: ReleaseService(project).commit_release(p,"wrong")
    assert err_code(exc) == "USER_CANCELLED"

def test_t33_commit_happy_path(project, changed_p3):
    p=plan(project, changed_p3); result=ReleaseService(project).commit_release(p,p.confirmation_token); assert result.status == "BACKUP_REQUIRED"

def test_t34_commit_activates_s002(project, changed_p3):
    p=plan(project, changed_p3); ReleaseService(project).commit_release(p,p.confirmation_token); d=json.loads((project/"data/version_history.json").read_text()); assert d["active_snapshot"]=="S002"

def test_t35_commit_increments_app_data_once(project, changed_p3):
    p=plan(project, changed_p3); ReleaseService(project).commit_release(p,p.confirmation_token); d=json.loads((project/"data/version_history.json").read_text()); assert d["app_data_revision"]==3

def test_t36_parent_snapshot_remains_complete(project, changed_p3):
    p=plan(project, changed_p3); ReleaseService(project).commit_release(p,p.confirmation_token); d=json.loads((project/"data/version_history.json").read_text()); assert next(x for x in d["snapshots"] if x["id"]=="S001")["status"]=="COMPLETE"

def test_t37_new_snapshot_backup_required(project, changed_p3):
    p=plan(project, changed_p3); ReleaseService(project).commit_release(p,p.confirmation_token); d=json.loads((project/"data/version_history.json").read_text()); s=next(x for x in d["snapshots"] if x["id"]=="S002"); assert s["status"]=="BACKUP_REQUIRED" and s["backup_id"] is None

def test_t38_backup_record_is_unchanged(project, canonical, changed_p3):
    before=canonical["backups"]; p=plan(project, changed_p3); ReleaseService(project).commit_release(p,p.confirmation_token); d=json.loads((project/"data/version_history.json").read_text()); assert d["backups"]==before

def test_t39_primary_becomes_r2(project, changed_p3):
    p=plan(project, changed_p3); ReleaseService(project).commit_release(p,p.confirmation_token); d=json.loads((project/"data/version_history.json").read_text()); assert d["prompts"]["P3"]["active_revision"]=="R2"

def test_t40_old_primary_superseded(project, changed_p3):
    p=plan(project, changed_p3); ReleaseService(project).commit_release(p,p.confirmation_token); d=json.loads((project/"data/version_history.json").read_text()); assert d["prompts"]["P3"]["revisions"]["R1"]["status"]=="SUPERSEDED"

def test_t41_new_revision_file_exact(project, changed_p3):
    p=plan(project, changed_p3); ReleaseService(project).commit_release(p,p.confirmation_token); assert sha256_path(project/p.primary.target_relative)==p.primary.source_sha256

def test_t42_unchanged_prompt_stays_r1(project, changed_p3):
    p=plan(project, changed_p3); ReleaseService(project).commit_release(p,p.confirmation_token); d=json.loads((project/"data/version_history.json").read_text()); assert d["prompts"]["P4"]["active_revision"]=="R1"

def test_t43_committed_canonical_valid(project, changed_p3):
    p=plan(project, changed_p3); ReleaseService(project).commit_release(p,p.confirmation_token); assert VersionRepository(project).validate(VersionRepository(project).load()).is_valid

def test_t44_journal_committed(project, changed_p3):
    p=plan(project, changed_p3); result=ReleaseService(project).commit_release(p,p.confirmation_token); assert TransactionJournalStore(project).load(result.txn_id)["phase"]=="COMMITTED"

def test_t45_manifest_written(project, changed_p3):
    p=plan(project, changed_p3); result=ReleaseService(project).commit_release(p,p.confirmation_token); assert (project/"release_txn"/result.txn_id/"manifest.json").is_file()

def test_t46_changelog_written(project, changed_p3):
    p=plan(project, changed_p3); result=ReleaseService(project).commit_release(p,p.confirmation_token); assert (project/"release_txn"/result.txn_id/"CHANGELOG.md").is_file()

def test_t47_staged_file_exact(project, changed_p3):
    p=plan(project, changed_p3); result=ReleaseService(project).commit_release(p,p.confirmation_token); j=TransactionJournalStore(project).load(result.txn_id); staged=project/"release_txn"/result.txn_id/j["staged"]["P3"]; assert sha256_path(staged)==p.primary.source_sha256

def test_t48_immutable_target_refuses_overwrite(project):
    r=ReleaseRepository(project); target=project/"x.txt"; target.write_text("old",encoding="utf-8"); raw=b"new"; digest=hashlib.sha256(raw).hexdigest()
    with pytest.raises(ReleaseWorkflowError) as exc: r.place_new_file(target,raw,digest)
    assert err_code(exc)=="REVISION_TARGET_EXISTS" and target.read_text()=="old"

def test_t49_exclusive_lock_blocks_second_holder(project):
    r=ReleaseRepository(project)
    with r.exclusive_lock("one"):
        with pytest.raises(ReleaseWorkflowError) as exc:
            with r.exclusive_lock("two"): pass
        assert err_code(exc)=="RELEASE_BUSY"

def test_t50_journal_pending_inspection(project):
    store=TransactionJournalStore(project); store.create("pending-one",{"snapshot_id":"S002","parent_snapshot":"S001","expected_app_data_revision":2}); assert store.inspect_pending()["txn_id"]=="pending-one"

def test_t51_multiple_pending_requires_recovery(project):
    store=TransactionJournalStore(project); store.create("a",{"snapshot_id":"S002","parent_snapshot":"S001","expected_app_data_revision":2}); store.create("b",{"snapshot_id":"S003","parent_snapshot":"S001","expected_app_data_revision":2})
    with pytest.raises(ReleaseWorkflowError) as exc: store.inspect_pending()
    assert err_code(exc)=="RECOVERY_REQUIRED"

@pytest.mark.parametrize("phase",["PREPARING","STAGED","PLACING_FILES","FILES_PLACED","COMMITTING_METADATA"])
def test_t52_t56_precommit_runtime_failure_aborts(project, changed_p3, phase):
    p=plan(project,changed_p3)
    def fail(name):
        if name==phase: raise RuntimeError("injected")
    with pytest.raises(ReleaseWorkflowError): ReleaseService(project,fault_injector=fail).commit_release(p,p.confirmation_token)
    assert TransactionJournalStore(project).unresolved()==[]
    assert json.loads((project/"data/version_history.json").read_text())["active_snapshot"]=="S001"
    assert not (project/p.primary.target_relative).exists()

def test_t57_post_commit_failure_requires_recovery(project, changed_p3):
    p=plan(project,changed_p3)
    def fail(name):
        if name=="METADATA_COMMITTED": raise RuntimeError("injected")
    with pytest.raises(ReleaseWorkflowError) as exc: ReleaseService(project,fault_injector=fail).commit_release(p,p.confirmation_token)
    assert err_code(exc)=="RECOVERY_REQUIRED" and ReleaseRecoveryService(project).inspect_pending_transaction() is not None

def test_t58_resume_verifies_post_commit_ambiguity(project, changed_p3):
    p=plan(project,changed_p3)
    def crash(name):
        if name=="METADATA_COMMITTED": raise SystemExit("crash")
    with pytest.raises(SystemExit): ReleaseService(project,fault_injector=crash).commit_release(p,p.confirmation_token)
    recovery=ReleaseRecoveryService(project); state=recovery.inspect_pending_transaction(); result=recovery.recover_transaction(state.txn_id,"resume"); assert result.phase=="COMMITTED"

def test_t59_crash_at_staged_is_pending(project, changed_p3):
    p=plan(project,changed_p3)
    def crash(name):
        if name=="STAGED": raise SystemExit("crash")
    with pytest.raises(SystemExit): ReleaseService(project,fault_injector=crash).commit_release(p,p.confirmation_token)
    assert ReleaseRecoveryService(project).inspect_pending_transaction().phase=="STAGED"

def test_t60_abort_staged_crash(project, changed_p3):
    p=plan(project,changed_p3)
    def crash(name):
        if name=="STAGED": raise SystemExit("crash")
    with pytest.raises(SystemExit): ReleaseService(project,fault_injector=crash).commit_release(p,p.confirmation_token)
    recovery=ReleaseRecoveryService(project); state=recovery.inspect_pending_transaction(); result=recovery.recover_transaction(state.txn_id,"abort"); assert result.phase=="ABORTED"

def test_t61_crash_files_placed_keeps_exact_target(project, changed_p3):
    p=plan(project,changed_p3)
    def crash(name):
        if name=="FILES_PLACED": raise SystemExit("crash")
    with pytest.raises(SystemExit): ReleaseService(project,fault_injector=crash).commit_release(p,p.confirmation_token)
    assert (project/p.primary.target_relative).is_file()

def test_t62_abort_files_placed_removes_target(project, changed_p3):
    p=plan(project,changed_p3)
    def crash(name):
        if name=="FILES_PLACED": raise SystemExit("crash")
    with pytest.raises(SystemExit): ReleaseService(project,fault_injector=crash).commit_release(p,p.confirmation_token)
    recovery=ReleaseRecoveryService(project); state=recovery.inspect_pending_transaction(); recovery.recover_transaction(state.txn_id,"abort"); assert not (project/p.primary.target_relative).exists()

def test_t63_resume_files_placed_commits(project, changed_p3):
    p=plan(project,changed_p3)
    def crash(name):
        if name=="FILES_PLACED": raise SystemExit("crash")
    with pytest.raises(SystemExit): ReleaseService(project,fault_injector=crash).commit_release(p,p.confirmation_token)
    recovery=ReleaseRecoveryService(project); state=recovery.inspect_pending_transaction(); result=recovery.recover_transaction(state.txn_id,"resume"); assert result.phase=="COMMITTED"

def test_t64_resume_result_is_s002(project, changed_p3):
    p=plan(project,changed_p3)
    def crash(name):
        if name=="FILES_PLACED": raise SystemExit("crash")
    with pytest.raises(SystemExit): ReleaseService(project,fault_injector=crash).commit_release(p,p.confirmation_token)
    recovery=ReleaseRecoveryService(project); state=recovery.inspect_pending_transaction(); recovery.recover_transaction(state.txn_id,"resume"); assert json.loads((project/"data/version_history.json").read_text())["active_snapshot"]=="S002"

def test_t65_new_release_blocked_until_step11_backup(project, changed_p3):
    p=plan(project,changed_p3); ReleaseService(project).commit_release(p,p.confirmation_token)
    new=project/"incoming/P4-later.txt"; new.write_text("new p4",encoding="utf-8")
    with pytest.raises(ReleaseWorkflowError) as exc:
        ReleasePlanner(project).plan_release(primary_prompt_id="P4",primary_source=new,reason="later")
    assert err_code(exc)=="PREVIOUS_BACKUP_INCOMPLETE"

def test_t66_source_changed_before_commit_is_blocked(project, changed_p3):
    p=plan(project,changed_p3); changed_p3.write_bytes(changed_p3.read_bytes()+b"changed")
    with pytest.raises(ReleaseWorkflowError) as exc: ReleaseService(project).commit_release(p,p.confirmation_token)
    assert err_code(exc)=="HASH_MISMATCH"

def test_t67_target_created_before_commit_is_blocked(project, changed_p3):
    p=plan(project,changed_p3); target=project/p.primary.target_relative; target.parent.mkdir(parents=True,exist_ok=True); target.write_text("collision",encoding="utf-8")
    with pytest.raises(ReleaseWorkflowError) as exc: ReleaseService(project).commit_release(p,p.confirmation_token)
    assert err_code(exc)=="REVISION_TARGET_EXISTS"

def test_t68_candidate_document_declares_exact_change(project, canonical, changed_p3):
    p=plan(project,changed_p3); d=build_candidate_document(canonical,p); s=next(x for x in d["snapshots"] if x["id"]=="S002"); assert s["primary_change"]=={"prompt_id":"P3","from":"R1","to":"R2"}

def test_t69_candidate_document_does_not_create_backup(project, canonical, changed_p3):
    p=plan(project,changed_p3); d=build_candidate_document(canonical,p); assert d["backups"]==canonical["backups"] and next(x for x in d["snapshots"] if x["id"]=="S002")["backup_id"] is None

def test_t70_repo_production_baseline_remains_s001_complete(repo_root):
    d=json.loads((repo_root/"data/version_history.json").read_text(encoding="utf-8")); assert d["app_data_revision"]==2 and d["active_snapshot"]=="S001" and active_snapshot(d)["status"]=="COMPLETE"
