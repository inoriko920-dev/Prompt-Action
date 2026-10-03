from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

from prompt_action.settings.defaults import default_settings
from prompt_action.settings.models import AppSettings
from prompt_action.settings.repository import SettingsRepository, SettingsWriteError
from prompt_action.settings.sanitization import sanitize_text, sanitize_value
from prompt_action.settings.validator import PathStatus, normalize_for_storage, validate_settings
from prompt_action.ui.viewmodels.settings_view_model import SettingsViewModel

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "BASELINE.json"
CANONICAL = ROOT / "data/version_history.json"
SETTINGS_QML = ROOT / "src/prompt_action/ui/qml/pages/SettingsPage.qml"
CONTENT_HOST = ROOT / "src/prompt_action/ui/qml/shell/ContentHost.qml"
MASTER = ROOT / "docs/UI_REFERENCE_PACKAGE_V1/materialized/images/05-Pengaturan.jpg"


def digest(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

def make_project(tmp_path: Path) -> Path:
    root = tmp_path / "Prompt Action Ω"; root.mkdir()
    for name in ("prompts","backups","backups-second-copy"): (root/name).mkdir()
    (root/"runtime"/"temp").mkdir(parents=True); (root/"runtime"/"logs").mkdir(parents=True)
    return root

def settings_for(root: Path) -> AppSettings: return default_settings(root)


def test_t01_route_pengaturan_can_open():
    assert "Pages.SettingsPage" in CONTENT_HOST.read_text(encoding="utf-8") and 'objectName: "settingsPage"' in SETTINGS_QML.read_text(encoding="utf-8")

def test_t02_master_visual_parity_basic():
    text=SETTINGS_QML.read_text(encoding="utf-8"); assert MASTER.is_file() and "GridLayout" in text and "Simpan Pengaturan" in text

def test_t03_sections_visible():
    text=SETTINGS_QML.read_text(encoding="utf-8")
    for label in ("Umum","Backup","GitHub","Tampilan","Advanced"): assert f'title: "{label}"' in text or f'title:"{label}"' in text

def test_t04_persisted_settings_load(tmp_path):
    root=make_project(tmp_path); repo=SettingsRepository(root); s=settings_for(root); s.github.branch="develop"; repo.save(s); loaded=repo.load(); assert loaded.source=="persisted" and loaded.settings.github.branch=="develop"

def test_t05_draft_equals_persisted_on_open(tmp_path):
    vm=SettingsViewModel(make_project(tmp_path)); assert vm.state["draft_settings"]==vm.state["persisted_settings"]

def test_t06_edit_field_sets_dirty(tmp_path):
    vm=SettingsViewModel(make_project(tmp_path)); vm.updateField("github","branch","feature/settings"); assert vm.state["is_dirty"] is True

def test_t07_revert_discards_draft(tmp_path):
    vm=SettingsViewModel(make_project(tmp_path)); vm.updateField("github","branch","feature/settings"); vm.revertSettings(); assert vm.state["is_dirty"] is False and vm.state["draft_settings"]["github"]["branch"]=="main"

def test_t08_save_valid_writes_once(tmp_path):
    import os
    root=make_project(tmp_path); calls=[]
    def replace(src,dst): calls.append(1); os.replace(src,dst)
    vm=SettingsViewModel(root, repository=SettingsRepository(root,replace_func=replace)); vm.updateField("github","branch","develop"); vm.saveSettings(); assert len(calls)==1 and vm.state["save_state"]=="SUCCESS"

def test_t09_double_click_save_no_double_write(tmp_path):
    import os
    root=make_project(tmp_path); calls=[]
    def replace(src,dst): calls.append(1); os.replace(src,dst)
    vm=SettingsViewModel(root, repository=SettingsRepository(root,replace_func=replace)); vm.updateField("github","branch","develop"); vm.saveSettings(); vm.saveSettings(); assert len(calls)==1

def test_t10_atomic_replace_success(tmp_path):
    root=make_project(tmp_path); repo=SettingsRepository(root); s=settings_for(root); s.github.branch="release/v1"; saved=repo.save(s); raw=json.loads(repo.settings_path.read_text()); assert raw["github"]["branch"]=="release/v1" and saved.github.branch=="release/v1"

def test_t11_atomic_failure_preserves_old_file(tmp_path):
    root=make_project(tmp_path); good=SettingsRepository(root); s=settings_for(root); good.save(s); before=good.settings_path.read_bytes()
    def fail(src,dst): raise OSError("simulated")
    broken=SettingsRepository(root,replace_func=fail); s.github.branch="broken"
    with pytest.raises(SettingsWriteError): broken.save(s)
    assert good.settings_path.read_bytes()==before

def test_t12_parse_error_safe_handling(tmp_path):
    root=make_project(tmp_path); repo=SettingsRepository(root); repo.settings_dir.mkdir(parents=True); repo.settings_path.write_text("{broken"); loaded=repo.load(); assert loaded.degraded and loaded.source=="safe_defaults" and repo.settings_path.read_text()=="{broken"

def test_t13_schema_version_supported(tmp_path): assert validate_settings(settings_for(make_project(tmp_path)),make_project(tmp_path)).valid is True

def test_t14_unknown_field_forward_tolerant(tmp_path):
    root=make_project(tmp_path); raw=settings_for(root).to_dict(); raw["future_section"]={"x":1}; raw["github"]["future_value"]="x"; s=AppSettings.from_dict(raw); assert s.github.repository=="inoriko920-dev/Prompt-Action" and "future_section" not in s.to_dict()

def test_t15_missing_settings_uses_safe_defaults(tmp_path):
    loaded=SettingsRepository(make_project(tmp_path)).load(); assert loaded.source=="defaults" and loaded.settings.appearance.theme=="light_blue"

def test_t16_root_path_with_spaces(tmp_path):
    root=make_project(tmp_path); s=settings_for(root); s.general.root_dir=str(root); assert not any(e["field"]=="general.root_dir" for e in validate_settings(s,root).errors)

def test_t17_unicode_path(tmp_path):
    root=make_project(tmp_path); d=root/"data Ω 漢字"; d.mkdir(); s=settings_for(root); s.general.root_dir=str(d); assert not any(e["field"]=="general.root_dir" for e in validate_settings(s,root).errors)

def test_t18_prompts_dir_unreadable_blocked(tmp_path):
    root=make_project(tmp_path); target=(root/"prompts").resolve()
    def probe(path): return PathStatus(True,True,False,False) if path==target else PathStatus(True,True,True,True)
    assert any(e["code"]=="not_readable" for e in validate_settings(settings_for(root),root,path_probe=probe).errors)

def test_t19_backup_dir_nonwritable_blocked(tmp_path):
    root=make_project(tmp_path); target=(root/"backups").resolve()
    def probe(path): return PathStatus(True,True,True,False) if path==target else PathStatus(True,True,True,True)
    assert any(e["field"]=="general.backup_dir" and e["code"]=="not_writable" for e in validate_settings(settings_for(root),root,path_probe=probe).errors)

def test_t20_second_copy_same_as_primary_blocked(tmp_path):
    root=make_project(tmp_path); s=settings_for(root); s.backup.second_copy_dir="backups"; assert any(e["code"]=="second_copy_same_as_primary" for e in validate_settings(s,root).errors)

def test_t21_external_path_normalize(tmp_path):
    root=make_project(tmp_path); external=tmp_path/"External"; external.mkdir(); assert normalize_for_storage(str(external),root)==str(external.resolve())

def test_t22_internal_path_relative_portability(tmp_path):
    root=make_project(tmp_path); assert normalize_for_storage(str(root/"backups"),root)=="backups"

def test_t23_folder_picker_cancel_no_mutation(tmp_path):
    vm=SettingsViewModel(make_project(tmp_path)); before=vm.state["draft_settings"]; vm.selectFolder("backup_dir",""); assert vm.state["draft_settings"]==before and vm.state["is_dirty"] is False

def test_t24_folder_picker_update_draft_only(tmp_path):
    root=make_project(tmp_path); selected=root/"backup selected"; selected.mkdir(); vm=SettingsViewModel(root); vm.selectFolder("backup_dir",str(selected)); assert vm.state["is_dirty"] and not (root/"runtime/settings/settings.json").exists()

def test_t25_backup_policy_toggle_draft_only(tmp_path):
    root=make_project(tmp_path); vm=SettingsViewModel(root); vm.updateField("backup","backup_on_release",False); assert vm.state["draft_settings"]["backup"]["backup_on_release"] is False and not (root/"runtime/settings/settings.json").exists()

def test_t26_sha_verify_locked_on(tmp_path):
    vm=SettingsViewModel(make_project(tmp_path)); vm.updateField("backup","write_sha256",False); vm.updateField("backup","verify_after_write",False); b=vm.state["draft_settings"]["backup"]; assert b["write_sha256"] and b["verify_after_write"]

def test_t27_second_copy_enabled_requires_path(tmp_path):
    root=make_project(tmp_path); s=settings_for(root); s.backup.second_copy_dir=""; assert any(e["code"]=="second_copy_missing" for e in validate_settings(s,root).errors)

def test_t28_github_repo_format_valid(tmp_path):
    root=make_project(tmp_path); assert not any(e["field"]=="github.repository" for e in validate_settings(settings_for(root),root).errors)

def test_t29_github_repo_malformed_blocked(tmp_path):
    root=make_project(tmp_path); s=settings_for(root); s.github.repository="https://github.com/owner/repo"; assert any(e["code"]=="invalid_repository" for e in validate_settings(s,root).errors)

def test_t30_branch_empty_blocked(tmp_path):
    root=make_project(tmp_path); s=settings_for(root); s.github.branch=""; assert any(e["code"]=="invalid_branch" for e in validate_settings(s,root).errors)

def test_t31_open_repository_safe_url(tmp_path):
    vm=SettingsViewModel(make_project(tmp_path)); assert vm.state["repository_url"]=="https://github.com/inoriko920-dev/Prompt-Action" and vm.state["github_capability"]["can_open_repository"]

def test_t32_connection_capability_unavailable_honest(tmp_path):
    cap=SettingsViewModel(make_project(tmp_path)).state["github_capability"]; assert not cap["test_available"] and not cap["connected"] and cap["status"]=="UNAVAILABLE"

def test_t33_connection_success_only_real_service(tmp_path):
    vm=SettingsViewModel(make_project(tmp_path)); vm.testGitHubConnection(); assert not vm.state["github_capability"]["connected"] and "STEP 13" in vm.state["status_message"]

def test_t34_no_token_in_settings_file(tmp_path):
    root=make_project(tmp_path); raw=settings_for(root).to_dict(); raw["github"]["token"]="ghp_123456789012345678901234567890"; repo=SettingsRepository(root); repo.save(AppSettings.from_dict(raw)); text=repo.settings_path.read_text().lower(); assert "ghp_" not in text and '"token"' not in text and "password" not in text

def test_t35_no_token_in_logs_sanitizer():
    clean=sanitize_text("Authorization: Bearer ghp_123456789012345678901234567890"); assert "ghp_" not in clean and "Bearer" not in clean

def test_t36_light_theme_selected_locked(tmp_path):
    vm=SettingsViewModel(make_project(tmp_path)); vm.updateField("appearance","theme","dark"); assert vm.state["draft_settings"]["appearance"]["theme"]=="light_blue" and vm.state["theme_locked"]

def test_t37_ui_scale_valid_values(tmp_path):
    root=make_project(tmp_path)
    for value in (100,110,125):
        s=settings_for(root); s.appearance.ui_scale=value; assert not any(e["field"]=="appearance.ui_scale" for e in validate_settings(s,root).errors)

def test_t38_ui_scale_invalid_explicit_reject(tmp_path):
    root=make_project(tmp_path); s=settings_for(root); s.appearance.ui_scale=250; assert any(e["code"]=="invalid_ui_scale" for e in validate_settings(s,root).errors)

def test_t39_restart_required_indicator(tmp_path):
    vm=SettingsViewModel(make_project(tmp_path)); vm.updateField("appearance","ui_scale",110); assert vm.state["restart_required"]

def test_t40_tree_density_modes(tmp_path):
    root=make_project(tmp_path)
    for value in ("comfortable","compact"):
        s=settings_for(root); s.appearance.tree_density=value; assert not any(e["field"]=="appearance.tree_density" for e in validate_settings(s,root).errors)

def test_t41_reset_layout_affects_layout_only(tmp_path):
    vm=SettingsViewModel(make_project(tmp_path)); repo=vm.state["draft_settings"]["github"]["repository"]; vm.updateField("appearance","ui_scale",125); vm.updateField("appearance","tree_density","compact"); vm.resetLayout(True); d=vm.state["draft_settings"]; assert d["appearance"]["ui_scale"]==100 and d["appearance"]["tree_density"]=="comfortable" and d["github"]["repository"]==repo

def test_t42_reset_layout_requires_confirmation(tmp_path):
    vm=SettingsViewModel(make_project(tmp_path)); vm.updateField("appearance","ui_scale",125); vm.resetLayout(False); assert vm.state["draft_settings"]["appearance"]["ui_scale"]==125

def test_t43_open_log_missing_handles_without_crash(tmp_path):
    root=make_project(tmp_path); (root/"runtime/logs").rmdir(); vm=SettingsViewModel(root); vm.openLogFolder(); assert "belum tersedia" in vm.state["status_message"].lower()

def test_t44_export_diagnostics_generated(tmp_path):
    vm=SettingsViewModel(make_project(tmp_path)); vm.exportDiagnostics(); path=Path(vm.state["last_export_path"]); assert path.is_file() and "PromptAction-Diagnostics-" in path.name

def test_t45_diagnostics_sanitizer_removes_secret(tmp_path):
    root=make_project(tmp_path); clean=sanitize_value({"token":"ghp_123456789012345678901234567890","nested":{"password":"secret-value"},"path":str(root/"private")},project_root=root); dumped=json.dumps(clean); assert "ghp_" not in dumped and "secret-value" not in dumped and "<PROJECT_ROOT>" in dumped

def test_t46_responsive_capture_contract():
    text=(ROOT/"scripts/dev/capture_step08_evidence.py").read_text()
    for dims in ("1600, 900","1920, 1080","1366, 768"): assert dims in text

def test_t47_dpi_contract():
    text=(ROOT/".github/workflows/ci-step08.yml").read_text(); assert "100;125;150;175" in text and "STEP08_DPI" in text

def test_t48_keyboard_focus_tab_order_contract():
    text=SETTINGS_QML.read_text(); component=(ROOT/"src/prompt_action/ui/qml/settings/SettingsToggleRow.qml").read_text(); assert "focusPolicy: Qt.StrongFocus" in text and "activeFocusOnTab: true" in component

def test_t49_no_regression_pages_present():
    for name in ("DashboardPage.qml","SystemHistoryPage.qml","PerPromptPage.qml","BackupRecoveryPage.qml"): assert (ROOT/"src/prompt_action/ui/qml/pages"/name).is_file()

def test_t50_protected_canonical_prompt_files_unchanged():
    assert digest(BASELINE)=="8ffd22fe3636309ce0484f8b724f9fe306f3156383c5f4efbcc7e59f79e90b6d" and digest(CANONICAL)=="1a0fddf98b000bb908e12e5aa617b42793a399a8dd9cb36e1acf7204ca8465bb"
