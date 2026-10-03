from __future__ import annotations

"""Read-only export service for verified Prompt Action artifacts.

All sources are resolved from canonical stable IDs and restricted to approved
project roots. User-supplied arbitrary source paths are never accepted.
"""

from pathlib import Path
from typing import Any

from .models import DownloadPlan, DownloadResult, CancelToken


class DownloadService:
    def __init__(self, project_root: Path, *, document: dict[str, Any] | None = None):
        self.project_root = Path(project_root).resolve()
        self.document_override = document

    def prepare(self, entity_ref: dict[str, Any]) -> DownloadPlan:
        raise NotImplementedError

    def execute(self, plan: DownloadPlan, destination_dir: Path, *, conflict_policy: str = "cancel", cancel_token: CancelToken | None = None) -> DownloadResult:
        raise NotImplementedError
