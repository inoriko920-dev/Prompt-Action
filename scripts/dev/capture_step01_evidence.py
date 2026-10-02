from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer
from PySide6.QtQuick import QQuickWindow

from prompt_action.bootstrap.app_paths import resolve_app_paths
from prompt_action.bootstrap.qml_boot import create_application, load_qml


def _latest_log(runtime_root: Path) -> Path:
    logs = sorted((runtime_root / "logs").glob("prompt-action-*.log"), key=lambda p: p.stat().st_mtime)
    if not logs:
        raise RuntimeError(f"No startup log produced under {runtime_root}")
    return logs[-1]


def _run_module(repo_root: Path, runtime_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PROMPT_ACTION_RUNTIME_ROOT"] = str(runtime_root)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_QUICK_BACKEND"] = "software"
    env["QSG_RENDER_LOOP"] = "basic"
    return subprocess.run(
        [sys.executable, "-m", "prompt_action", *args],
        cwd=repo_root.parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def _capture_screenshot(path: Path) -> int:
    QQuickWindow.setSceneGraphBackend("software")
    paths = resolve_app_paths()
    app = create_application([])
    engine = load_qml(paths.resource_root / "qml" / "App.qml")
    roots = engine.rootObjects()
    if not roots:
        return 3
    window = roots[0]

    def capture() -> None:
        image = window.grabWindow()
        if image.isNull() or not image.save(str(path)):
            app.exit(4)
            return
        app.quit()

    QTimer.singleShot(800, capture)
    return int(app.exec())


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--screenshot-only":
        return _capture_screenshot(Path(sys.argv[2]).resolve())

    repo_root = Path(__file__).resolve().parents[2]
    output = repo_root / "evidence" / "step01" / "ci-generated"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    success_runtime = output / "success-runtime"
    failure_runtime = output / "failure-runtime"

    success = _run_module(repo_root, success_runtime, "--smoke-test-ms", "150")
    if success.returncode != 0:
        raise RuntimeError(f"Success smoke failed: rc={success.returncode}\n{success.stderr}")
    shutil.copy2(_latest_log(success_runtime), output / "startup-success.log")

    missing_qml = output / "missing.qml"
    failure = _run_module(repo_root, failure_runtime, "--qml", str(missing_qml), "--smoke-test-ms", "1")
    if failure.returncode != 21:
        raise RuntimeError(f"Invalid-QML smoke returned {failure.returncode}, expected 21")
    shutil.copy2(_latest_log(failure_runtime), output / "startup-failure.log")

    screenshot = output / "minimal-window.png"
    screenshot_env = os.environ.copy()
    screenshot_env["QT_QPA_PLATFORM"] = "offscreen"
    screenshot_env["QT_QUICK_BACKEND"] = "software"
    screenshot_env["QSG_RENDER_LOOP"] = "basic"
    screenshot_result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--screenshot-only", str(screenshot)],
        cwd=repo_root,
        env=screenshot_env,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if screenshot_result.returncode != 0 or not screenshot.is_file() or screenshot.stat().st_size == 0:
        raise RuntimeError(
            "Screenshot capture failed: "
            f"rc={screenshot_result.returncode} stderr={screenshot_result.stderr.strip()}"
        )

    environment = {
        "python": sys.version,
        "platform": sys.platform,
        "success_backend": "offscreen + Qt Quick software + basic render loop",
        "screenshot_backend": "offscreen + Qt Quick software + basic render loop",
        "success_returncode": success.returncode,
        "failure_returncode": failure.returncode,
        "expected_window_title": "Prompt Action",
        "screenshot_bytes": screenshot.stat().st_size,
    }
    (output / "environment.json").write_text(json.dumps(environment, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
