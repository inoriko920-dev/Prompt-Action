from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class IntegrationError(RuntimeError):
    code: str
    user_message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.code}: {self.user_message}"


class SearchError(IntegrationError):
    pass


class CompareError(IntegrationError):
    pass


class DownloadError(IntegrationError):
    pass


class PathSafetyError(IntegrationError):
    pass
