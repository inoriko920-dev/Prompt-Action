from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot

from .backup_query_service import BackupRecoveryQueryService


class BackupRecoveryViewModel(QObject):
    stateChanged = Signal()
    navigationRequested = Signal(str, str)

    def __init__(self, project_root: Path):
        super().__init__()
        self._service = BackupRecoveryQueryService(project_root)
        self._state = self._service.read()

    @Property('QVariant', notify=stateChanged)
    def state(self):
        return self._state

    @Slot()
    def refresh(self) -> None:
        self._state = self._service.read()
        self.stateChanged.emit()

    @Slot()
    def openRecoveryGuide(self) -> None:
        if self._state.get('actions', {}).get('can_open_recovery_guide'):
            self.navigationRequested.emit('backup', 'recovery-guide')

    @Slot()
    def requestCreateBackup(self) -> None:
        # STEP 07 intentionally exposes no write path.
        return

    @Slot()
    def requestRestoreBackup(self) -> None:
        # Restore is deferred to the later write/recovery workflow.
        return
