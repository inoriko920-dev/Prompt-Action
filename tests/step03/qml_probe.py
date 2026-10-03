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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qml", type=Path, required=True)
    parser.add_argument("--width", type=int, default=1180)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--route", default="dashboard")
    args = parser.parse_args()

    QQuickWindow.setSceneGraphBackend("software")
    app = QGuiApplication.instance() or QGuiApplication([sys.argv[0]])
    warnings: list[str] = []
    engine = QQmlApplicationEngine()
    engine.warnings.connect(lambda items: warnings.extend(str(item) for item in items))
    engine.load(QUrl.fromLocalFile(str(args.qml.resolve())))
    if not engine.rootObjects():
        print(json.dumps({"valid": False, "warnings": warnings, "error": "root-load-failed"}))
        return 2

    window = engine.rootObjects()[0]
    window.setProperty("width", args.width)
    window.setProperty("height", args.height)
    window.setProperty("currentRoute", args.route)
    QTest.qWait(80)
    app.processEvents()

    sidebar = window.findChild(QObject, "sidebar")
    topbar = window.findChild(QObject, "topbar")
    host = window.findChild(QObject, "contentHost")
    result = {
        "valid": not warnings and sidebar is not None and topbar is not None and host is not None,
        "warnings": warnings,
        "width": window.property("width"),
        "height": window.property("height"),
        "route": window.property("currentRoute"),
        "scale_factor": os.environ.get("QT_SCALE_FACTOR", "1"),
        "sidebar_width": sidebar.property("width") if sidebar else None,
        "topbar_height": topbar.property("height") if topbar else None,
        "content_width": host.property("width") if host else None,
        "content_height": host.property("height") if host else None,
        "page_title": topbar.property("pageTitle") if topbar else None,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["valid"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
