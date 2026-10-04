from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from prompt_action.presentation.history_query_service import SystemHistoryQueryService
from prompt_action.presentation.history_view_model import SystemHistoryViewModel

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "data/version_history.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_t01_query_reads_ready_canonical():
    state = SystemHistoryQueryService(ROOT).read()
    assert state["load_state"] == "ready"


def test_t02_active_system_is_v1():
    assert SystemHistoryQueryService(ROOT).read()["active_system"] == "V1"


def test_t03_active_snapshot_is_s001():
    assert SystemHistoryQueryService(ROOT).read()["active_snapshot"] == "S001"


def test_t04_single_legacy_node_is_v2251():
    legacy = SystemHistoryQueryService(ROOT).read()["legacy"]
    assert legacy["id"] == "V22.5.1" and legacy["verified"] is True


def test_t05_no_fake_legacy_branches():
    state = SystemHistoryQueryService(ROOT).read()
    assert "V21" not in str(state) and "V22.5.2" not in str(state)


def test_t06_system_tree_contains_v1():
    systems = SystemHistoryQueryService(ROOT).read()["systems"]
    assert [item["id"] for item in systems] == ["V1"]


def test_t07_v1_contains_only_real_snapshot():
    snapshots = SystemHistoryQueryService(ROOT).read()["systems"][0]["snapshots"]
    assert [item["id"] for item in snapshots] == ["S001"]


def test_t08_s001_is_baseline():
    assert SystemHistoryQueryService(ROOT).read()["selected_snapshot"]["title"] == "Baseline"


def test_t09_baseline_has_no_fake_primary():
    assert SystemHistoryQueryService(ROOT).read()["selected_snapshot"]["primary_change"] is None


def test_t10_baseline_has_no_fake_sync():
    assert SystemHistoryQueryService(ROOT).read()["selected_snapshot"]["sync_changes"] == []


def test_t11_completed_backup_is_honest():
    detail = SystemHistoryQueryService(ROOT).read()["selected_snapshot"]
    assert detail["status"] == "COMPLETE" and detail["backup_status"] == "VALID" and detail["backup_id"] == "B001"


def test_t12_backup_download_enabled_with_verified_evidence():
    caps = SystemHistoryQueryService(ROOT).read()["selected_snapshot"]["capabilities"]
    assert caps["can_download_snapshot_backup"] is True


def test_t13_compare_disabled_for_baseline():
    caps = SystemHistoryQueryService(ROOT).read()["selected_snapshot"]["capabilities"]
    assert caps["can_compare_previous"] is False


def test_t14_changed_prompts_disabled_for_baseline():
    caps = SystemHistoryQueryService(ROOT).read()["selected_snapshot"]["capabilities"]
    assert caps["can_view_changed_prompts"] is False


def test_t15_invalid_selection_falls_back_active():
    assert SystemHistoryQueryService(ROOT).read("S999")["selected_snapshot_id"] == "S001"


def test_t16_query_is_read_only():
    before = digest(CANONICAL)
    service = SystemHistoryQueryService(ROOT)
    service.read(); service.read("S001"); service.read()
    assert digest(CANONICAL) == before


def test_t17_viewmodel_refresh_is_read_only():
    before = digest(CANONICAL)
    vm = SystemHistoryViewModel(ROOT)
    vm.refresh()
    assert digest(CANONICAL) == before


def test_t18_viewmodel_select_keeps_canonical():
    before = digest(CANONICAL)
    vm = SystemHistoryViewModel(ROOT)
    vm.selectSnapshot("S001")
    assert vm.state["selected_snapshot_id"] == "S001" and digest(CANONICAL) == before


def test_t19_history_page_replaces_placeholder():
    text = (ROOT / "src/prompt_action/ui/qml/shell/ContentHost.qml").read_text(encoding="utf-8")
    assert "Pages.SystemHistoryPage" in text


def test_t20_history_page_keeps_step03_marker_only_hidden():
    text = (ROOT / "src/prompt_action/ui/qml/pages/SystemHistoryPage.qml").read_text(encoding="utf-8")
    assert 'objectName: "placeholder_system_history"' in text and "visible: false" in text


def test_t21_history_page_has_tree_and_detail():
    text = (ROOT / "src/prompt_action/ui/qml/pages/SystemHistoryPage.qml").read_text(encoding="utf-8")
    assert "Pohon Sistem & Snapshot" in text and "Detail Snapshot" in text

@pytest.mark.parametrize("label", ["PRIMARY CHANGE", "SYNC CHANGE", "Alasan Perubahan", "Download Snapshot Backup", "Bandingkan dengan Sebelumnya", "Lihat Changelog"])
def test_t22_to_t27_required_ui_contracts(label: str):
    text = (ROOT / "src/prompt_action/ui/qml/pages/SystemHistoryPage.qml").read_text(encoding="utf-8")
    assert label in text


def test_t28_no_mock_s004_or_r3_in_history_page():
    text = (ROOT / "src/prompt_action/ui/qml/pages/SystemHistoryPage.qml").read_text(encoding="utf-8")
    assert "S004" not in text and "R3" not in text


def test_t29_main_wires_history_viewmodel():
    text = (ROOT / "src/prompt_action/main.py").read_text(encoding="utf-8")
    assert "SystemHistoryViewModel" in text and '"historyViewModel": history_vm' in text


def test_t30_master_reference_exists():
    assert (ROOT / "docs/UI_REFERENCE_PACKAGE_V1/materialized/images/02-Sejarah-Sistem.jpg").is_file()


def test_t31_reconciled_b001_hash_protected():
    assert digest(ROOT / "backups/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip") == "f04e1b69c2613bf238c547bfab9cc81ab5708c100843e13b6750ea950f33d8a6"


def test_t32_recovered_p3_hash_protected():
    assert digest(ROOT / "prompts/V1/Prompt-3/Prompt-3_V1_R1.txt") == "0aa955989b428700293a4d76793718bd33c78015f3b0021256a665dd386c3de1"


def test_t33_legacy_reason_is_real_metadata():
    assert SystemHistoryQueryService(ROOT).read()["selected_snapshot"]["reason"] == "LEGACY_BASELINE_SEED"


def test_t34_snapshot_prompt_state_has_eight_prompts():
    assert len(SystemHistoryQueryService(ROOT).read()["selected_snapshot"]["prompt_state"]) == 8


def test_t35_no_history_write_api_exposed():
    vm = SystemHistoryViewModel(ROOT)
    assert not hasattr(vm, "save") and not hasattr(vm, "release") and not hasattr(vm, "deleteSnapshot")
