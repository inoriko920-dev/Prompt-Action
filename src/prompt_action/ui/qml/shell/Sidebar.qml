import QtQuick
import QtQuick.Controls
import "../theme" as PATheme
import "../components" as PA

Rectangle {
    id: sidebar
    objectName: "sidebar"
    property string currentRoute: "dashboard"
    property bool narrow: false
    signal routeRequested(string route)

    color: PATheme.Theme.sidebar
    width: narrow ? PATheme.Metrics.sidebarNarrowWidth : PATheme.Metrics.sidebarWidth

    Rectangle {
        anchors.fill: parent
        color: PATheme.Theme.sidebar
        border.width: 0
    }

    Column {
        id: brand
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.leftMargin: 18
        anchors.rightMargin: 18
        anchors.topMargin: 22
        spacing: 4
        Text {
            text: "Prompt Action"
            color: "#FFFFFF"
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: 19
            font.weight: Font.DemiBold
        }
        Text {
            text: "Versioning Workspace"
            color: PATheme.Theme.sidebarMuted
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.caption
        }
    }

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: brand.bottom
        anchors.topMargin: 18
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        height: 1
        color: "#1B5A96"
    }

    Column {
        id: navColumn
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: brand.bottom
        anchors.topMargin: 42
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        spacing: 7

        PA.PANavItem {
            id: navDashboard
            objectName: "nav_dashboard"
            width: parent.width
            text: "Dashboard"
            route: "dashboard"
            iconSource: "../../assets/icons/dashboard.svg"
            selected: sidebar.currentRoute === route
            KeyNavigation.tab: navHistory
            onClicked: sidebar.routeRequested(route)
        }
        PA.PANavItem {
            id: navHistory
            objectName: "nav_system_history"
            width: parent.width
            text: "Sejarah Sistem"
            route: "system_history"
            iconSource: "../../assets/icons/history.svg"
            selected: sidebar.currentRoute === route
            KeyNavigation.tab: navPrompt
            onClicked: sidebar.routeRequested(route)
        }
        PA.PANavItem {
            id: navPrompt
            objectName: "nav_prompt"
            width: parent.width
            text: "Per Prompt"
            route: "prompt"
            iconSource: "../../assets/icons/prompt.svg"
            selected: sidebar.currentRoute === route
            KeyNavigation.tab: navBackup
            onClicked: sidebar.routeRequested(route)
        }
        PA.PANavItem {
            id: navBackup
            objectName: "nav_backup"
            width: parent.width
            text: "Backup"
            route: "backup"
            iconSource: "../../assets/icons/backup.svg"
            selected: sidebar.currentRoute === route
            KeyNavigation.tab: navSettings
            onClicked: sidebar.routeRequested(route)
        }
        PA.PANavItem {
            id: navSettings
            objectName: "nav_settings"
            width: parent.width
            text: "Pengaturan"
            route: "settings"
            iconSource: "../../assets/icons/settings.svg"
            selected: sidebar.currentRoute === route
            KeyNavigation.tab: navDashboard
            onClicked: sidebar.routeRequested(route)
        }
    }

    Rectangle {
        id: readyCard
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        anchors.bottomMargin: 16
        height: 58
        radius: PATheme.Metrics.radius12
        color: PATheme.Theme.sidebarStrong
        border.width: 1
        border.color: "#195A97"

        Rectangle {
            width: 9
            height: 9
            radius: 5
            color: PATheme.Theme.success
            anchors.left: parent.left
            anchors.leftMargin: 14
            anchors.verticalCenter: parent.verticalCenter
        }
        Column {
            anchors.left: parent.left
            anchors.leftMargin: 34
            anchors.verticalCenter: parent.verticalCenter
            spacing: 2
            Text {
                text: "Siap bekerja"
                color: "#FFFFFF"
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.body
                font.weight: Font.DemiBold
            }
            Text {
                text: "UI shell • STEP 03"
                color: PATheme.Theme.sidebarMuted
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.meta
            }
        }
    }
}
