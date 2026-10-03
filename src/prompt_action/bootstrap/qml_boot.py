from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Sequence

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


def create_application(argv: Sequence[str] | None = None) -> QGuiApplication:
    existing = QGuiApplication.instance()
    if existing is not None:
        return existing
    return QGuiApplication(list(argv or []))


def load_qml(qml_path: Path, context_properties: Mapping[str, Any] | None = None) -> QQmlApplicationEngine:
    engine = QQmlApplicationEngine()
    if context_properties:
        for name, value in context_properties.items():
            if isinstance(value, QObject) and value.parent() is None:
                value.setParent(engine)
            engine.rootContext().setContextProperty(name, value)
    engine.load(QUrl.fromLocalFile(str(qml_path.resolve())))
    return engine
