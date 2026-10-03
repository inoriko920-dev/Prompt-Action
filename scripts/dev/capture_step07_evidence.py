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

from PySide6.QtCore import QCoreApplication

from prompt_action.bootstrap.qml_boot import create_application, load_qml
from prompt_action.presentation.backup_view_model import BackupRecoveryViewModel


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="ci-step07-evidence")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    out = root / args.output
    screens = out / "screenshots"
    screens.mkdir(parents=True, exist_ok=True)

    app = create_application(["step07-capture"])
    vm = BackupRecoveryViewModel(root)
    qml = root / "src/prompt_action/ui/qml/App.qml"
    engine = load_qml(qml, {"backupViewModel": vm})
    warnings: list[str] = []
    engine.warnings.connect(lambda items: warnings.extend(str(item.toString()) for item in items))
    QCoreApplication.processEvents()
    if not engine.rootObjects():
        raise RuntimeError("QML root failed to load")
    window = engine.rootObjects()[0]
    window.setProperty("currentRoute", "backup")
    QCoreApplication.processEvents()
    screen = app.primaryScreen()
    if screen is None:
        raise RuntimeError("No primary screen available for capture")

    captured = []
    for width, height in [(1600, 900), (1920, 1080), (1366, 768)]:
        window.setWidth(width); window.setHeight(height)
        QCoreApplication.processEvents()
        image = screen.grabWindow(int(window.winId()), 0, 0, width, height).toImage()
        path = screens / f"backup-recovery-{width}x{height}.png"
        if image.isNull() or not image.save(str(path)):
            raise RuntimeError(f"Screenshot failed: {width}x{height}")
        captured.append({"file": path.name, "width": image.width(), "height": image.height(), "bytes": path.stat().st_size})

    meta = {"screenshots": captured, "warnings": warnings, "canonical_state": vm.state}
    (out / "capture.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    if warnings:
        raise RuntimeError("QML warnings: " + " | ".join(warnings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
