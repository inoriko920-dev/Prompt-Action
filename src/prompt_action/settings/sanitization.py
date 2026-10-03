from __future__ import annotations

from pathlib import Path
import re
from typing import Any

_SECRET_KEYS = ("token", "password", "passwd", "secret", "authorization", "auth_header", "cookie", "oauth", "credential", "private_key", "pat")
_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"(?i)(token|password|secret|authorization|cookie)\s*[:=]\s*[^\s,;]+"),
)


def _secret_key(key: object) -> bool:
    lowered = str(key).lower()
    return any(part in lowered for part in _SECRET_KEYS)


def sanitize_text(text: str, *, project_root: Path | None = None, user_home: Path | None = None) -> str:
    result = text
    if project_root is not None:
        root = str(project_root.resolve(strict=False))
        if root:
            result = result.replace(root, "<PROJECT_ROOT>").replace(root.replace("\\", "/"), "<PROJECT_ROOT>")
    home_path = user_home or Path.home()
    home = str(home_path.resolve(strict=False))
    if home:
        result = result.replace(home, "<USER_HOME>").replace(home.replace("\\", "/"), "<USER_HOME>")
    for pattern in _PATTERNS:
        result = pattern.sub("<REDACTED>", result)
    return result


def sanitize_value(value: Any, *, project_root: Path | None = None, user_home: Path | None = None, _parent_key: str | None = None) -> Any:
    if _parent_key is not None and _secret_key(_parent_key):
        return "<REDACTED>"
    if isinstance(value, dict):
        return {str(key): ("<REDACTED>" if _secret_key(key) else sanitize_value(item, project_root=project_root, user_home=user_home, _parent_key=str(key))) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_value(item, project_root=project_root, user_home=user_home) for item in value]
    if isinstance(value, str):
        return sanitize_text(value, project_root=project_root, user_home=user_home)
    return value
