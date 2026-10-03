from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=900)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
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
        print(json.dumps({"valid": False, "warnings": warnings, "reason": "root-load"}))
        return 2
    window = engine.rootObjects()[0]
    window.setProperty("width", args.width)
    window.setProperty("height", args.height)
    window.setProperty("currentRoute", "dashboard")
    QTest.qWait(120)
    app.processEvents()
    page = window.findChild(QObject, "dashboardPage")
    host = window.findChild(QObject, "contentHost")
    state = vm.state
    result = {
        "valid": page is not None and host is not None and not warnings,
        "warnings": warnings,
        "width": window.property("width"),
        "height": window.property("height"),
        "page_width": page.property("width") if page else None,
        "page_height": page.property("height") if page else None,
        "host_width": host.property("width") if host else None,
        "host_height": host.property("height") if host else None,
        "scale_factor": os.environ.get("QT_SCALE_FACTOR", "1"),
        "state": state,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["valid"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
