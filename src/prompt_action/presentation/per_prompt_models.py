from __future__ import annotations

from enum import StrEnum


class FileState(StrEnum):
    VALID = "VALID"
    MISSING = "MISSING"
    HASH_MISMATCH = "HASH_MISMATCH"
    HISTORY_ONLY = "HISTORY_ONLY"
    UNKNOWN = "UNKNOWN"


INTEGRITY_DEGRADED_CODES = frozenset({"INV-10", "INV-10-SHA-MISMATCH"})
