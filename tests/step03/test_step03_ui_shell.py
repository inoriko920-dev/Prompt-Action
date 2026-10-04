from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QSG_RHI_BACKEND", "software")
os.environ.setdefault("QSG_RENDER_LOOP", "basic")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

ROOT = Path(__file__).resolve().parents[2]
APP_QML = ROOT / "src/prompt_action/ui/qml/App.qml"
GALLERY_QML = ROOT / "tests/step03/qml/ComponentGallery.qml"
PROBE = ROOT / "tests/step03/qml_probe.py"

# STEP 03 protects immutable UI reference assets. Canonical/baseline metadata
# legitimately evolves in later validated steps and must not be byte-pinned here.
EXPECTED_HASHES = {
    "docs/UI_REFERENCE_PACKAGE_V1/materialized/VERSIONING_RULES.md": "9b33b4af31ddf27b5b6cfffd95011550a4e4de3f48c8e8d697b95f9e06da8969",
    "docs/UI_REFERENCE_PACKAGE_V1/materialized/images/01-Dashboard.jpg": "7553c2808f5051a4b51c82d163cbd6142bf3aab658e407802f3e39eccb03a514",
    "docs/UI_REFERENCE_PACKAGE_V1/materialized/images/02-Sejarah-Sistem.jpg": "72c1ead9cb91e93989070718f4ceb8f1df8483239ca07f10f86a0a8d337343d8",
    "docs/UI_REFERENCE_PACKAGE_V1/materialized/images/03-Per-Prompt.jpg": "7ae0a93a27ca7fc3b2576aa1298d75a527d9c061b38c4690fcb3189ffe818e52",
    "docs/UI_REFERENCE_PACKAGE_V1/materialized/images/04-Backup-Recovery.jpg": "6149e181c1577f3c080b8e908b5d9ffaa339cf1fefae88fc4f82f879d920efcb",
    "docs/UI_REFERENCE_PACKAGE_V1/materialized/images/05-Pengaturan.jpg": "64c916b15b2e0d36129748348d22c0e66949cbdf8756b3a5de583bf62bc2c84a",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="session")
def app():
    QQuickWindow.setSceneGraphBackend("software")
    instance = QGuiApplication.instance() or QGuiApplication(["step03-tests"])
    yield instance


def _load(path: Path, app: QGuiApplication):
    warnings: list[str] = []
    engine = QQmlApplicationEngine()
    engine.warnings.connect(lambda items: warnings.extend(str(item) for item in items))
    engine.load(QUrl.fromLocalFile(str(path.resolve())))
    assert engine.rootObjects(), "QML root did not load: " + " | ".join(warnings)
    root = engine.rootObjects()[0]
    QTest.qWait(50)
    app.processEvents()
    return engine, root, warnings


def _gallery(mode: str, app: QGuiApplication):
    engine, root, warnings = _load(GALLERY_QML, app)
    root.setProperty("galleryMode", mode)
    QTest.qWait(30)
    app.processEvents()
    return engine, root, warnings


def _probe(scale: str, qml: Path = APP_QML, cwd: Path = ROOT, width: int = 1180, height: int = 720):
    env = os.environ.copy()
    env["QT_SCALE_FACTOR"] = scale
    result = subprocess.run(
        [sys.executable, str(PROBE), "--qml", str(qml), "--width", str(width), "--height", str(height)],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=40,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_t01_theme_singleton_load_without_qml_error(app):
    engine, root, warnings = _load(APP_QML, app)
    assert warnings == []
    engine.deleteLater()


def test_t02_main_tokens_are_accessible(app):
    engine, root, _ = _load(APP_QML, app)
    assert root.property("primaryToken").name().lower() == "#1677ff"
    assert root.property("sidebarWidthToken") == 232
    engine.deleteLater()


def test_t03_button_primary_state(app):
    engine, root, warnings = _gallery("buttons", app)
    button = root.findChild(QObject, "button_primary")
    assert button and button.property("enabled")
    assert button.property("resolvedBackground").name().lower() == "#1677ff"
    assert warnings == []
    engine.deleteLater()


def test_t04_button_secondary_disabled_loading(app):
    engine, root, _ = _gallery("buttons", app)
    assert root.findChild(QObject, "button_secondary").property("variant") == "secondary"
    assert not root.findChild(QObject, "button_disabled").property("enabled")
    assert root.findChild(QObject, "button_loading").property("loading")
    assert not root.findChild(QObject, "button_loading").property("enabled")
    engine.deleteLater()


def test_t05_card_states(app):
    engine, root, _ = _gallery("buttons", app)
    assert root.findChild(QObject, "card_default")
    assert root.findChild(QObject, "card_selected").property("selected")
    assert root.findChild(QObject, "card_warning").property("tone") == "warning"
    assert root.findChild(QObject, "card_error").property("tone") == "error"
    engine.deleteLater()


def test_t06_input_states(app):
    engine, root, _ = _gallery("inputs", app)
    assert root.findChild(QObject, "input_empty")
    assert root.findChild(QObject, "input_error").property("invalid")
    assert not root.findChild(QObject, "input_disabled").property("enabled")
    engine.deleteLater()


def test_t07_search_field_layout(app):
    engine, root, _ = _gallery("inputs", app)
    search = root.findChild(QObject, "search_field")
    assert search and search.property("implicitHeight") >= 40
    assert search.property("leftPadding") >= 36
    engine.deleteLater()


def test_t08_nav_item_states(app):
    engine, root, _ = _gallery("nav", app)
    assert root.findChild(QObject, "nav_selected").property("selected")
    assert not root.findChild(QObject, "nav_default").property("selected")
    engine.deleteLater()


def test_t09_status_badge_states(app):
    engine, root, _ = _gallery("status", app)
    for name in ("neutral", "success", "warning", "error", "draft", "legacy"):
        assert root.findChild(QObject, f"badge_{name}").property("tone") == name
    engine.deleteLater()


def test_t10_icon_button_tooltip_accessibility(app):
    engine, root, _ = _gallery("nav", app)
    button = root.findChild(QObject, "icon_button")
    assert button.property("tooltipText") == "Informasi"
    assert button.property("accessibleName") == "Buka informasi"
    engine.deleteLater()


def test_t11_main_window_1600x900(app):
    engine, root, _ = _load(APP_QML, app)
    assert root.property("width") == 1600 and root.property("height") == 900
    engine.deleteLater()


def test_t12_min_window_1180x720(app):
    engine, root, _ = _load(APP_QML, app)
    assert root.property("minimumWidth") == 1180
    assert root.property("minimumHeight") == 720
    engine.deleteLater()


def test_t13_1366x768_layout(app):
    engine, root, warnings = _load(APP_QML, app)
    root.setProperty("width", 1366); root.setProperty("height", 768); QTest.qWait(30)
    sidebar = root.findChild(QObject, "sidebar"); host = root.findChild(QObject, "contentHost")
    assert sidebar.property("width") >= 200 and host.property("width") > 800 and host.property("height") > 500
    assert warnings == []
    engine.deleteLater()


def test_t14_125_percent_dpi():
    result = _probe("1.25")
    assert result["valid"] and result["content_width"] > 700


def test_t15_150_percent_dpi():
    result = _probe("1.5")
    assert result["valid"] and result["content_height"] > 500


def test_t16_175_percent_dpi():
    result = _probe("1.75")
    assert result["valid"] and result["sidebar_width"] >= 200


def test_t17_keyboard_tab_order_declared(app):
    text = (ROOT / "src/prompt_action/ui/qml/shell/Sidebar.qml").read_text(encoding="utf-8")
    for target in ("navHistory", "navPrompt", "navBackup", "navSettings", "navDashboard"):
        assert f"KeyNavigation.tab: {target}" in text
    engine, root, _ = _load(APP_QML, app)
    for name in ("nav_dashboard", "nav_system_history", "nav_prompt", "nav_backup", "nav_settings"):
        assert root.findChild(QObject, name).property("activeFocusOnTab")
    engine.deleteLater()


def test_t18_enter_space_activation_contract():
    for relative in ("components/PAButton.qml", "components/PANavItem.qml"):
        text = (ROOT / "src/prompt_action/ui/qml" / relative).read_text(encoding="utf-8")
        assert "Keys.onReturnPressed" in text and "Keys.onSpacePressed" in text


@pytest.mark.parametrize("route,object_name", [
    ("dashboard", "placeholder_dashboard"),
    ("system_history", "placeholder_system_history"),
    ("prompt", "placeholder_prompt"),
    ("backup", "placeholder_backup"),
    ("settings", "placeholder_settings"),
])
def test_t19_t23_placeholder_routes(route, object_name, app):
    engine, root, warnings = _load(APP_QML, app)
    root.setProperty("currentRoute", route); QTest.qWait(30); app.processEvents()
    assert root.findChild(QObject, object_name) is not None
    assert warnings == []
    engine.deleteLater()


def test_t24_topbar_title_subtitle_follow_route(app):
    engine, root, _ = _load(APP_QML, app)
    topbar = root.findChild(QObject, "topbar")
    root.setProperty("currentRoute", "backup"); QTest.qWait(20)
    assert topbar.property("pageTitle") == "Backup & Recovery"
    assert "STEP 07" in topbar.property("pageSubtitle")
    engine.deleteLater()


def test_t25_sidebar_only_one_selected(app):
    engine, root, _ = _load(APP_QML, app)
    names = ("nav_dashboard", "nav_system_history", "nav_prompt", "nav_backup", "nav_settings")
    for route in ("dashboard", "system_history", "prompt", "backup", "settings"):
        root.setProperty("currentRoute", route); QTest.qWait(15)
        selected = [root.findChild(QObject, name).property("selected") for name in names]
        assert selected.count(True) == 1
    engine.deleteLater()


def test_t26_no_qml_warning_during_navigation(app):
    engine, root, warnings = _load(APP_QML, app)
    for route in ("dashboard", "system_history", "prompt", "backup", "settings", "dashboard"):
        root.setProperty("currentRoute", route); QTest.qWait(15); app.processEvents()
    assert warnings == []
    engine.deleteLater()


def test_t27_local_assets_resolve_from_non_project_cwd(tmp_path):
    unrelated = tmp_path / "unrelated cwd"; unrelated.mkdir()
    result = _probe("1", cwd=unrelated)
    assert result["valid"]


def test_t28_relocation_resolves_assets(tmp_path):
    relocated = tmp_path / "Relocated Prompt Action Ω" / "ui"
    shutil.copytree(ROOT / "src/prompt_action/ui", relocated)
    result = _probe("1", qml=relocated / "qml/App.qml", cwd=tmp_path)
    assert result["valid"]


def test_t29_protected_prompt_legacy_version_data_unchanged():
    for relative, expected in EXPECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected, relative


def test_t30_screenshot_evidence_set_complete():
    base = Path(os.environ.get("STEP03_EVIDENCE_DIR", ROOT / "evidence/step03/generated"))
    required = [
        "screenshots/1600x900_100_dashboard-shell.png",
        "screenshots/1600x900_100_history-shell.png",
        "screenshots/1600x900_100_prompt-shell.png",
        "screenshots/1600x900_100_backup-shell.png",
        "screenshots/1600x900_100_settings-shell.png",
        "components/buttons_states.png",
        "components/inputs_states.png",
        "components/nav_states.png",
        "components/status_badges.png",
        "visual_review.md",
        "capture.json",
    ]
    missing = [relative for relative in required if not (base / relative).is_file()]
    assert missing == []
