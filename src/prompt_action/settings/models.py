from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

SUPPORTED_SCHEMA_VERSION = 1


@dataclass(slots=True)
class GeneralSettings:
    root_dir: str = "."
    prompts_dir: str = "prompts"
    backup_dir: str = "backups"


@dataclass(slots=True)
class BackupPolicySettings:
    backup_on_release: bool = True
    write_sha256: bool = True
    verify_after_write: bool = True
    second_copy_enabled: bool = True
    second_copy_dir: str = "backups-second-copy"


@dataclass(slots=True)
class GitHubSettings:
    repository: str = "inoriko920-dev/Prompt-Action"
    branch: str = "main"


@dataclass(slots=True)
class AppearanceSettings:
    theme: str = "light_blue"
    ui_scale: int = 100
    tree_density: str = "comfortable"


@dataclass(slots=True)
class AdvancedSettings:
    diagnostics_dir: str = "runtime/diagnostics"
    log_level: str = "INFO"


@dataclass(slots=True)
class SettingsMeta:
    schema_version: int = SUPPORTED_SCHEMA_VERSION
    saved_at: str | None = None
    app_version: str = "unknown"


@dataclass(slots=True)
class AppSettings:
    general: GeneralSettings = field(default_factory=GeneralSettings)
    backup: BackupPolicySettings = field(default_factory=BackupPolicySettings)
    github: GitHubSettings = field(default_factory=GitHubSettings)
    appearance: AppearanceSettings = field(default_factory=AppearanceSettings)
    advanced: AdvancedSettings = field(default_factory=AdvancedSettings)
    meta: SettingsMeta = field(default_factory=SettingsMeta)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.meta.schema_version),
            "general": asdict(self.general),
            "backup": asdict(self.backup),
            "github": asdict(self.github),
            "appearance": asdict(self.appearance),
            "advanced": asdict(self.advanced),
            "meta": {"saved_at": self.meta.saved_at, "app_version": self.meta.app_version},
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], *, app_version: str = "unknown") -> "AppSettings":
        # Unknown keys are ignored for forward tolerance. Only typed known keys can
        # flow back to disk, preventing accidental secret persistence.
        schema = raw.get("schema_version", SUPPORTED_SCHEMA_VERSION)
        try:
            schema_int = int(schema)
        except (TypeError, ValueError):
            schema_int = -1
        general_raw = _mapping(raw.get("general"))
        backup_raw = _mapping(raw.get("backup"))
        github_raw = _mapping(raw.get("github"))
        appearance_raw = _mapping(raw.get("appearance"))
        advanced_raw = _mapping(raw.get("advanced"))
        meta_raw = _mapping(raw.get("meta"))
        return cls(
            general=GeneralSettings(
                root_dir=_string(general_raw.get("root_dir"), "."),
                prompts_dir=_string(general_raw.get("prompts_dir"), "prompts"),
                backup_dir=_string(general_raw.get("backup_dir"), "backups"),
            ),
            backup=BackupPolicySettings(
                backup_on_release=_bool(backup_raw.get("backup_on_release"), True),
                write_sha256=_bool(backup_raw.get("write_sha256"), True),
                verify_after_write=_bool(backup_raw.get("verify_after_write"), True),
                second_copy_enabled=_bool(backup_raw.get("second_copy_enabled"), True),
                second_copy_dir=_string(backup_raw.get("second_copy_dir"), "backups-second-copy"),
            ),
            github=GitHubSettings(
                repository=_string(github_raw.get("repository"), "inoriko920-dev/Prompt-Action").strip(),
                branch=_string(github_raw.get("branch"), "main").strip(),
            ),
            appearance=AppearanceSettings(
                theme=_string(appearance_raw.get("theme"), "light_blue"),
                ui_scale=_int(appearance_raw.get("ui_scale"), 100),
                tree_density=_string(appearance_raw.get("tree_density"), "comfortable"),
            ),
            advanced=AdvancedSettings(
                diagnostics_dir=_string(advanced_raw.get("diagnostics_dir"), "runtime/diagnostics"),
                log_level=_string(advanced_raw.get("log_level"), "INFO").upper(),
            ),
            meta=SettingsMeta(
                schema_version=schema_int,
                saved_at=_nullable_string(meta_raw.get("saved_at")),
                app_version=_string(meta_raw.get("app_version"), app_version),
            ),
        )


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _string(value: Any, default: str) -> str:
    return value if isinstance(value, str) else default


def _nullable_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _bool(value: Any, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def _int(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
