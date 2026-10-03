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

from prompt_action.presentation.dashboard_models import DashboardState
from prompt_action.presentation.dashboard_view_model import DashboardViewModel


def capture(window, app, path: Path, width: int, height: int) -> dict[str, object]:
    window.setProperty("width", width)
    window.setProperty("height", height)
    QTest.qWait(140)
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
    parser.add_argument("--output", type=Path, default=Path("ci-step04-evidence"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output = (root / args.output).resolve() if not args.output.is_absolute() else args.output.resolve()
    screenshots = output / "screenshots"
    refs = output / "master_refs"

    QQuickWindow.setSceneGraphBackend("software")
    app = QGuiApplication.instance() or QGuiApplication([sys.argv[0]])
    vm = DashboardViewModel(root)
    warnings: list[str] = []
    engine = QQmlApplicationEngine()
    vm.setParent(engine)
    engine.rootContext().setContextProperty("dashboardViewModel", vm)
    engine.warnings.connect(lambda items: warnings.extend(str(item) for item in items))
    engine.load(QUrl.fromLocalFile(str((root / "src/prompt_action/ui/qml/App.qml").resolve())))
    if not engine.rootObjects():
        raise RuntimeError("Dashboard App.qml failed to load: " + " | ".join(warnings))
    window = engine.rootObjects()[0]
    window.setProperty("currentRoute", "dashboard")
    QTest.qWait(150)
    app.processEvents()
    page = window.findChild(QObject, "dashboardPage")
    if page is None:
        raise RuntimeError("dashboardPage object not found")
    if warnings:
        raise RuntimeError("QML warnings: " + " | ".join(warnings))

    result: dict[str, object] = {"screenshots": [], "warnings": warnings, "canonical_state": vm.state}
    actual = vm.state
    page.setProperty("stateOverride", actual)
    for filename, width, height in [
        ("dashboard-1600x900.png", 1600, 900),
        ("dashboard-1920x1080.png", 1920, 1080),
        ("dashboard-1366x768.png", 1366, 768),
        ("dashboard-backup-required.png", 1600, 900),
    ]:
        result["screenshots"].append(capture(window, app, screenshots / filename, width, height))

    page.setProperty("stateOverride", DashboardState.loading().to_dict())
    result["screenshots"].append(capture(window, app, screenshots / "dashboard-loading.png", 1600, 900))

    invalid = DashboardState.invalid(["TEST-EVIDENCE: canonical data invalid untuk visual state."]).to_dict()
    page.setProperty("stateOverride", invalid)
    result["screenshots"].append(capture(window, app, screenshots / "dashboard-invalid.png", 1600, 900))

    refs.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / "docs/UI_REFERENCE_PACKAGE_V1/materialized/images/01-Dashboard.jpg", refs / "01-Dashboard.jpg")
    output.mkdir(parents=True, exist_ok=True)
    (output / "capture.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    window.close()
    engine.deleteLater()
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
