from __future__ import annotations

from pathlib import Path

from prompt_action.presentation.per_prompt_view_model import PerPromptViewModel
from prompt_action.ui.viewmodels.release_wizard_view_model import ReleaseWizardViewModel


def test_ui01_per_prompt_enables_add_revision_on_complete_snapshot(project: Path):
    vm = PerPromptViewModel(project)
    assert vm.state["capabilities"]["can_add_revision"] is True


def test_ui02_wizard_opens_for_selected_prompt(project: Path):
    vm = ReleaseWizardViewModel(project)
    vm.openForPrompt("P3")
    assert vm.state["stage"] == "input"
    assert vm.state["primary_prompt_id"] == "P3"
    assert vm.state["primary_active_revision"] == "R1"
    assert vm.state["availability"]["can_start"] is True


def test_ui03_wizard_plans_s002_r2_without_mutating_canonical(project: Path, changed_p3: Path):
    before = (project / "data/version_history.json").read_bytes()
    vm = ReleaseWizardViewModel(project)
    vm.openForPrompt("P3")
    vm.setPrimarySource(str(changed_p3))
    vm.setReason("UI fixture release")
    vm.setSummary("Update Prompt 3")
    vm.planRelease()
    assert vm.state["stage"] == "review"
    assert vm.state["plan"]["snapshot_id"] == "S002"
    assert vm.state["plan"]["primary"]["to_revision"] == "R2"
    assert (project / "data/version_history.json").read_bytes() == before


def test_ui04_wizard_optional_sync_is_in_review(project: Path, changed_p3: Path, changed_p4: Path):
    vm = ReleaseWizardViewModel(project)
    vm.openForPrompt("P3")
    vm.setPrimarySource(str(changed_p3))
    vm.setReason("Primary reason")
    vm.addSync("P4", str(changed_p4), "Compatibility sync")
    vm.planRelease()
    assert vm.state["stage"] == "review"
    assert [item["prompt_id"] for item in vm.state["plan"]["sync"]] == ["P4"]
    assert vm.state["plan"]["sync"][0]["to_revision"] == "R2"


def test_ui05_wizard_does_not_expose_prompt_text_editor(project: Path, repo_root: Path):
    qml = (repo_root / "src/prompt_action/ui/qml/dialogs/AddRevisionDialog.qml").read_text(encoding="utf-8")
    assert "Pilih TXT" in qml
    assert "Import TXT" in qml
    assert "prompt content" not in qml.lower()
    assert "sourceText" not in qml


def test_ui06_required_release_dialogs_exist(repo_root: Path):
    base = repo_root / "src/prompt_action/ui/qml/dialogs"
    names = {
        "AddRevisionDialog.qml",
        "ReleaseReviewDialog.qml",
        "ReleaseProgressDialog.qml",
        "ReleaseResultDialog.qml",
    }
    assert names <= {path.name for path in base.glob("*.qml")}


def test_ui07_shell_wires_release_view_model_and_refresh(repo_root: Path):
    shell = (repo_root / "src/prompt_action/ui/qml/shell/MainWindow.qml").read_text(encoding="utf-8")
    assert "releaseWizardViewModel" in shell
    assert "onAddRevisionRequested" in shell
    assert "refreshCanonicalViews" in shell
    assert "onReleaseCompleted" in shell


def test_ui08_topbar_reads_canonical_snapshot_and_backup_health(repo_root: Path):
    shell = (repo_root / "src/prompt_action/ui/qml/shell/MainWindow.qml").read_text(encoding="utf-8")
    topbar = (repo_root / "src/prompt_action/ui/qml/shell/TopBar.qml").read_text(encoding="utf-8")
    assert "dashboardState.snapshot_label" in shell
    assert "dashboardState.backup_health" in shell
    assert "backupLabel" in topbar and "backupTone" in topbar


def test_ui09_review_states_backup_required(repo_root: Path):
    review = (repo_root / "src/prompt_action/ui/qml/dialogs/ReleaseReviewDialog.qml").read_text(encoding="utf-8")
    result = (repo_root / "src/prompt_action/ui/qml/dialogs/ReleaseResultDialog.qml").read_text(encoding="utf-8")
    assert "BACKUP_REQUIRED" in review
    assert "BACKUP_REQUIRED" in result
    assert "STEP 11" in result


def test_ui10_main_registers_release_context(repo_root: Path):
    main = (repo_root / "src/prompt_action/main.py").read_text(encoding="utf-8")
    assert "ReleaseWizardViewModel" in main
    assert '"releaseWizardViewModel": release_wizard_vm' in main
