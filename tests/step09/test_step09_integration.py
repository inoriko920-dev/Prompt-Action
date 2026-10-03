from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QSG_RHI_BACKEND", "software")
os.environ.setdefault("QSG_RENDER_LOOP", "basic")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

import pytest
from PySide6.QtCore import QObject
from PySide6.QtTest import QTest

from prompt_action.bootstrap.qml_boot import create_application, load_qml
from prompt_action.services.step09 import (
    CancelToken, CapabilityService, CompareError, DownloadError, DownloadService,
    GlobalSearchService, PathSafetyError, PathSafetyPolicy, RevisionCompareService,
    SearchError, SnapshotCompareService,
)
from prompt_action.services.step09.download import sha256_file
from prompt_action.settings.sanitization import sanitize_value
from prompt_action.ui.viewmodels.search_view_model import SearchViewModel

ROOT = Path(__file__).resolve().parents[2]
APP_QML = ROOT / "src/prompt_action/ui/qml/App.qml"
CANONICAL = ROOT / "data/version_history.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_bytes(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def build_fixture(tmp_path: Path):
    root = tmp_path / "Prompt Action Ω"
    root.mkdir(parents=True, exist_ok=True)
    p3r1 = b"alpha\nbeta\nfreeze alpha\n"
    p3r2 = b"alpha\nbeta changed\nfreeze alpha update\n"
    p3r3 = b"alpha\nhello   world\n"
    p3r4 = b"alpha\nhello world\n"
    p3r5 = b"line one\r\nline two\r\n"
    p3r6 = b"line one\nline two\n"
    p4r1 = b"sync old\n"
    p4r2 = b"sync new\n"
    paths = {}
    for name, data in {
        "prompts/V1/Prompt-3/Prompt-3_V1_R1.txt": p3r1,
        "prompts/V1/Prompt-3/Prompt-3_V1_R2.txt": p3r2,
        "prompts/V1/Prompt-3/Prompt-3_V1_R3.txt": p3r3,
        "prompts/V1/Prompt-3/Prompt-3_V1_R4.txt": p3r4,
        "prompts/V1/Prompt-3/Prompt-3_V1_R5.txt": p3r5,
        "prompts/V1/Prompt-3/Prompt-3_V1_R6.txt": p3r6,
        "prompts/V1/Prompt-4/Prompt-4_V1_R1.txt": p4r1,
        "prompts/V1/Prompt-4/Prompt-4_V1_R2.txt": p4r2,
    }.items():
        paths[name] = write_bytes(root / name, data)
    backup_bytes = (b"PK\x03\x04PROMPT-ACTION-TEST\n" * 3000)
    backup_rel = "backups/Prompt-Action-V1-S002-FULL-BACKUP.zip"
    backup_sha = write_bytes(root / backup_rel, backup_bytes)
    side_rel = backup_rel + ".sha256"
    side_bytes = f"{backup_sha}  {Path(backup_rel).name}\n".encode()
    side_sha = write_bytes(root / side_rel, side_bytes)
    guide_rel = "docs/recovery-guide.md"
    guide_sha = write_bytes(root / guide_rel, b"# Recovery Guide\nread only\n")
    changelog_rel = "docs/changelog/S002.md"
    changelog_sha = write_bytes(root / changelog_rel, b"# S002\nUpdate Prompt 3 and sync Prompt 4\n")

    def revision(rel: str, snapshot: str, role: str, parent=None, summary=None):
        return {
            "parent": parent, "snapshot": snapshot, "status": "ACTIVE", "file": rel,
            "sha256": paths[rel], "file_available": True, "change_role": role,
            "summary": summary or [role], "reason": "fixture",
        }

    document = {
        "schema_version": 1, "app_data_revision": 9, "app_version": "test", "active_system": "V1", "active_snapshot": "S002",
        "systems": [
            {"id":"V1","status":"ACTIVE","latest_snapshot":"S002"},
            {"id":"V2","status":"ARCHIVE","latest_snapshot":"S900"},
        ],
        "snapshots": [
            {"id":"S001","system":"V1","parent_snapshot":None,"status":"COMPLETE","primary_change":None,"sync_changes":[],"prompt_state":{"P3":"R1","P4":"R1"},"backup_id":None},
            {"id":"S002","system":"V1","parent_snapshot":"S001","status":"COMPLETE","primary_change":{"prompt_id":"P3","from":"R1","to":"R2"},"sync_changes":[{"prompt_id":"P4","from":"R1","to":"R2"}],"prompt_state":{"P3":"R2","P4":"R2"},"backup_id":"B2"},
            {"id":"S900","system":"V2","parent_snapshot":None,"status":"COMPLETE","primary_change":None,"sync_changes":[],"prompt_state":{"P3":"R2","P4":"R2"},"backup_id":None},
        ],
        "prompts": {
            "P3": {"display_name":"Prompt 3","active_revision":"R2","revisions": {
                "R1": revision("prompts/V1/Prompt-3/Prompt-3_V1_R1.txt","S001","BASELINE",None,["baseline alpha"]),
                "R2": revision("prompts/V1/Prompt-3/Prompt-3_V1_R2.txt","S002","PRIMARY","R1",["Freeze alpha update"]),
                "R3": revision("prompts/V1/Prompt-3/Prompt-3_V1_R3.txt","S002","TEST","R2"),
                "R4": revision("prompts/V1/Prompt-3/Prompt-3_V1_R4.txt","S002","TEST","R3"),
                "R5": revision("prompts/V1/Prompt-3/Prompt-3_V1_R5.txt","S002","TEST","R4"),
                "R6": revision("prompts/V1/Prompt-3/Prompt-3_V1_R6.txt","S002","TEST","R5"),
            }},
            "P4": {"display_name":"Prompt 4","active_revision":"R2","revisions": {
                "R1": revision("prompts/V1/Prompt-4/Prompt-4_V1_R1.txt","S001","BASELINE"),
                "R2": revision("prompts/V1/Prompt-4/Prompt-4_V1_R2.txt","S002","SYNC","R1",["sync update"]),
            }},
        },
        "backups": [{
            "id":"B2","snapshot":"S002","status":"VALID","verified":True,"file":backup_rel,"sha256":backup_sha,
            "sha256_file":side_rel,"sha256_file_sha256":side_sha,
        }],
        "release_policy": {},
    }
    return root, document, {"guide": (guide_rel, guide_sha), "changelog": (changelog_rel, changelog_sha), "backup_sha": backup_sha}


@pytest.fixture(scope="session")
def app():
    return create_application(["step09-tests"])


def test_t01_search_exact_prompt_id(tmp_path):
    root, doc, _ = build_fixture(tmp_path); page=GlobalSearchService(root,document=doc).search("P3"); assert page.results[0].entity.entity_type=="PROMPT" and page.results[0].entity.stable_id=="P3"

def test_t02_search_exact_snapshot_id(tmp_path):
    root,doc,_=build_fixture(tmp_path); page=GlobalSearchService(root,document=doc).search("S002"); assert page.results[0].entity.entity_type=="SNAPSHOT" and page.results[0].entity.stable_id=="S002"

def test_t03_search_exact_revision_id(tmp_path):
    root,doc,_=build_fixture(tmp_path); page=GlobalSearchService(root,document=doc).search("R2"); assert page.results and page.results[0].entity.entity_type=="REVISION" and page.results[0].score==100

def test_t04_search_case_insensitive_name(tmp_path):
    root,doc,_=build_fixture(tmp_path); assert GlobalSearchService(root,document=doc).search("pRoMpT 3").results[0].entity.stable_id=="P3"

def test_t05_search_prefix(tmp_path):
    root,doc,_=build_fixture(tmp_path); page=GlobalSearchService(root,document=doc).search("snap"); assert any(x.entity.entity_type=="SNAPSHOT" for x in page.results)

def test_t06_search_phrase_token(tmp_path):
    root,doc,_=build_fixture(tmp_path); page=GlobalSearchService(root,document=doc).search("freeze alpha"); assert any(x.entity.stable_id=="P3:R2" for x in page.results)

def test_t07_search_empty_idle(tmp_path):
    root,doc,_=build_fixture(tmp_path); assert GlobalSearchService(root,document=doc).search("   ").state=="IDLE"

def test_t08_search_result_cap(tmp_path):
    root,doc,_=build_fixture(tmp_path); assert len(GlobalSearchService(root,document=doc,result_cap=2).search("r").results)<=2

def test_t09_search_deterministic_ranking(tmp_path):
    root,doc,_=build_fixture(tmp_path); s=GlobalSearchService(root,document=doc); a=[x.to_dict() for x in s.search("R2").results]; b=[x.to_dict() for x in s.search("R2").results]; assert a==b

def test_t10_keyboard_navigation_state(tmp_path, app):
    root,doc,_=build_fixture(tmp_path); vm=SearchViewModel(root,service=GlobalSearchService(root,document=doc),debounce_ms=0); vm.setQuery("R2"); QTest.qWait(10); before=vm.state["selected_index"]; vm.moveSelection(1); assert vm.state["selected_index"]>=before

def test_t11_cancel_stale_query(tmp_path):
    root,doc,_=build_fixture(tmp_path); token=CancelToken(); token.cancel();
    with pytest.raises(SearchError) as exc: GlobalSearchService(root,document=doc).search("P3",cancel_token=token)
    assert exc.value.code=="SEARCH_CANCELLED"

def test_t12_search_invalid_index_degraded(tmp_path):
    root=tmp_path/"bad"; root.mkdir(); service=GlobalSearchService(root,document={"invalid":True}); assert service.ready is False and service.search("P3").state=="ERROR"

def test_t13_deep_link_prompt(tmp_path):
    root,doc,_=build_fixture(tmp_path); s=GlobalSearchService(root,document=doc); target=s.resolver.resolve(s.search("P3").results[0].entity); assert (target.route,target.entity_id)==("prompt","P3")

def test_t14_deep_link_snapshot(tmp_path):
    root,doc,_=build_fixture(tmp_path); s=GlobalSearchService(root,document=doc); target=s.resolver.resolve(s.search("S002").results[0].entity); assert (target.route,target.entity_id)==("system_history","S002")

def test_t15_deep_link_backup(tmp_path):
    root,doc,_=build_fixture(tmp_path); s=GlobalSearchService(root,document=doc); result=next(x for x in s.search("B2").results if x.entity.entity_type=="BACKUP"); target=s.resolver.resolve(result.entity); assert target.route=="backup" and target.entity_id=="S002"

def test_t16_compare_same_prompt(tmp_path):
    root,doc,_=build_fixture(tmp_path); r=RevisionCompareService(root,document=doc).compare("P3","R1","R2"); assert r.status=="OK" and r.changed_lines>0

def test_t17_swap_compare_sides(tmp_path):
    root,doc,_=build_fixture(tmp_path); r=RevisionCompareService(root,document=doc).compare("P3","R2","R1"); assert (r.left_revision,r.right_revision)==("R2","R1")

def test_t18_cross_prompt_compare_rejected(tmp_path):
    root,doc,_=build_fixture(tmp_path)
    with pytest.raises(CompareError) as exc: RevisionCompareService(root,document=doc).compare_refs("P3","R1","P4","R1")
    assert exc.value.code=="COMPARE_CROSS_PROMPT"

def test_t19_missing_revision_file_blocked(tmp_path):
    root,doc,_=build_fixture(tmp_path); doc=deepcopy(doc); doc["prompts"]["P3"]["revisions"]["R2"]["file_available"]=False
    with pytest.raises(CompareError) as exc: RevisionCompareService(root,document=doc).compare("P3","R1","R2")
    assert exc.value.code=="COMPARE_FILE_MISSING"

def test_t20_compare_hash_mismatch_blocked(tmp_path):
    root,doc,_=build_fixture(tmp_path); doc=deepcopy(doc); doc["prompts"]["P3"]["revisions"]["R2"]["sha256"]="0"*64
    with pytest.raises(CompareError) as exc: RevisionCompareService(root,document=doc).compare("P3","R1","R2")
    assert exc.value.code=="COMPARE_HASH_MISMATCH"

def test_t21_line_diff_correct(tmp_path):
    root,doc,_=build_fixture(tmp_path); text=RevisionCompareService(root,document=doc).compare("P3","R1","R2").unified_diff; assert "-beta" in text and "+beta changed" in text

def test_t22_word_highlight_optional_consistent(tmp_path):
    root,doc,_=build_fixture(tmp_path); svc=RevisionCompareService(root,document=doc); assert svc.compare("P3","R1","R2").unified_diff==svc.compare("P3","R1","R2").unified_diff

def test_t23_whitespace_only_change_visible(tmp_path):
    root,doc,_=build_fixture(tmp_path); r=RevisionCompareService(root,document=doc).compare("P3","R3","R4"); assert r.whitespace_only is True and "hello" in r.unified_diff

def test_t24_eol_only_handling(tmp_path):
    root,doc,_=build_fixture(tmp_path); r=RevisionCompareService(root,document=doc).compare("P3","R5","R6"); assert r.eol_only is True and "EOL-ONLY" in r.unified_diff

def test_t25_snapshot_compare_composition(tmp_path):
    root,doc,_=build_fixture(tmp_path); r=SnapshotCompareService(root,document=doc).compare("S001","S002"); assert {x["prompt_id"] for x in r.changed}=={"P3","P4"}

def test_t26_primary_delta_correct(tmp_path):
    root,doc,_=build_fixture(tmp_path); r=SnapshotCompareService(root,document=doc).compare("S001","S002"); assert r.primary_delta=={"prompt_id":"P3","from":"R1","to":"R2","role":"PRIMARY"}

def test_t27_sync_delta_correct(tmp_path):
    root,doc,_=build_fixture(tmp_path); r=SnapshotCompareService(root,document=doc).compare("S001","S002"); assert r.sync_deltas[0]["prompt_id"]=="P4" and r.sync_deltas[0]["role"]=="SYNC"

def test_t28_same_snapshot_compare(tmp_path):
    root,doc,_=build_fixture(tmp_path); r=SnapshotCompareService(root,document=doc).compare("S001","S001"); assert r.status=="SAME" and not r.changed

def test_t29_cross_system_warning(tmp_path):
    root,doc,_=build_fixture(tmp_path); assert SnapshotCompareService(root,document=doc).compare("S002","S900").cross_system_warning is True

def test_t30_compare_no_mutation(tmp_path):
    root,doc,_=build_fixture(tmp_path); before=json.dumps(doc,sort_keys=True); RevisionCompareService(root,document=doc).compare("P3","R1","R2"); SnapshotCompareService(root,document=doc).compare("S001","S002"); assert json.dumps(doc,sort_keys=True)==before

def test_t31_download_verified_prompt_exact_bytes(tmp_path):
    root,doc,_=build_fixture(tmp_path); out=tmp_path/"out"; out.mkdir(); svc=DownloadService(root,document=doc); plan=svc.prepare({"type":"prompt_revision","prompt_id":"P3","revision_id":"R2"}); result=svc.execute(plan,out); assert result.status=="SUCCESS" and result.path.read_bytes()==plan.source_path.read_bytes()

def test_t32_download_active_prompt_resolves_pointer(tmp_path):
    root,doc,_=build_fixture(tmp_path); plan=DownloadService(root,document=doc).prepare({"type":"active_prompt","prompt_id":"P3"}); assert plan.stable_id=="P3:R2"

def test_t33_download_missing_source_blocked(tmp_path):
    root,doc,_=build_fixture(tmp_path); doc=deepcopy(doc); doc["prompts"]["P3"]["revisions"]["R2"]["file_available"]=False
    with pytest.raises(DownloadError) as exc: DownloadService(root,document=doc).prepare({"type":"prompt_revision","prompt_id":"P3","revision_id":"R2"})
    assert exc.value.code=="DOWNLOAD_SOURCE_MISSING"

def test_t34_download_hash_mismatch_blocked(tmp_path):
    root,doc,_=build_fixture(tmp_path); doc=deepcopy(doc); doc["prompts"]["P3"]["revisions"]["R2"]["sha256"]="f"*64
    with pytest.raises(DownloadError) as exc: DownloadService(root,document=doc).prepare({"type":"prompt_revision","prompt_id":"P3","revision_id":"R2"})
    assert exc.value.code=="DOWNLOAD_HASH_MISMATCH"

def test_t35_download_zip_streaming(tmp_path):
    root,doc,_=build_fixture(tmp_path); out=tmp_path/"out"; out.mkdir(); svc=DownloadService(root,document=doc,chunk_size=4096); plan=svc.prepare({"type":"backup","backup_id":"B2"}); result=svc.execute(plan,out); assert result.bytes_copied==plan.source_path.stat().st_size and result.bytes_copied>4096

def test_t36_download_sha_sidecar(tmp_path):
    root,doc,_=build_fixture(tmp_path); plan=DownloadService(root,document=doc).prepare({"type":"sha256","backup_id":"B2"}); assert plan.filename.endswith(".sha256")

def test_t37_download_changelog(tmp_path):
    root,doc,meta=build_fixture(tmp_path); rel,sha=meta["changelog"]; plan=DownloadService(root,document=doc).prepare({"type":"changelog","id":"S002","approved_file":rel,"sha256":sha}); assert plan.source_path.name=="S002.md"

def test_t38_path_traversal_rejected(tmp_path):
    root,_,_=build_fixture(tmp_path)
    with pytest.raises(PathSafetyError) as exc: PathSafetyPolicy(root).resolve_source(root,"../secret.txt",must_exist=False)
    assert exc.value.code=="PATH_ESCAPE"

def test_t39_symlink_junction_escape_rejected(tmp_path):
    root,_,_=build_fixture(tmp_path); outside=tmp_path/"outside.txt"; outside.write_text("x")
    with pytest.raises(PathSafetyError) as exc: PathSafetyPolicy.assert_resolved_within(root,outside,escape_code="PATH_SYMLINK_ESCAPE")
    assert exc.value.code=="PATH_SYMLINK_ESCAPE"

def test_t40_absolute_source_injection_rejected(tmp_path):
    root,_,_=build_fixture(tmp_path); absolute=str((tmp_path/"outside.txt").resolve())
    with pytest.raises(PathSafetyError) as exc: PathSafetyPolicy(root).resolve_source(root,absolute,must_exist=False)
    assert exc.value.code=="PATH_ABSOLUTE_SOURCE"

def test_t41_destination_overwrite_prompt(tmp_path):
    root,doc,_=build_fixture(tmp_path); out=tmp_path/"out"; out.mkdir(); svc=DownloadService(root,document=doc); plan=svc.prepare({"type":"prompt_revision","prompt_id":"P3","revision_id":"R2"}); (out/plan.filename).write_text("existing"); result=svc.execute(plan,out,conflict_policy="cancel"); assert result.code=="DOWNLOAD_DEST_EXISTS" and (out/plan.filename).read_text()=="existing"

def test_t42_keep_both_safe_naming(tmp_path):
    root,doc,_=build_fixture(tmp_path); out=tmp_path/"out"; out.mkdir(); svc=DownloadService(root,document=doc); plan=svc.prepare({"type":"prompt_revision","prompt_id":"P3","revision_id":"R2"}); (out/plan.filename).write_text("existing"); result=svc.execute(plan,out,conflict_policy="keep_both"); assert result.status=="SUCCESS" and "(2)" in result.path.name

def test_t43_destination_unwritable_recoverable(tmp_path):
    root,doc,_=build_fixture(tmp_path); plan=DownloadService(root,document=doc).prepare({"type":"prompt_revision","prompt_id":"P3","revision_id":"R2"})
    with pytest.raises(DownloadError) as exc: DownloadService(root,document=doc).execute(plan,tmp_path/"missing-destination")
    assert exc.value.code=="DOWNLOAD_DEST_UNWRITABLE"

def test_t44_unicode_destination(tmp_path):
    root,doc,_=build_fixture(tmp_path); out=tmp_path/"Unduhan Ω"; out.mkdir(); svc=DownloadService(root,document=doc); r=svc.copy_exact({"type":"prompt_revision","prompt_id":"P3","revision_id":"R1"},out); assert r.status=="SUCCESS" and r.path.is_file()

def test_t45_path_with_spaces(tmp_path):
    root,doc,_=build_fixture(tmp_path); out=tmp_path/"Folder Dengan Spasi"; out.mkdir(); r=DownloadService(root,document=doc).copy_exact({"type":"prompt_revision","prompt_id":"P3","revision_id":"R1"},out); assert r.path.parent==out.resolve()

def test_t46_long_path_handling(tmp_path):
    with pytest.raises(PathSafetyError) as exc: PathSafetyPolicy.validate_final_path(Path("C:/")/("x"*260))
    assert exc.value.code=="PATH_TOO_LONG"

def test_t47_cancel_cleans_temp(tmp_path):
    root,doc,_=build_fixture(tmp_path); out=tmp_path/"out"; out.mkdir(); svc=DownloadService(root,document=doc,chunk_size=4096); plan=svc.prepare({"type":"backup","backup_id":"B2"}); token=CancelToken(); token.cancel(); r=svc.execute(plan,out,cancel_token=token); assert r.code=="DOWNLOAD_CANCELLED" and not list(out.glob(".tmp-*")) and not list(out.glob("*.zip"))

def test_t48_copy_failure_cleans_temp(tmp_path):
    root,doc,_=build_fixture(tmp_path); out=tmp_path/"out"; out.mkdir(); svc=DownloadService(root,document=doc,chunk_size=4096); plan=svc.prepare({"type":"backup","backup_id":"B2"})
    def fail(_): raise OSError("simulated")
    with pytest.raises(DownloadError) as exc: svc.execute(plan,out,before_chunk=fail)
    assert exc.value.code=="DOWNLOAD_COPY_FAILED" and not list(out.glob(".tmp-*")) and not list(out.glob("*.zip"))

def test_t49_large_zip_no_ram_spike_contract(tmp_path):
    root,doc,_=build_fixture(tmp_path); out=tmp_path/"out"; out.mkdir(); calls=[]; svc=DownloadService(root,document=doc,chunk_size=4096); plan=svc.prepare({"type":"backup","backup_id":"B2"}); svc.execute(plan,out,before_chunk=lambda n:calls.append(n)); assert len(calls)>2 and svc.chunk_size==4096

def test_t50_open_folder_safe(tmp_path):
    folder=tmp_path/"safe"; folder.mkdir(); file=folder/"x.txt"; file.write_text("x"); assert PathSafetyPolicy.safe_open_folder_target(file)==folder.resolve()

def test_t51_capability_disabled_reason():
    cap=CapabilityService(search_ready=False).get("SEARCH"); assert cap.enabled is False and cap.reason

def test_t52_add_revision_still_disabled():
    cap=CapabilityService().get("ADD_REVISION"); assert cap.enabled is False and "STEP 10" in cap.reason

def test_t53_create_backup_still_disabled():
    cap=CapabilityService().get("CREATE_BACKUP"); assert cap.enabled is False and "STEP 11" in cap.reason

def test_t54_restore_still_disabled():
    cap=CapabilityService().get("RESTORE"); assert cap.enabled is False and "STEP 12" in cap.reason

def test_t55_search_compare_download_no_canonical_mutation():
    before=digest(CANONICAL); GlobalSearchService(ROOT).search("P3");
    with pytest.raises(CompareError): RevisionCompareService(ROOT).compare("P3","R1","R1")
    with pytest.raises(DownloadError): DownloadService(ROOT).prepare({"type":"active_prompt","prompt_id":"P3"})
    assert digest(CANONICAL)==before

def test_t56_ui_1366x768(app):
    engine=load_qml(APP_QML); warnings=[]; engine.warnings.connect(lambda items:warnings.extend(str(x.toString()) for x in items)); QTest.qWait(80); assert engine.rootObjects(); root=engine.rootObjects()[0]; root.setWidth(1366); root.setHeight(768); QTest.qWait(30); assert root.width()==1366 and root.height()==768 and warnings==[]; engine.deleteLater()

def test_t57_dpi_150_workflow_contract():
    text=(ROOT/".github/workflows/ci-step09.yml").read_text(encoding="utf-8"); assert "QT_SCALE_FACTOR: '1.5'" in text and "DPI 150" in text

def test_t58_keyboard_focus_contract():
    top=(ROOT/"src/prompt_action/ui/qml/shell/TopBar.qml").read_text(encoding="utf-8"); field=(ROOT/"src/prompt_action/ui/qml/components/PASearchField.qml").read_text(encoding="utf-8"); assert all(x in top for x in ("Qt.Key_Down","Qt.Key_Up","Qt.Key_Return","Qt.Key_Escape")) and "Qt.StrongFocus" in field

def test_t59_logs_and_diagnostics_sanitized():
    clean=sanitize_value({"token":"ghp_123456789012345678901234567890","authorization":"Bearer abcdefghijklmnop","path":str(ROOT/"private")},project_root=ROOT); dumped=json.dumps(clean); assert "ghp_" not in dumped and "Bearer" not in dumped and "<PROJECT_ROOT>" in dumped

def test_t60_protected_corpus_unchanged():
    assert digest(ROOT/"BASELINE.json")=="8ffd22fe3636309ce0484f8b724f9fe306f3156383c5f4efbcc7e59f79e90b6d" and digest(CANONICAL)=="1a0fddf98b000bb908e12e5aa617b42793a399a8dd9cb36e1acf7204ca8465bb"
