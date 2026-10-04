from __future__ import annotations

import re

from prompt_action.domain.errors import BackupWorkflowError

_BACKUP_RE = re.compile(r"^B([0-9]{3})$")


def allocate_backup(existing: list[str]) -> str:
    values: list[int] = []
    for value in existing:
        match = _BACKUP_RE.fullmatch(str(value))
        if not match:
            raise BackupWorkflowError("BACKUP_ID_INVALID", f"Invalid official Backup ID: {value!r}")
        values.append(int(match.group(1)))
    number = max(values, default=0) + 1
    if number > 999:
        raise BackupWorkflowError("BACKUP_ID_EXHAUSTED", "Backup ID space exhausted for 3-digit policy")
    return f"B{number:03d}"
