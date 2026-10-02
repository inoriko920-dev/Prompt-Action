from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


def create_application(argv: Sequence[str] | None = None) -> QGuiApplication:
    existing = QGuiApplication.instance()
    if existing is not None:
        return existing
    return QGuiApplication(list(argv or []))


def load_qml(qml_path: Path) -> QQmlApplicationEngine:
    engine = QQmlApplicationEngine()
    engine.load(QUrl.fromLocalFile(str(qml_path.resolve())))
    return engine
