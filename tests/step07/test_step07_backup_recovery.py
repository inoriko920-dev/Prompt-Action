from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from prompt_action.presentation.backup_query_service import BackupRecoveryQueryService
from prompt_action.presentation.backup_view_model import BackupRecoveryViewModel

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "data/version_history.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def state():
    return BackupRecoveryQueryService(ROOT).read()


def test_t01_ready(): assert state()["load_state"] == "ready"
def test_t02_active_system(): assert state()["active_system"] == "V1"
def test_t03_active_snapshot(): assert state()["active_snapshot"] == "S001"
def test_t04_snapshot_complete(): assert state()["snapshot_status"] == "COMPLETE"
def test_t05_health_safe(): assert state()["recovery_health"] == "SAFE"
def test_t06_label_safe(): assert state()["recovery_label"] == "AMAN"
def test_t07_latest_backup_is_real_b001(): assert state()["latest_backup"] is not None and state()["latest_backup"]["id"] == "B001" and state()["latest_backup"]["valid"] is True
def test_t08_history_real_only(): assert [x["snapshot"] for x in state()["history"]] == ["S001"]
def test_t09_history_valid(): assert state()["history"][0]["status"] == "VALID"
def test_t10_checklist_eight(): assert len(state()["checklist"]) == 8
def test_t11_version_data_true(): assert next(x for x in state()["checklist"] if x["key"] == "version_data")["ok"] is True
def test_t12_active_prompts_true(): assert next(x for x in state()["checklist"] if x["key"] == "active_prompts")["ok"] is True
def test_t13_revisions_true(): assert next(x for x in state()["checklist"] if x["key"] == "revisions")["ok"] is True
def test_t14_full_backup_true(): assert next(x for x in state()["checklist"] if x["key"] == "full_backup")["ok"] is True
def test_t15_sha_true(): assert next(x for x in state()["checklist"] if x["key"] == "sha256")["ok"] is True
def test_t16_verify_true(): assert next(x for x in state()["checklist"] if x["key"] == "zip_verified")["ok"] is True
def test_t17_second_copy_true(): assert next(x for x in state()["checklist"] if x["key"] == "second_copy")["ok"] is True
def test_t18_download_enabled(): assert state()["actions"]["can_download_backup"] is True
def test_t19_sha_download_enabled(): assert state()["actions"]["can_download_sha256"] is True
def test_t20_verify_enabled(): assert state()["actions"]["can_verify_backup"] is True
def test_t21_folder_enabled(): assert state()["actions"]["can_open_folder"] is True
def test_t22_create_disabled(): assert state()["actions"]["can_create_backup"] is False
def test_t23_restore_disabled(): assert state()["actions"]["can_restore_backup"] is False
def test_t24_guide_available(): assert state()["actions"]["can_open_recovery_guide"] is True

def test_t25_query_read_only():
    before = digest(CANONICAL); BackupRecoveryQueryService(ROOT).read(); assert digest(CANONICAL) == before

def test_t26_viewmodel_refresh_read_only():
    before = digest(CANONICAL); vm = BackupRecoveryViewModel(ROOT); vm.refresh(); assert digest(CANONICAL) == before

def test_t27_viewmodel_no_write_api():
    vm = BackupRecoveryViewModel(ROOT); assert not hasattr(vm, "save") and not hasattr(vm, "restore") and not hasattr(vm, "createBackup")

def test_t28_page_replaces_placeholder():
    text = (ROOT / "src/prompt_action/ui/qml/shell/ContentHost.qml").read_text(encoding="utf-8"); assert "Pages.BackupRecoveryPage" in text

def test_t29_hidden_compat_marker():
    text = (ROOT / "src/prompt_action/ui/qml/pages/BackupRecoveryPage.qml").read_text(encoding="utf-8"); assert 'objectName: "placeholder_backup"' in text and "visible: false" in text

@pytest.mark.parametrize("label", [
    "STATUS PEMULIHAN","Kelengkapan Recovery","Backup Terbaru","Riwayat Backup",
    "Download Full Backup","Download SHA256","Verifikasi Backup","Buka Recovery Guide",
    "Buka Folder Backup","Buat Backup Baru","Restore Backup",
    "Perubahan belum dianggap selesai sebelum Full Backup + SHA256 + verifikasi dibuat."
])
def test_t30_to_t41_ui_contract(label: str):
    text = (ROOT / "src/prompt_action/ui/qml/pages/BackupRecoveryPage.qml").read_text(encoding="utf-8"); assert label in text

def test_t42_no_mock_s004_or_aman_literal_state():
    text = (ROOT / "src/prompt_action/ui/qml/pages/BackupRecoveryPage.qml").read_text(encoding="utf-8"); assert "S004" not in text

def test_t43_main_wires_backup_viewmodel():
    text = (ROOT / "src/prompt_action/main.py").read_text(encoding="utf-8"); assert "BackupRecoveryViewModel" in text and '"backupViewModel": backup_vm' in text

def test_t44_master_reference_exists():
    assert (ROOT / "docs/UI_REFERENCE_PACKAGE_V1/materialized/images/04-Backup-Recovery.jpg").is_file()

def test_t45_reconciled_backup_hash_protected():
    assert digest(ROOT / "backups/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip") == "f04e1b69c2613bf238c547bfab9cc81ab5708c100843e13b6750ea950f33d8a6"

def test_t46_recovered_p3_hash_protected():
    assert digest(ROOT / "prompts/V1/Prompt-3/Prompt-3_V1_R1.txt") == "0aa955989b428700293a4d76793718bd33c78015f3b0021256a665dd386c3de1"
