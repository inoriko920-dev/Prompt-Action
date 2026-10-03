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
                "load_state": "loading",
                "legacy": {"available": false, "label": "", "verified": false},
                "systems": [],
                "selected_snapshot_id": "",
                "selected_snapshot": {},
                "diagnostics": []
            }) : null
        }
    }
    Component { id: promptComponent; Pages.PlaceholderPrompt {} }
    Component { id: backupComponent; Pages.PlaceholderBackup {} }
    Component { id: settingsComponent; Pages.PlaceholderSettings {} }

    Loader {
        id: loader
        objectName: "routeLoader"
        anchors.fill: parent
        sourceComponent: host.currentRoute === "system_history" ? historyComponent : host.currentRoute === "prompt" ? promptComponent : host.currentRoute === "backup" ? backupComponent : host.currentRoute === "settings" ? settingsComponent : dashboardComponent
    }
}
