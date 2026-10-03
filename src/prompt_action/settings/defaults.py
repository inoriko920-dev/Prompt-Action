from __future__ import annotations

from pathlib import Path

from prompt_action.app_version import APP_VERSION

from .models import AdvancedSettings, AppSettings, AppearanceSettings, BackupPolicySettings, GeneralSettings, GitHubSettings, SettingsMeta


def default_settings(project_root: Path) -> AppSettings:
    # Portable internal defaults; STEP 08 never silently creates/moves Prompt data.
    return AppSettings(
        general=GeneralSettings(root_dir=".", prompts_dir="prompts", backup_dir="backups"),
        backup=BackupPolicySettings(
            backup_on_release=True,
            write_sha256=True,
            verify_after_write=True,
            second_copy_enabled=True,
            second_copy_dir="backups-second-copy",
        ),
        github=GitHubSettings(repository="inoriko920-dev/Prompt-Action", branch="main"),
        appearance=AppearanceSettings(theme="light_blue", ui_scale=100, tree_density="comfortable"),
        advanced=AdvancedSettings(diagnostics_dir="runtime/diagnostics", log_level="INFO"),
        meta=SettingsMeta(schema_version=1, saved_at=None, app_version=APP_VERSION),
    )
