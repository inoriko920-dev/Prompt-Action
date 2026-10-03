from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QSG_RHI_BACKEND", "software")
os.environ.setdefault("QSG_RENDER_LOOP", "basic")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QObject, QCoreApplication, QMetaObject
from PySide6.QtTest import QTest

from prompt_action.bootstrap.qml_boot import create_application, load_qml
from prompt_action.services.step09 import GlobalSearchService
from prompt_action.ui.viewmodels.search_view_model import SearchViewModel


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="ci-step09-evidence")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    out = root / args.output
    screens = out / "screenshots"
    screens.mkdir(parents=True, exist_ok=True)
    app = create_application(["step09-capture"])
    screen = app.primaryScreen()
    if screen is None:
        raise RuntimeError("No primary screen available")
    qml = root / "src/prompt_action/ui/qml/App.qml"
    captured: list[dict] = []
    all_warnings: list[str] = []

    def load(search_vm: SearchViewModel):
        engine = load_qml(qml, {"searchViewModel": search_vm})
        warnings: list[str] = []
        engine.warnings.connect(lambda items: warnings.extend(str(item.toString()) for item in items))
        QTest.qWait(80)
        if not engine.rootObjects():
            raise RuntimeError("QML root failed")
        return engine, engine.rootObjects()[0], warnings

    def capture(window, name: str, width: int = 1600, height: int = 900):
        window.setWidth(width); window.setHeight(height); QTest.qWait(40)
        image = screen.grabWindow(int(window.winId()), 0, 0, width, height).toImage()
        path = screens / name
        if image.isNull() or not image.save(str(path)):
            raise RuntimeError(f"Screenshot failed: {name}")
        captured.append({"file":name,"width":image.width(),"height":image.height(),"bytes":path.stat().st_size})

    search_vm = SearchViewModel(root, debounce_ms=0)
    engine, window, warnings = load(search_vm)
    capture(window, "search-idle-1600x900.png")
    search_vm.setQuery("P3"); QTest.qWait(30); capture(window, "search-results-1600x900.png")
    search_vm.setQuery("tidak-ada-entitas-xyz"); QTest.qWait(30); capture(window, "search-empty-1600x900.png")
    search_vm.setQuery("P3"); QTest.qWait(30); capture(window, "search-results-1366x768.png", 1366, 768)

    revision_dialog = window.findChild(QObject, "compareRevisionDialog")
    if revision_dialog is None:
        raise RuntimeError("CompareRevisionDialog not found")
    revision_dialog.setProperty("compareData", {
        "status":"OK","prompt_id":"P3","left_revision":"R1","right_revision":"R2",
        "unified_diff":"--- P3-R1\n+++ P3-R2\n-beta\n+beta changed","eol_only":False,"whitespace_only":False,
    })
    QMetaObject.invokeMethod(revision_dialog, "open"); QTest.qWait(30); capture(window, "compare-revision-1600x900.png")
    QMetaObject.invokeMethod(revision_dialog, "close"); QTest.qWait(20)

    snapshot_dialog = window.findChild(QObject, "compareSnapshotDialog")
    if snapshot_dialog is None:
        raise RuntimeError("CompareSnapshotDialog not found")
    snapshot_dialog.setProperty("compareData", {
        "status":"OK","left_snapshot":"S001","right_snapshot":"S002","left_system":"V1","right_system":"V1",
        "cross_system_warning":False,"summary":"2 Prompt berubah, 6 tetap.",
        "changed":[{"prompt_id":"P3","from":"R1","to":"R2","role":"PRIMARY"},{"prompt_id":"P4","from":"R1","to":"R2","role":"SYNC"}],
    })
    QMetaObject.invokeMethod(snapshot_dialog, "open"); QTest.qWait(30); capture(window, "compare-snapshot-1600x900.png")
    QMetaObject.invokeMethod(snapshot_dialog, "close")
    all_warnings.extend(warnings)
    engine.deleteLater(); QCoreApplication.processEvents()

    error_vm = SearchViewModel(root, service=GlobalSearchService(root, document={"invalid": True}), debounce_ms=0)
    error_engine, error_window, error_warnings = load(error_vm)
    error_vm.setQuery("P3"); QTest.qWait(30); capture(error_window, "search-error-1600x900.png")
    all_warnings.extend(error_warnings)
    error_engine.deleteLater(); QCoreApplication.processEvents()

    meta = {
        "screenshots": captured,
        "warnings": all_warnings,
        "production_search_state": GlobalSearchService(root).search("P3").to_dict(),
        "production_truth": "Canonical baseline has no materialized Prompt revision files or backup records; compare/download remain honestly gated.",
    }
    (out / "capture.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    if all_warnings:
        raise RuntimeError("QML warnings: " + " | ".join(all_warnings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
