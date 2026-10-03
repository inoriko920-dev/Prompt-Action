from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path

from prompt_action.presentation.per_prompt_query_service import PerPromptQueryService
from prompt_action.presentation.per_prompt_view_model import PerPromptViewModel

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "data/version_history.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def state():
    return PerPromptQueryService(ROOT).read()


def test_t01_ready(): assert state()["load_state"] == "ready"
def test_t02_eight_prompts(): assert len(state()["prompts"]) == 8
def test_t03_selector_is_canonical_order(): assert [x["id"] for x in state()["prompts"]] == ["P1A","P1B","P1B1","P1B2","P2","P3","P4","P5"]
def test_t04_default_not_mock_prompt3(): assert state()["selected_prompt_id"] == "P1A"
def test_t05_active_revision_from_snapshot(): assert state()["active_revision_id"] == "R1"
def test_t06_selected_defaults_active(): assert state()["selected_revision_id"] == state()["active_revision_id"]
def test_t07_only_real_r1(): assert [x["id"] for x in state()["official_revisions"]] == ["R1"]
def test_t08_no_fake_r3(): assert "R3" not in str(state())
def test_t09_no_fake_s004(): assert "S004" not in str(state())
def test_t10_baseline_snapshot_s001(): assert state()["selected_revision"]["snapshot"] == "S001"
def test_t11_baseline_role(): assert state()["selected_revision"]["change_role"] == "BASELINE"
def test_t12_no_fake_change_item(): assert state()["selected_revision"]["change_item"] is None
def test_t13_no_fake_sync_impact(): assert state()["selected_revision"]["sync_impacts"] == []
def test_t14_history_only_file_state(): assert state()["selected_revision"]["file_state"] == "HISTORY_ONLY"
def test_t15_hash_is_real_baseline(): assert state()["selected_revision"]["sha256"] == "65fb561dfaf328b204bb86ef2a55789e835fa56cfab01d89f1c67a7b348a46c5"
def test_t16_active_download_disabled(): assert state()["capabilities"]["can_download_active"] is False
def test_t17_selected_download_disabled(): assert state()["capabilities"]["can_download_selected"] is False
def test_t18_compare_disabled_baseline(): assert state()["capabilities"]["can_compare"] is False
def test_t19_snapshot_navigation_enabled(): assert state()["capabilities"]["can_view_snapshot"] is True
def test_t20_changelog_not_faked(): assert state()["capabilities"]["can_view_changelog"] is False
def test_t21_add_revision_disabled_until_step10(): assert state()["capabilities"]["can_add_revision"] is False
def test_t22_no_draft_fabricated(): assert state()["drafts"] == []
def test_t23_select_prompt_p3_is_data_driven(): assert PerPromptQueryService(ROOT).read("P3")["selected_prompt_id"] == "P3"
def test_t24_p3_still_real_r1(): assert PerPromptQueryService(ROOT).read("P3")["active_revision_id"] == "R1"
def test_t25_invalid_prompt_falls_back_first(): assert PerPromptQueryService(ROOT).read("P999")["selected_prompt_id"] == "P1A"
def test_t26_invalid_revision_falls_back_active(): assert PerPromptQueryService(ROOT).read("P2", "R999")["selected_revision_id"] == "R1"
def test_t27_query_read_only():
    before=digest(CANONICAL); q=PerPromptQueryService(ROOT); q.read(); q.read("P3"); q.read("P5","R1"); assert digest(CANONICAL)==before
def test_t28_viewmodel_refresh_read_only():
    before=digest(CANONICAL); vm=PerPromptViewModel(ROOT); vm.refresh(); assert digest(CANONICAL)==before
def test_t29_viewmodel_select_prompt_read_only():
    before=digest(CANONICAL); vm=PerPromptViewModel(ROOT); vm.selectPrompt("P4"); assert vm.state["selected_prompt_id"]=="P4" and digest(CANONICAL)==before
def test_t30_viewmodel_select_revision_read_only():
    before=digest(CANONICAL); vm=PerPromptViewModel(ROOT); vm.selectRevision("R1"); assert digest(CANONICAL)==before
def test_t31_page_replaces_placeholder(): assert "Pages.PerPromptPage" in (ROOT/"src/prompt_action/ui/qml/shell/ContentHost.qml").read_text(encoding="utf-8")
def test_t32_keeps_hidden_step03_marker():
    text=(ROOT/"src/prompt_action/ui/qml/pages/PerPromptPage.qml").read_text(encoding="utf-8"); assert 'objectName: "placeholder_prompt"' in text and "visible: false" in text
def test_t33_ui_has_prompt_selector(): assert "PromptSelector" in (ROOT/"src/prompt_action/ui/qml/pages/PerPromptPage.qml").read_text(encoding="utf-8")
def test_t34_ui_has_revision_tree(): assert "RevisionTree" in (ROOT/"src/prompt_action/ui/qml/pages/PerPromptPage.qml").read_text(encoding="utf-8")
def test_t35_ui_has_revision_detail(): assert "RevisionDetailCard" in (ROOT/"src/prompt_action/ui/qml/pages/PerPromptPage.qml").read_text(encoding="utf-8")
def test_t36_ui_has_files_card(): assert "AvailableFilesCard" in (ROOT/"src/prompt_action/ui/qml/pages/PerPromptPage.qml").read_text(encoding="utf-8")
def test_t37_active_selected_language_present():
    text=(ROOT/"src/prompt_action/ui/qml/per_prompt/RevisionTree.qml").read_text(encoding="utf-8"); assert "ACTIVE" in text and "SELECTED" in text
def test_t38_required_actions_present():
    text=(ROOT/"src/prompt_action/ui/qml/per_prompt/AvailableFilesCard.qml").read_text(encoding="utf-8");
    for label in ["Download Prompt Aktif","Download Revision Ini","Bandingkan","Lihat Snapshot","Buka Changelog","Tambah Revisi"]: assert label in text
def test_t39_no_mock_r3_or_s004_in_production_qml():
    text="\n".join(p.read_text(encoding="utf-8") for p in (ROOT/"src/prompt_action/ui/qml/per_prompt").glob("*.qml")); assert "R3" not in text and "S004" not in text
def test_t40_main_wires_per_prompt_vm():
    text=(ROOT/"src/prompt_action/main.py").read_text(encoding="utf-8"); assert "PerPromptViewModel" in text and '"perPromptViewModel": per_prompt_vm' in text
def test_t41_master_reference_exists(): assert (ROOT/"docs/UI_REFERENCE_PACKAGE_V1/materialized/images/03-Per-Prompt.jpg").is_file()
def test_t42_baseline_hash_protected(): assert digest(ROOT/"BASELINE.json") == "8ffd22fe3636309ce0484f8b724f9fe306f3156383c5f4efbcc7e59f79e90b6d"
def test_t43_version_history_hash_protected(): assert digest(CANONICAL) == "1a0fddf98b000bb908e12e5aa617b42793a399a8dd9cb36e1acf7204ca8465bb"
def test_t44_no_write_api_exposed():
    vm=PerPromptViewModel(ROOT); assert not hasattr(vm,"save") and not hasattr(vm,"edit") and not hasattr(vm,"createRevision") and not hasattr(vm,"deleteRevision")
def test_t45_baseline_reason_is_canonical(): assert state()["selected_revision"]["reason"].startswith("Seeded from verified V22.5.1")
