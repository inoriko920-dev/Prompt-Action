from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from prompt_action.domain.errors import CanonicalDataError


@dataclass(frozen=True, slots=True)
class MigrationResult:
    from_schema_version: int
    to_schema_version: int
    document: dict[str, Any]
    changes: tuple[str, ...]


def migrate_document(document: dict[str, Any], target_version: int = 1) -> MigrationResult:
    if not isinstance(document, dict):
        raise CanonicalDataError("Migration source must be an object")
    current = document.get("schema_version")
    if not isinstance(current, int):
        raise CanonicalDataError("Migration source requires integer schema_version")
    if target_version != 1:
        raise CanonicalDataError(f"Unsupported migration target schema_version={target_version}")
    if current > target_version:
        raise CanonicalDataError(f"Cannot downgrade schema_version {current} -> {target_version}")
    if current == target_version:
        return MigrationResult(current, target_version, deepcopy(document), tuple())
    if current != 0:
        raise CanonicalDataError(f"No deterministic migration path from schema_version={current}")

    migrated = deepcopy(document)
    previous_revision = migrated.get("app_data_revision", 0)
    if not isinstance(previous_revision, int):
        previous_revision = 0
    migrated["schema_version"] = 1
    migrated["app_data_revision"] = max(previous_revision + 1, 1)
    migrated.setdefault("app_version", "0.1.0-dev")
    migrated.setdefault("legacy_sources", [])
    migrated.setdefault("backups", [])
    migrated.setdefault("release_policy", {"require_backup_for_complete": True, "require_second_copy": True})
    migrated.setdefault("integrity", {})
    migrated["integrity"] = deepcopy(migrated["integrity"])
    migrated["integrity"]["last_metadata_migration"] = {
        "from_schema_version": 0,
        "to_schema_version": 1,
        "note": "Metadata-only deterministic migration; prompt bytes are outside migration scope.",
    }
    return MigrationResult(
        from_schema_version=0,
        to_schema_version=1,
        document=migrated,
        changes=(
            "schema_version:0->1",
            "ensure app_version",
            "ensure legacy_sources/backups/release_policy/integrity",
            "increment app_data_revision",
        ),
    )


@dataclass(frozen=True, slots=True)
class AppliedMigration:
    result: MigrationResult
    backup_path: str | None
    backup_sha256: str | None
    saved_revision: int | None


def migrate_repository(repository, target_version: int = 1) -> AppliedMigration:
    import hashlib
    import os

    current_state = repository.load()
    result = migrate_document(current_state.document, target_version=target_version)
    if result.from_schema_version == result.to_schema_version:
        return AppliedMigration(result, None, None, None)

    original_bytes = repository.path.read_bytes()
    backup_dir = repository.project_root / "data" / "migrations" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_name = (
        f"version_history.before_schema{result.from_schema_version}_to_"
        f"{result.to_schema_version}.rev{current_state.app_data_revision}.json"
    )
    backup_path = backup_dir / backup_name
    with backup_path.open("wb") as handle:
        handle.write(original_bytes)
        handle.flush()
        os.fsync(handle.fileno())
    backup_hash = hashlib.sha256(original_bytes).hexdigest()

    save = repository.save(result.document, expected_revision=current_state.app_data_revision)
    return AppliedMigration(
        result=result,
        backup_path=str(backup_path.relative_to(repository.project_root)).replace("\\", "/"),
        backup_sha256=backup_hash,
        saved_revision=save.app_data_revision,
    )
