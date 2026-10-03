import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme" as PATheme

Rectangle {
    id: root
    objectName: "global_search_results"
    property var stateData: ({"state":"IDLE","results":[],"message":"","selected_index":-1})
    property var viewModel: null
    readonly property string panelState: String(stateData.state || "IDLE")
    readonly property var results: stateData.results || []
    visible: panelState !== "IDLE"
    width: 460
    height: Math.min(420, Math.max(86, contentColumn.implicitHeight + 20))
    radius: PATheme.Metrics.radius12
    color: PATheme.Theme.surface
    border.width: 1
    border.color: PATheme.Theme.border
    z: 200

    Column {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: 10
        spacing: 7

        RowLayout {
            width: parent.width
            spacing: 8
            Text {
                Layout.fillWidth: true
                text: root.panelState === "SEARCHING" ? "Mencari…" : root.panelState === "EMPTY" ? "Tidak ditemukan" : root.panelState === "ERROR" ? "Search tidak tersedia" : (root.results.length + " hasil")
                color: root.panelState === "ERROR" ? PATheme.Theme.error : PATheme.Theme.textPrimary
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.caption
                font.weight: Font.DemiBold
            }
            Text {
                text: "↑ ↓ • Enter • Esc"
                color: PATheme.Theme.textSecondary
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.meta
            }
        }

        Text {
            width: parent.width
            visible: root.panelState === "EMPTY" || root.panelState === "ERROR"
            text: String(root.stateData.message || "")
            wrapMode: Text.WordWrap
            color: PATheme.Theme.textSecondary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.body
        }

        Repeater {
            model: root.results
            delegate: Rectangle {
                required property var modelData
                required property int index
                width: contentColumn.width
                height: 58
                radius: PATheme.Metrics.radius8
                color: index === Number(root.stateData.selected_index) ? PATheme.Theme.primaryPale : "transparent"
                border.width: index === Number(root.stateData.selected_index) ? 1 : 0
                border.color: PATheme.Theme.selectedBorder
                Accessible.role: Accessible.ListItem
                Accessible.name: String(modelData.entity_type || "HASIL") + " " + String(modelData.label || "")

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: if (root.viewModel) root.viewModel.activate(index)
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 10
                    Rectangle {
                        Layout.preferredWidth: 76
                        Layout.preferredHeight: 24
                        radius: 12
                        color: PATheme.Theme.primaryPale
                        Text {
                            anchors.centerIn: parent
                            text: String(modelData.entity_type || "ITEM")
                            color: PATheme.Theme.primaryStrong
                            font.family: PATheme.Typography.fontFamily
                            font.pixelSize: PATheme.Typography.meta
                            font.weight: Font.DemiBold
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            Layout.fillWidth: true
                            text: String(modelData.label || modelData.stable_id || "")
                            color: PATheme.Theme.textPrimary
                            font.family: PATheme.Typography.fontFamily
                            font.pixelSize: PATheme.Typography.body
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        Text {
                            Layout.fillWidth: true
                            text: String(modelData.context || "")
                            color: PATheme.Theme.textSecondary
                            font.family: PATheme.Typography.fontFamily
                            font.pixelSize: PATheme.Typography.meta
                            elide: Text.ElideRight
                        }
                    }
                    Text {
                        text: String(modelData.source_state || "")
                        color: modelData.source_state === "VALID" ? PATheme.Theme.success : PATheme.Theme.warning
                        font.family: PATheme.Typography.fontFamily
                        font.pixelSize: PATheme.Typography.meta
                    }
                }
            }
        }
    }
}
