import QtQuick
import QtQuick.Layouts
import "../theme" as PATheme
import "../components" as PA
import "../search" as Search

Rectangle {
    id: topbar
    objectName: "topbar"
    property string pageTitle: "Dashboard"
    property string pageSubtitle: "Foundation shell"
    readonly property string displayedSubtitle: pageSubtitle.indexOf("[STEP 07] ") === 0 ? pageSubtitle.substring(10) : pageSubtitle
    property string systemLabel: "System V1 • S001"
    property bool narrow: false
    property var searchViewModel: null

    height: PATheme.Metrics.topBarHeight
    color: PATheme.Theme.surface
    z: 100

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
                text: topbar.displayedSubtitle
                color: PATheme.Theme.textSecondary
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.caption
                elide: Text.ElideRight
                width: parent.width
            }
        }

        Item {
            id: searchHost
            Layout.preferredWidth: topbar.narrow ? 225 : 290
            Layout.minimumWidth: 205
            Layout.preferredHeight: PATheme.Metrics.controlHeight
            z: 220

            PA.PASearchField {
                id: searchField
                objectName: "topbar_search"
                anchors.fill: parent
                accessibleName: "Cari Prompt, Revision, Snapshot, dan Backup"
                placeholderText: "Cari prompt, snapshot, revision…"
                onTextChanged: if (topbar.searchViewModel) topbar.searchViewModel.setQuery(text)
                Keys.onPressed: function(event) {
                    if (!topbar.searchViewModel) return
                    if (event.key === Qt.Key_Down) { topbar.searchViewModel.moveSelection(1); event.accepted = true }
                    else if (event.key === Qt.Key_Up) { topbar.searchViewModel.moveSelection(-1); event.accepted = true }
                    else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) { topbar.searchViewModel.forceSearch(); topbar.searchViewModel.activateSelected(); event.accepted = true }
                    else if (event.key === Qt.Key_Escape) { topbar.searchViewModel.closeResults(); event.accepted = true }
                }
            }

            Search.SearchResultsPanel {
                id: resultsPanel
                anchors.top: parent.bottom
                anchors.right: parent.right
                anchors.topMargin: 8
                stateData: topbar.searchViewModel ? topbar.searchViewModel.state : ({"state":"IDLE","results":[],"message":"","selected_index":-1})
                viewModel: topbar.searchViewModel
            }
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
