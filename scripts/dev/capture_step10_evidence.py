from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QSG_RHI_BACKEND", "software")
os.environ.setdefault("QSG_RENDER_LOOP", "basic")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtQml import QQmlApplicationEngine

from prompt_action.bootstrap.qml_boot import create_application
from prompt_action.presentation.backup_view_model import BackupRecoveryViewModel
from prompt_action.presentation.dashboard_view_model import DashboardViewModel
from prompt_action.presentation.history_view_model import SystemHistoryViewModel
from prompt_action.presentation.per_prompt_view_model import PerPromptViewModel
from prompt_action.ui.viewmodels.release_wizard_view_model import ReleaseWizardViewModel
from prompt_action.ui.viewmodels.search_view_model import SearchViewModel
from prompt_action.ui.viewmodels.settings_view_model import SettingsViewModel


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def production_manifest(root: Path) -> dict[str, str]:
    paths = [root / "data/version_history.json"] + sorted((root / "prompts").rglob("*.txt"))
    return {str(path.relative_to(root)).replace("\\", "/"): digest(path) for path in paths}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="ci-step10-evidence")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    out = root / args.output
    screens = out / "screenshots"
    fixture = out / "runtime" / "release-fixture"
    settings_runtime = out / "runtime" / "settings-runtime"
    screens.mkdir(parents=True, exist_ok=True)
    if fixture.exists():
        shutil.rmtree(fixture)
    (fixture / "data").mkdir(parents=True)
    shutil.copy2(root / "data/version_history.json", fixture / "data/version_history.json")
    shutil.copytree(root / "prompts", fixture / "prompts")

    before = production_manifest(root)
    fixture_doc = json.loads((fixture / "data/version_history.json").read_text(encoding="utf-8"))
    active = fixture_doc["prompts"]["P3"]["active_revision"]
    active_rel = fixture_doc["prompts"]["P3"]["revisions"][active]["file"]
    candidate = fixture / "incoming" / "P3-step10-evidence.txt"
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes((fixture / active_rel).read_bytes() + b"\n# STEP 10 UI evidence candidate\n")

    app = create_application(["step10-capture"])
    dashboard_vm = DashboardViewModel(fixture)
    history_vm = SystemHistoryViewModel(fixture)
    per_prompt_vm = PerPromptViewModel(fixture)
    backup_vm = BackupRecoveryViewModel(fixture)
    settings_vm = SettingsViewModel(fixture, runtime_root=settings_runtime)
    search_vm = SearchViewModel(fixture)
    release_vm = ReleaseWizardViewModel(fixture)
    qml = root / "src/prompt_action/ui/qml/App.qml"
    warnings: list[str] = []
    engine = QQmlApplicationEngine()
    engine.warnings.connect(lambda items: warnings.extend(str(item.toString()) for item in items))
    for vm in (dashboard_vm, history_vm, per_prompt_vm, backup_vm, settings_vm, search_vm, release_vm):
        vm.setParent(engine)
    context = engine.rootContext()
    context.setContextProperty("dashboardViewModel", dashboard_vm)
    context.setContextProperty("historyViewModel", history_vm)
    context.setContextProperty("perPromptViewModel", per_prompt_vm)
    context.setContextProperty("backupViewModel", backup_vm)
    context.setContextProperty("settingsViewModel", settings_vm)
    context.setContextProperty("searchViewModel", search_vm)
    context.setContextProperty("releaseWizardViewModel", release_vm)
    engine.load(QUrl.fromLocalFile(str(qml.resolve())))
    QCoreApplication.processEvents()
    if not engine.rootObjects():
        raise RuntimeError("QML root failed to load")
    window = engine.rootObjects()[0]
    window.setWidth(1600)
    window.setHeight(900)
    window.setProperty("currentRoute", "prompt")
    QCoreApplication.processEvents()
    screen = app.primaryScreen()
    if screen is None:
        raise RuntimeError("No primary screen available")
    captured: list[dict[str, object]] = []

    def pump(rounds: int = 6) -> None:
        for _ in range(rounds):
            QCoreApplication.processEvents()
            time.sleep(0.02)

    def snap(name: str) -> None:
        pump()
        image = screen.grabWindow(int(window.winId()), 0, 0, 1600, 900).toImage()
        path = screens / f"{name}.png"
        if image.isNull() or not image.save(str(path)):
            raise RuntimeError(f"Screenshot failed: {name}")
        captured.append({"file": path.name, "width": image.width(), "height": image.height(), "bytes": path.stat().st_size})

    release_vm.openForPrompt("P3")
    pump()
    snap("01-add-revision-input")

    release_vm.setPrimarySource(str(candidate))
    release_vm.setSummary("STEP 10 visual evidence — update Prompt 3")
    release_vm.setReason("Evidence fixture untuk memverifikasi Release Wizard tanpa mengubah corpus produksi")
    release_vm.planRelease()
    if release_vm.state["stage"] != "review":
        raise RuntimeError(f"Wizard failed to reach review: {release_vm.state}")
    snap("02-release-review")

    release_vm.commitRelease()
    for _ in range(100):
        pump(1)
        if release_vm.state["stage"] != "committing":
            break
    if release_vm.state["stage"] != "success":
        raise RuntimeError(f"Fixture release failed: {release_vm.state}")
    snap("03-release-result-backup-required")

    committed = json.loads((fixture / "data/version_history.json").read_text(encoding="utf-8"))
    snapshot = next(item for item in committed["snapshots"] if item["id"] == "S002")
    proof = {
        "fixture_only": True,
        "snapshot_id": committed["active_snapshot"],
        "snapshot_status": snapshot["status"],
        "backup_id": snapshot["backup_id"],
        "p3_active_revision": committed["prompts"]["P3"]["active_revision"],
        "app_data_revision": committed["app_data_revision"],
        "production_unchanged": before == production_manifest(root),
        "screenshots": captured,
        "qml_warnings": warnings,
    }
    (out / "ui-release-proof.json").write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(proof, ensure_ascii=False, indent=2))

    if proof["snapshot_id"] != "S002" or proof["p3_active_revision"] != "R2":
        raise RuntimeError("Fixture did not produce deterministic S002/R2")
    if proof["snapshot_status"] != "BACKUP_REQUIRED" or proof["backup_id"] is not None:
        raise RuntimeError("STEP 10 fixture snapshot must be BACKUP_REQUIRED with no backup")
    if not proof["production_unchanged"]:
        raise RuntimeError("Visual evidence capture mutated production corpus")
    if warnings:
        raise RuntimeError("QML warnings: " + " | ".join(warnings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
