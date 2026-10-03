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
            stateOverride: (typeof historyViewModel === "undefined") ? ({
                "load_state": "loading", "legacy": {"available": false, "label": "", "verified": false},
                "systems": [], "selected_snapshot_id": "", "selected_snapshot": {}, "diagnostics": []
            }) : null
        }
    }
    Component {
        id: promptComponent
        Pages.PerPromptPage {
            stateOverride: (typeof perPromptViewModel === "undefined") ? ({
                "load_state":"loading","prompts":[],"selected_prompt_id":"","selected_prompt_name":"",
                "active_revision_id":"","selected_revision_id":"","official_revisions":[],"drafts":[],
                "selected_revision":{},"available_files":[],"capabilities":{},"issues":[],"diagnostics":[]
            }) : null
        }
    }
    Component {
        id: backupComponent
        Pages.BackupRecoveryPage {
            stateOverride: (typeof backupViewModel === "undefined") ? ({
                "load_state":"loading","active_system":"","active_snapshot":"","snapshot_status":"",
                "recovery_health":"REQUIRED","recovery_label":"MEMUAT","recovery_message":"Membaca status recovery…",
                "checklist":[],"latest_backup":null,"history":[],"actions":{},"diagnostics":[]
            }) : null
        }
    }
    Component { id: settingsComponent; Pages.PlaceholderSettings {} }

    Loader {
        id: loader
        objectName: "routeLoader"
        anchors.fill: parent
        sourceComponent: host.currentRoute === "system_history" ? historyComponent : host.currentRoute === "prompt" ? promptComponent : host.currentRoute === "backup" ? backupComponent : host.currentRoute === "settings" ? settingsComponent : dashboardComponent
    }
}
