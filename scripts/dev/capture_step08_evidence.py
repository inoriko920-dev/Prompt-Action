from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QSG_RHI_BACKEND", "software")
os.environ.setdefault("QSG_RENDER_LOOP", "basic")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from prompt_action.bootstrap.qml_boot import create_application
from prompt_action.settings.sanitization import sanitize_value
from prompt_action.ui.viewmodels.settings_view_model import SettingsViewModel


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", default="ci-step08-evidence"); args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    out = root / args.output; screens = out / "screenshots"; runtime = out / "runtime"
    screens.mkdir(parents=True, exist_ok=True); runtime.mkdir(parents=True, exist_ok=True)
    app = create_application(["step08-capture"])
    vm = SettingsViewModel(root, runtime_root=runtime)
    qml = root / "src/prompt_action/ui/qml/App.qml"
    warnings: list[str] = []
    engine = QQmlApplicationEngine(); engine.warnings.connect(lambda items: warnings.extend(str(item.toString()) for item in items))
    vm.setParent(engine); engine.rootContext().setContextProperty("settingsViewModel", vm); engine.load(QUrl.fromLocalFile(str(qml.resolve())))
    QCoreApplication.processEvents()
    if not engine.rootObjects(): raise RuntimeError("QML root failed to load")
    window = engine.rootObjects()[0]; window.setProperty("currentRoute", "settings"); QCoreApplication.processEvents()
    screen = app.primaryScreen()
    if screen is None: raise RuntimeError("No primary screen available for capture")
    captured: list[dict[str, object]] = []

    def snap(name: str, width: int = 1600, height: int = 900) -> None:
        window.setWidth(width); window.setHeight(height); QCoreApplication.processEvents()
        image = screen.grabWindow(int(window.winId()), 0, 0, width, height).toImage()
        path = screens / f"{name}.png"
        if image.isNull() or not image.save(str(path)): raise RuntimeError(f"Screenshot failed: {name}")
        captured.append({"file":path.name,"width":image.width(),"height":image.height(),"bytes":path.stat().st_size})

    for width, height in [(1600, 900), (1920, 1080), (1366, 768)]: snap(f"settings-{width}x{height}", width, height)
    vm.updateField("github", "branch", "feature/settings-evidence"); snap("settings-dirty")
    vm.revertSettings(); backup_dir = vm.state["draft_settings"]["general"]["backup_dir"]; vm.updateField("backup", "second_copy_dir", backup_dir); snap("settings-invalid-path")
    vm.revertSettings(); vm.updateField("github", "branch", "settings-evidence"); vm.saveSettings(); snap("settings-save-success")
    settings_path = runtime / "settings" / "settings.json"; before = hashlib.sha256(settings_path.read_bytes()).hexdigest()
    def fail_replace(src, dst): raise OSError("simulated atomic replace failure")
    vm._repository._replace = fail_replace  # evidence-only failure injection
    vm.updateField("github", "branch", "settings-error"); vm.saveSettings(); snap("settings-save-error")
    after = hashlib.sha256(settings_path.read_bytes()).hexdigest()
    atomic = {"simulated":True,"save_state":vm.state["save_state"],"before_sha256":before,"after_sha256":after,"preserved":before==after}
    (out/"atomic-failure.json").write_text(json.dumps(atomic, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    vm.revertSettings(); snap("settings-github-unavailable"); vm.exportDiagnostics(); snap("settings-diagnostics-export")
    (out/"settings-example.json").write_text(json.dumps(sanitize_value(vm.state["persisted_settings"], project_root=root), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    scan_text = settings_path.read_text(encoding="utf-8")
    diag_dir = out / "runtime" / "diagnostics"
    diag_text = "\n".join(p.read_text(encoding="utf-8") for p in diag_dir.glob("*.json")) if diag_dir.exists() else ""
    lowered = (scan_text + "\n" + diag_text).lower()
    security = {"contains_ghp_token":"ghp_" in lowered,"contains_password_key":'"password"' in lowered,"contains_authorization_key":'"authorization"' in lowered}
    security["pass"] = not any(security.values())
    (out/"security-proof.json").write_text(json.dumps(security, indent=2)+"\n", encoding="utf-8")
    meta = {"screenshots":captured,"warnings":warnings,"state":sanitize_value(vm.state, project_root=root),"diagnostics_files":sorted(p.name for p in diag_dir.glob("*.json")) if diag_dir.exists() else []}
    (out/"capture.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    if not atomic["preserved"]: raise RuntimeError("Atomic failure simulation changed persisted settings")
    if not security["pass"]: raise RuntimeError("Secret-like material leaked into settings/diagnostics evidence")
    if warnings: raise RuntimeError("QML warnings: " + " | ".join(warnings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
