from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QSG_RHI_BACKEND", "software")
os.environ.setdefault("QSG_RENDER_LOOP", "basic")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from prompt_action.presentation.dashboard_view_model import DashboardViewModel
from prompt_action.presentation.history_view_model import SystemHistoryViewModel
from prompt_action.presentation.per_prompt_view_model import PerPromptViewModel


def capture(window, app, path: Path, width: int, height: int) -> dict[str, object]:
    window.setProperty("width", width)
    window.setProperty("height", height)
    QTest.qWait(160)
    app.processEvents()
    image = window.grabWindow()
    if image.isNull():
        raise RuntimeError(f"grabWindow returned null for {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(path)):
        raise RuntimeError(f"Failed to save {path}")
    return {"file": path.name, "width": image.width(), "height": image.height(), "bytes": path.stat().st_size}


def base_state(load_state: str, diagnostics: list[str] | None = None) -> dict[str, object]:
    return {"load_state":load_state,"prompts":[],"selected_prompt_id":"","selected_prompt_name":"","active_revision_id":"","selected_revision_id":"","official_revisions":[],"drafts":[],"selected_revision":{},"available_files":[],"capabilities":{},"issues":[],"diagnostics":diagnostics or []}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("ci-step06-evidence"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output = (root / args.output).resolve() if not args.output.is_absolute() else args.output.resolve()
    screenshots = output / "screenshots"
    refs = output / "master_refs"

    QQuickWindow.setSceneGraphBackend("software")
    app = QGuiApplication.instance() or QGuiApplication([sys.argv[0]])
    dashboard_vm = DashboardViewModel(root)
    history_vm = SystemHistoryViewModel(root)
    per_prompt_vm = PerPromptViewModel(root)
    warnings: list[str] = []
    engine = QQmlApplicationEngine()
    for vm in (dashboard_vm, history_vm, per_prompt_vm):
        vm.setParent(engine)
    engine.rootContext().setContextProperty("dashboardViewModel", dashboard_vm)
    engine.rootContext().setContextProperty("historyViewModel", history_vm)
    engine.rootContext().setContextProperty("perPromptViewModel", per_prompt_vm)
    engine.warnings.connect(lambda items: warnings.extend(str(item) for item in items))
    engine.load(QUrl.fromLocalFile(str((root / "src/prompt_action/ui/qml/App.qml").resolve())))
    if not engine.rootObjects():
        raise RuntimeError("App.qml failed to load: " + " | ".join(warnings))
    window = engine.rootObjects()[0]
    window.setProperty("currentRoute", "prompt")
    QTest.qWait(180)
    app.processEvents()
    page = window.findChild(QObject, "perPromptPage")
    if page is None:
        raise RuntimeError("perPromptPage object not found")
    if warnings:
        raise RuntimeError("QML warnings: " + " | ".join(warnings))

    result: dict[str, object] = {"screenshots": [], "warnings": warnings, "canonical_state": per_prompt_vm.state}
    for filename, width, height in [("per-prompt-1600x900.png", 1600, 900), ("per-prompt-1920x1080.png", 1920, 1080), ("per-prompt-1366x768.png", 1366, 768)]:
        result["screenshots"].append(capture(window, app, screenshots / filename, width, height))

    page.setProperty("stateOverride", base_state("loading"))
    result["screenshots"].append(capture(window, app, screenshots / "per-prompt-loading.png", 1600, 900))
    page.setProperty("stateOverride", base_state("invalid", ["TEST-EVIDENCE: revision graph invalid"]))
    result["screenshots"].append(capture(window, app, screenshots / "per-prompt-invalid.png", 1600, 900))
    degraded = dict(per_prompt_vm.state)
    degraded["load_state"] = "degraded"
    degraded["issues"] = [{"code":"INV-10","message":"TEST-EVIDENCE: file missing"}]
    page.setProperty("stateOverride", degraded)
    result["screenshots"].append(capture(window, app, screenshots / "per-prompt-degraded.png", 1600, 900))
    if warnings:
        raise RuntimeError("QML warnings after evidence states: " + " | ".join(warnings))

    refs.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / "docs/UI_REFERENCE_PACKAGE_V1/materialized/images/03-Per-Prompt.jpg", refs / "03-Per-Prompt.jpg")
    output.mkdir(parents=True, exist_ok=True)
    result["warnings"] = warnings
    (output / "capture.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    window.close()
    engine.deleteLater()
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
