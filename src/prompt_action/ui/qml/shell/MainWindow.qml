import QtQuick
import QtQuick.Window
import "../theme" as PATheme
import "../dialogs" as Dialogs

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
    property string navigationSubId: ""
    readonly property bool narrowLayout: width < 1320
    readonly property color primaryToken: PATheme.Theme.primary
    readonly property int sidebarWidthToken: PATheme.Metrics.sidebarWidth
    property var dashboardVm: (typeof dashboardViewModel !== "undefined") ? dashboardViewModel : null
    property var historyVm: (typeof historyViewModel !== "undefined") ? historyViewModel : null
    property var perPromptVm: (typeof perPromptViewModel !== "undefined") ? perPromptViewModel : null
    property var backupVm: (typeof backupViewModel !== "undefined") ? backupViewModel : null
    property var searchVm: (typeof searchViewModel !== "undefined") ? searchViewModel : null

    function routeTitle(route) {
        if (route === "system_history") return "Sejarah Sistem"
        if (route === "prompt") return "Per Prompt"
        if (route === "backup") return "Backup & Recovery"
        if (route === "settings") return "Pengaturan"
        return "Dashboard"
    }
    function routeSubtitle(route) {
        if (route === "system_history") return "System, snapshot, dan kesinambungan perubahan"
        if (route === "prompt") return "Revision explorer • ACTIVE dan SELECTED dipisahkan"
        if (route === "backup") return "[STEP 07] Pastikan Prompt Action dapat dibangun ulang kapan pun"
        if (route === "settings") return "Lokasi data, backup, GitHub, dan tampilan"
        return "Ringkasan canonical System, Snapshot, Prompt aktif, dan status backup"
    }
    function navigateTo(route, entityId, subId) {
        currentRoute = route
        navigationEntityId = entityId || ""
        navigationSubId = subId || ""
        if (route === "system_history" && historyVm && navigationEntityId) historyVm.selectSnapshot(navigationEntityId)
        if (route === "prompt" && perPromptVm && navigationEntityId) {
            perPromptVm.selectPrompt(navigationEntityId)
            if (navigationSubId) perPromptVm.selectRevision(navigationSubId)
        }
    }

    Connections { target: root.dashboardVm; enabled: root.dashboardVm !== null; function onNavigationRequested(route, entityId) { root.navigateTo(route, entityId, "") } }
    Connections {
        target: root.historyVm; enabled: root.historyVm !== null
        function onNavigationRequested(route, entityId) { root.navigateTo(route, entityId, "") }
        function onCompareRequested(data) { snapshotCompare.compareData = data; snapshotCompare.open() }
    }
    Connections {
        target: root.perPromptVm; enabled: root.perPromptVm !== null
        function onNavigationRequested(route, entityId) { root.navigateTo(route, entityId, "") }
        function onCompareRequested(data) { revisionCompare.compareData = data; revisionCompare.open() }
    }
    Connections { target: root.backupVm; enabled: root.backupVm !== null; function onNavigationRequested(route, entityId) { root.navigateTo(route, entityId, "") } }
    Connections { target: root.searchVm; enabled: root.searchVm !== null; function onNavigationRequested(route, entityId, subId) { root.navigateTo(route, entityId, subId) } }

    Sidebar {
        id: sidebar
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        narrow: root.narrowLayout
        currentRoute: root.currentRoute
        onRouteRequested: function(route) { root.navigateTo(route, "", "") }
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
            searchViewModel: root.searchVm
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

    Dialogs.CompareRevisionDialog {
        id: revisionCompare
        parent: root.contentItem
        x: Math.max(24, (root.width - width) / 2)
        y: Math.max(24, (root.height - height) / 2)
    }
    Dialogs.CompareSnapshotDialog {
        id: snapshotCompare
        parent: root.contentItem
        x: Math.max(24, (root.width - width) / 2)
        y: Math.max(24, (root.height - height) / 2)
    }
}
