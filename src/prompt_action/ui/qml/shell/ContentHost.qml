import QtQuick
import "../pages" as Pages

Item {
    id: host
    objectName: "contentHost"
    property string currentRoute: "dashboard"

    Component { id: dashboardComponent; Pages.DashboardPage {} }
    Component {
        id: historyComponent
        Pages.SystemHistoryPage {
            stateOverride: (typeof historyViewModel === "undefined") ? ({"load_state":"loading","legacy":{"available":false,"label":"","verified":false},"systems":[],"selected_snapshot_id":"","selected_snapshot":{},"diagnostics":[]}) : null
        }
    }
    Component {
        id: promptComponent
        Pages.PerPromptPage {
            stateOverride: (typeof perPromptViewModel === "undefined") ? ({"load_state":"loading","prompts":[],"selected_prompt_id":"","selected_prompt_name":"","active_revision_id":"","selected_revision_id":"","official_revisions":[],"drafts":[],"selected_revision":{},"available_files":[],"capabilities":{},"issues":[],"diagnostics":[]}) : null
        }
    }
    Component {
        id: backupComponent
        Pages.BackupRecoveryPage {
            stateOverride: (typeof backupViewModel === "undefined") ? ({"load_state":"loading","active_system":"","active_snapshot":"","snapshot_status":"","recovery_health":"REQUIRED","recovery_label":"MEMUAT","recovery_message":"Membaca status recovery…","checklist":[],"latest_backup":null,"history":[],"actions":{},"diagnostics":[]}) : null
        }
    }
    Component {
        id: settingsComponent
        Pages.SettingsPage {
            stateOverride: (typeof settingsViewModel === "undefined") ? ({
                "load_state":"loading","load_error":"","persisted_settings":{},"draft_settings":{
                    "general":{"root_dir":".","prompts_dir":"prompts","backup_dir":"backups"},
                    "backup":{"backup_on_release":true,"write_sha256":true,"verify_after_write":true,"second_copy_enabled":true,"second_copy_dir":"backups-second-copy"},
                    "github":{"repository":"inoriko920-dev/Prompt-Action","branch":"main"},
                    "appearance":{"theme":"light_blue","ui_scale":100,"tree_density":"comfortable"},
                    "advanced":{"diagnostics_dir":"runtime/diagnostics","log_level":"INFO"}
                },"is_dirty":false,"validation_errors":[],"validation_warnings":[],"save_state":"IDLE",
                "github_capability":{"status":"UNAVAILABLE","test_available":false,"reason":"GitHub service belum aktif.","can_open_repository":true},
                "path_capabilities":{},"repository_url":"https://github.com/inoriko920-dev/Prompt-Action","restart_required":false,"can_save":false,"can_revert":false,"status_message":"Memuat pengaturan…","last_export_path":""
            }) : null
        }
    }

    Loader {
        id: loader
        objectName: "routeLoader"
        anchors.fill: parent
        sourceComponent: host.currentRoute === "system_history" ? historyComponent : host.currentRoute === "prompt" ? promptComponent : host.currentRoute === "backup" ? backupComponent : host.currentRoute === "settings" ? settingsComponent : dashboardComponent
    }
}
