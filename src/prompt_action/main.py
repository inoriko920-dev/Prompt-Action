from __future__ import annotations

import argparse
import logging
from pathlib import Path
import platform
import sys
import traceback
from typing import Sequence

from .app_version import APP_VERSION
from .bootstrap.app_paths import ProjectRootNotFoundError, RuntimeDirectoryError, ensure_runtime_directories, resolve_app_paths
from .bootstrap.exit_codes import ExitCode
from .bootstrap.logging_setup import configure_logging, flush_and_close

EXPECTED_PYSIDE_VERSION = "6.11.2"


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="prompt-action")
    parser.add_argument("--smoke-test-ms", type=int, default=None, help="Auto-close after N ms; intended for automated smoke tests.")
    parser.add_argument("--qml", type=Path, default=None, help="Override QML file for diagnostics/tests.")
    return parser.parse_args(list(argv) if argv is not None else None)


def _validate_runtime() -> tuple[bool, str]:
    if sys.version_info[:2] != (3, 13):
        return False, f"Prompt Action requires Python 3.13.x; found {platform.python_version()}"
    try:
        import PySide6
    except Exception as exc:  # pragma: no cover
        return False, f"PySide6 import failed: {exc}"
    if PySide6.__version__ != EXPECTED_PYSIDE_VERSION:
        return False, f"PySide6 {EXPECTED_PYSIDE_VERSION} required; found {PySide6.__version__}"
    return True, "ok"


def run(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    logger: logging.Logger | None = None
    log_file: Path | None = None
    valid, message = _validate_runtime()
    if not valid:
        print(message, file=sys.stderr)
        return int(ExitCode.DEPENDENCY_RUNTIME_MISMATCH)
    try:
        paths = resolve_app_paths()
    except ProjectRootNotFoundError as exc:
        print(f"Bootstrap/path failure: {exc}", file=sys.stderr)
        return int(ExitCode.BOOTSTRAP_PATH_FAILURE)
    try:
        ensure_runtime_directories(paths)
    except RuntimeDirectoryError as exc:
        print(str(exc), file=sys.stderr)
        return int(ExitCode.RUNTIME_NOT_WRITABLE)

    try:
        logger, log_file = configure_logging(paths)
        import PySide6
        from PySide6.QtCore import QLibraryInfo, QTimer
        from .bootstrap.qml_boot import create_application, load_qml
        from .presentation.dashboard_view_model import DashboardViewModel
        from .presentation.history_view_model import SystemHistoryViewModel
        from .presentation.per_prompt_view_model import PerPromptViewModel
        from .presentation.backup_view_model import BackupRecoveryViewModel
        from .ui.viewmodels.settings_view_model import SettingsViewModel
        from .ui.viewmodels.search_view_model import SearchViewModel

        logger.info("startup.begin app_version=%s", APP_VERSION)
        logger.info("runtime.python=%s", platform.python_version())
        logger.info("runtime.pyside=%s", PySide6.__version__)
        logger.info("runtime.qt=%s", QLibraryInfo.version().toString())
        logger.info("paths.project_root=%s", paths.project_root)
        logger.info("paths.resource_root=%s", paths.resource_root)
        logger.info("paths.runtime_root=%s", paths.runtime_root)
        logger.info("paths.log_dir=%s", paths.log_dir)
        logger.info("paths.temp_dir=%s", paths.temp_dir)

        qml_path = args.qml.resolve() if args.qml else paths.resource_root / "qml" / "App.qml"
        if not qml_path.is_file():
            logger.fatal("qml.file_missing path=%s", qml_path)
            print(f"QML file not found: {qml_path}. Log: {log_file}", file=sys.stderr)
            return int(ExitCode.QML_ROOT_LOAD_FAILURE)
        try:
            app = create_application(sys.argv[:1])
            dashboard_vm = DashboardViewModel(paths.project_root)
            history_vm = SystemHistoryViewModel(paths.project_root)
            per_prompt_vm = PerPromptViewModel(paths.project_root)
            backup_vm = BackupRecoveryViewModel(paths.project_root)
            settings_vm = SettingsViewModel(paths.project_root, runtime_root=paths.runtime_root)
            search_vm = SearchViewModel(paths.project_root)
            logger.info("dashboard.state=%s", dashboard_vm.state.get("load_state"))
            logger.info("history.state=%s", history_vm.state.get("load_state"))
            logger.info("per_prompt.state=%s", per_prompt_vm.state.get("load_state"))
            logger.info("backup.state=%s", backup_vm.state.get("load_state"))
            logger.info("settings.state=%s", settings_vm.state.get("load_state"))
            logger.info("search.state=%s", search_vm.state.get("state"))
            engine = load_qml(qml_path, {
                "dashboardViewModel": dashboard_vm,
                "historyViewModel": history_vm,
                "perPromptViewModel": per_prompt_vm,
                "backupViewModel": backup_vm,
                "settingsViewModel": settings_vm,
                "searchViewModel": search_vm,
            })
        except Exception:
            logger.exception("qt.initialization_failure")
            print(f"Qt/QML initialization failed. Log: {log_file}", file=sys.stderr)
            return int(ExitCode.QT_INITIALIZATION_FAILURE)
        if not engine.rootObjects():
            logger.fatal("qml.root_object_failed path=%s", qml_path)
            print(f"QML root object failed to load. Log: {log_file}", file=sys.stderr)
            return int(ExitCode.QML_ROOT_LOAD_FAILURE)
        logger.info("startup.ready qml=%s", qml_path)
        if args.smoke_test_ms is not None:
            QTimer.singleShot(max(args.smoke_test_ms, 0), app.quit)
        exit_code = int(app.exec())
        logger.info("shutdown.normal exit_code=%s", exit_code)
        return exit_code
    except Exception as exc:  # pragma: no cover
        if logger is not None:
            logger.critical("startup.unexpected_fatal\n%s", traceback.format_exc())
        else:
            traceback.print_exc()
        suffix = f" Log: {log_file}" if log_file else ""
        print(f"Unexpected fatal startup error: {exc}.{suffix}", file=sys.stderr)
        return int(ExitCode.UNEXPECTED_FATAL)
    finally:
        if logger is not None:
            flush_and_close(logger)


def main() -> int:
    return run()
