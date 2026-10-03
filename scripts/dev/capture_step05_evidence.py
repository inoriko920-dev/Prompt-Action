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


def capture(window, app, path: Path, width: int, height: int) -> dict[str, object]:
    window.setProperty("width", width)
    window.setProperty("height", height)
    QTest.qWait(150)
    app.processEvents()
    image = window.grabWindow()
    if image.isNull():
        raise RuntimeError(f"grabWindow returned null for {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(path)):
        raise RuntimeError(f"Failed to save {path}")
    return {"file": path.name, "width": image.width(), "height": image.height(), "bytes": path.stat().st_size}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("ci-step05-evidence"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output = (root / args.output).resolve() if not args.output.is_absolute() else args.output.resolve()
    screenshots = output / "screenshots"
    refs = output / "master_refs"

    QQuickWindow.setSceneGraphBackend("software")
    app = QGuiApplication.instance() or QGuiApplication([sys.argv[0]])
    dashboard_vm = DashboardViewModel(root)
    history_vm = SystemHistoryViewModel(root)
    warnings: list[str] = []
    engine = QQmlApplicationEngine()
    dashboard_vm.setParent(engine)
    history_vm.setParent(engine)
    engine.rootContext().setContextProperty("dashboardViewModel", dashboard_vm)
    engine.rootContext().setContextProperty("historyViewModel", history_vm)
    engine.warnings.connect(lambda items: warnings.extend(str(item) for item in items))
    engine.load(QUrl.fromLocalFile(str((root / "src/prompt_action/ui/qml/App.qml").resolve())))
    if not engine.rootObjects():
        raise RuntimeError("App.qml failed to load: " + " | ".join(warnings))
    window = engine.rootObjects()[0]
    window.setProperty("currentRoute", "system_history")
    QTest.qWait(180)
    app.processEvents()
    page = window.findChild(QObject, "systemHistoryPage")
    if page is None:
        raise RuntimeError("systemHistoryPage object not found")
    if warnings:
        raise RuntimeError("QML warnings: " + " | ".join(warnings))

    result: dict[str, object] = {"screenshots": [], "warnings": warnings, "canonical_state": history_vm.state}
    for filename, width, height in [("history-1600x900.png", 1600, 900), ("history-1920x1080.png", 1920, 1080), ("history-1366x768.png", 1366, 768)]:
        result["screenshots"].append(capture(window, app, screenshots / filename, width, height))

    fallback_legacy = {"available": False, "label": "", "verified": False}
    page.setProperty("stateOverride", {"load_state":"loading","legacy":fallback_legacy,"systems":[],"selected_snapshot_id":"","selected_snapshot":{},"diagnostics":[]})
    result["screenshots"].append(capture(window, app, screenshots / "history-loading.png", 1600, 900))
    page.setProperty("stateOverride", {"load_state":"invalid","legacy":fallback_legacy,"systems":[],"selected_snapshot_id":"","selected_snapshot":{},"diagnostics":["TEST-EVIDENCE: canonical invalid"]})
    result["screenshots"].append(capture(window, app, screenshots / "history-invalid.png", 1600, 900))

    if warnings:
        raise RuntimeError("QML warnings after state captures: " + " | ".join(warnings))

    refs.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / "docs/UI_REFERENCE_PACKAGE_V1/materialized/images/02-Sejarah-Sistem.jpg", refs / "02-Sejarah-Sistem.jpg")
    output.mkdir(parents=True, exist_ok=True)
    (output / "capture.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    window.close()
    engine.deleteLater()
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
