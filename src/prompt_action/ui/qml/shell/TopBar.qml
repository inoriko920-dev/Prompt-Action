import QtQuick
import QtQuick.Layouts
import "../theme" as PATheme
import "../components" as PA

Rectangle {
    id: topbar
    objectName: "topbar"
    property string pageTitle: "Dashboard"
    property string pageSubtitle: "Foundation shell"
    property string systemLabel: "System V1 • S001"
    property bool narrow: false

    height: PATheme.Metrics.topBarHeight
    color: PATheme.Theme.surface

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 1
        color: PATheme.Theme.border
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: PATheme.Metrics.space24
        anchors.rightMargin: PATheme.Metrics.space24
        spacing: 12

        Column {
            Layout.fillWidth: true
            Layout.minimumWidth: 250
            spacing: 4
            Text {
                text: topbar.pageTitle
                color: PATheme.Theme.textPrimary
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.pageTitle
                font.weight: Font.DemiBold
                elide: Text.ElideRight
                width: parent.width
            }
            Text {
                text: topbar.pageSubtitle
                color: PATheme.Theme.textSecondary
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.caption
                elide: Text.ElideRight
                width: parent.width
            }
        }

        PA.PASearchField {
            id: searchField
            objectName: "topbar_search"
            Layout.preferredWidth: topbar.narrow ? 225 : 290
            Layout.minimumWidth: 205
            accessibleName: "Cari di Prompt Action"
        }
        PA.PABadge {
            objectName: "topbar_system_badge"
            text: topbar.systemLabel
            tone: "draft"
        }
        PA.PAStatusPill {
            objectName: "topbar_backup_status"
            text: topbar.narrow ? "Backup • placeholder" : "Backup status • placeholder"
            tone: "neutral"
        }
    }
}
