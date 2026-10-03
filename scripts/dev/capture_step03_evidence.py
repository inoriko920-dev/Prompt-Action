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

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest


ROUTES = [
    ("dashboard", "1600x900_100_dashboard-shell.png"),
    ("system_history", "1600x900_100_history-shell.png"),
    ("prompt", "1600x900_100_prompt-shell.png"),
    ("backup", "1600x900_100_backup-shell.png"),
    ("settings", "1600x900_100_settings-shell.png"),
]
GALLERIES = [
    ("buttons", "buttons_states.png"),
    ("inputs", "inputs_states.png"),
    ("nav", "nav_states.png"),
    ("status", "status_badges.png"),
]


def load_window(path: Path, app: QGuiApplication):
    warnings: list[str] = []
    engine = QQmlApplicationEngine()
    engine.warnings.connect(lambda items: warnings.extend(str(item) for item in items))
    engine.load(QUrl.fromLocalFile(str(path.resolve())))
    if not engine.rootObjects():
        raise RuntimeError(f"QML root failed: {path}\n" + "\n".join(warnings))
    window = engine.rootObjects()[0]
    QTest.qWait(100)
    app.processEvents()
    if warnings:
        raise RuntimeError("QML warnings: " + " | ".join(warnings))
    return engine, window, warnings


def save_window(window, path: Path, app: QGuiApplication, width: int, height: int) -> dict[str, object]:
    window.setProperty("width", width)
    window.setProperty("height", height)
    QTest.qWait(120)
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
    parser.add_argument("--output", type=Path, default=Path("evidence/step03/generated"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output = (root / args.output).resolve() if not args.output.is_absolute() else args.output.resolve()
    screenshots = output / "screenshots"
    components = output / "components"
    refs = output / "master_refs"
    refs.mkdir(parents=True, exist_ok=True)

    QQuickWindow.setSceneGraphBackend("software")
    app = QGuiApplication.instance() or QGuiApplication([sys.argv[0]])
    capture: dict[str, object] = {"routes": [], "components": [], "warnings": []}

    app_qml = root / "src/prompt_action/ui/qml/App.qml"
    engine, window, _ = load_window(app_qml, app)
    for route, filename in ROUTES:
        window.setProperty("currentRoute", route)
        QTest.qWait(70)
        capture["routes"].append(save_window(window, screenshots / filename, app, 1600, 900))
    window.close()
    engine.deleteLater()
    app.processEvents()

    gallery_qml = root / "tests/step03/qml/ComponentGallery.qml"
    gallery_engine, gallery, _ = load_window(gallery_qml, app)
    for mode, filename in GALLERIES:
        gallery.setProperty("galleryMode", mode)
        QTest.qWait(70)
        capture["components"].append(save_window(gallery, components / filename, app, 1000, 640))
    gallery.close()
    gallery_engine.deleteLater()
    app.processEvents()

    master_dir = root / "docs/UI_REFERENCE_PACKAGE_V1/materialized/images"
    for source in sorted(master_dir.glob("*.jpg")):
        shutil.copy2(source, refs / source.name)

    output.mkdir(parents=True, exist_ok=True)
    (output / "capture.json").write_text(json.dumps(capture, indent=2) + "\n", encoding="utf-8")
    (output / "visual_review.md").write_text(
        "# STEP 03 Visual Review\n\nAutomated capture complete. Human visual review is required before merge.\n\n"
        "Classification vocabulary: `expected technical adaptation`, `defect`, `deferred`.\n",
        encoding="utf-8",
    )
    print(json.dumps(capture, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
