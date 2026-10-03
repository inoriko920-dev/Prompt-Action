import QtQuick
import "../pages" as Pages

Item {
    id: host
    objectName: "contentHost"
    property string currentRoute: "dashboard"

    Component { id: dashboardComponent; Pages.DashboardPage {} }
    Component { id: historyComponent; Pages.PlaceholderSystemHistory {} }
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
