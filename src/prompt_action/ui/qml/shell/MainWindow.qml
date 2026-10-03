import QtQuick
import QtQuick.Window
import "../theme" as PATheme

Window {
    id: root
    objectName: "mainWindow"
    width: 1600
    height: 900
    minimumWidth: PATheme.Metrics.minimumWindowWidth
    minimumHeight: PATheme.Metrics.minimumWindowHeight
    visible: true
    title: "Prompt Action"
    color: PATheme.Theme.pageBackground

    property string currentRoute: "dashboard"
    property string navigationEntityId: ""
    readonly property bool narrowLayout: width < 1320
    readonly property color primaryToken: PATheme.Theme.primary
    readonly property int sidebarWidthToken: PATheme.Metrics.sidebarWidth
    property var dashboardVm: (typeof dashboardViewModel !== "undefined") ? dashboardViewModel : null

    function routeTitle(route) {
        if (route === "system_history") return "Sejarah Sistem"
        if (route === "prompt") return "Per Prompt"
        if (route === "backup") return "Backup & Recovery"
        if (route === "settings") return "Pengaturan"
        return "Dashboard"
    }
    function routeSubtitle(route) {
        if (route === "system_history") return "Shell navigasi • konten final pada STEP 05"
        if (route === "prompt") return "Shell navigasi • konten final pada STEP 06"
        if (route === "backup") return "Shell navigasi • konten final pada STEP 07"
        if (route === "settings") return "Shell navigasi • konten final pada STEP 08"
        return "Ringkasan canonical System, Snapshot, Prompt aktif, dan status backup"
    }
    function navigateTo(route, entityId) {
        currentRoute = route
        navigationEntityId = entityId || ""
    }

    Connections {
        target: root.dashboardVm
        enabled: root.dashboardVm !== null
        function onNavigationRequested(route, entityId) {
            root.navigateTo(route, entityId)
        }
    }

    Sidebar {
        id: sidebar
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        narrow: root.narrowLayout
        currentRoute: root.currentRoute
        onRouteRequested: function(route) { root.navigateTo(route, "") }
    }

    Item {
        id: workArea
        anchors.left: sidebar.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        TopBar {
            id: topbar
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            pageTitle: root.routeTitle(root.currentRoute)
            pageSubtitle: root.routeSubtitle(root.currentRoute)
            narrow: root.narrowLayout
        }

        ContentHost {
            id: contentHost
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: topbar.bottom
            anchors.bottom: parent.bottom
            anchors.margins: PATheme.Metrics.contentPadding
            currentRoute: root.currentRoute
        }
    }
}
