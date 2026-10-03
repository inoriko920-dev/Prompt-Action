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
def test_t04_backup_required(): assert state()["snapshot_status"] == "BACKUP_REQUIRED"
def test_t05_health_required(): assert state()["recovery_health"] == "REQUIRED"
def test_t06_label_not_safe(): assert state()["recovery_label"] == "BELUM AMAN"
def test_t07_no_fake_latest_backup(): assert state()["latest_backup"] is None
def test_t08_history_real_only(): assert [x["snapshot"] for x in state()["history"]] == ["S001"]
def test_t09_history_required(): assert state()["history"][0]["status"] == "REQUIRED"
def test_t10_checklist_eight(): assert len(state()["checklist"]) == 8
def test_t11_version_data_true(): assert next(x for x in state()["checklist"] if x["key"] == "version_data")["ok"] is True
def test_t12_active_prompts_false(): assert next(x for x in state()["checklist"] if x["key"] == "active_prompts")["ok"] is False
def test_t13_revisions_false(): assert next(x for x in state()["checklist"] if x["key"] == "revisions")["ok"] is False
def test_t14_full_backup_false(): assert next(x for x in state()["checklist"] if x["key"] == "full_backup")["ok"] is False
def test_t15_sha_false(): assert next(x for x in state()["checklist"] if x["key"] == "sha256")["ok"] is False
def test_t16_verify_false(): assert next(x for x in state()["checklist"] if x["key"] == "zip_verified")["ok"] is False
def test_t17_second_copy_false(): assert next(x for x in state()["checklist"] if x["key"] == "second_copy")["ok"] is False
def test_t18_download_disabled(): assert state()["actions"]["can_download_backup"] is False
def test_t19_sha_download_disabled(): assert state()["actions"]["can_download_sha256"] is False
def test_t20_verify_disabled(): assert state()["actions"]["can_verify_backup"] is False
def test_t21_folder_disabled(): assert state()["actions"]["can_open_folder"] is False
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

def test_t45_baseline_unchanged():
    assert digest(ROOT / "BASELINE.json") == "8ffd22fe3636309ce0484f8b724f9fe306f3156383c5f4efbcc7e59f79e90b6d"

def test_t46_canonical_unchanged():
    assert digest(CANONICAL) == "1a0fddf98b000bb908e12e5aa617b42793a399a8dd9cb36e1acf7204ca8465bb"
