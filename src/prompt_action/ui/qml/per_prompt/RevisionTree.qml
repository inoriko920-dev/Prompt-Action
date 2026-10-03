import QtQuick
import QtQuick.Layouts
import "../components" as PA
import "../theme" as PATheme

Item {
    id: root
    objectName: "perPromptRevisionTree"
    property var officialRevisions: []
    property var drafts: []
    property string activeRevisionId: ""
    property string selectedRevisionId: ""
    signal revisionSelected(string revisionId)

    PA.PACard {
        anchors.fill: parent
        Column {
            anchors.fill: parent
            spacing: PATheme.Metrics.space12
            Text { text: "Pohon Revision"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.sectionTitle; font.weight: Font.DemiBold }
            Text { text: "ACTIVE tetap mengikuti Snapshot aktif • SELECTED hanya yang sedang dilihat"; width: parent.width; wrapMode: Text.WordWrap; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
            Flickable {
                width: parent.width
                height: Math.max(160, parent.height - 72)
                contentWidth: width
                contentHeight: treeColumn.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                Column {
                    id: treeColumn
                    width: parent.width
                    spacing: PATheme.Metrics.space8
                    Repeater {
                        model: root.officialRevisions || []
                        delegate: Column {
                            required property var modelData
                            width: treeColumn.width
                            spacing: 4
                            Rectangle {
                                width: parent.width
                                height: 64
                                radius: PATheme.Metrics.radius8
                                color: modelData.selected ? PATheme.Theme.primaryPale : PATheme.Theme.surface
                                border.width: modelData.selected ? 2 : 1
                                border.color: modelData.selected ? PATheme.Theme.primary : PATheme.Theme.border
                                Accessible.role: Accessible.Button
                                Accessible.name: "Revision " + modelData.id + (modelData.active ? ", aktif" : "") + (modelData.selected ? ", dipilih" : "")
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    Column {
                                        Layout.fillWidth: true
                                        spacing: 2
                                        Text { text: modelData.id + (modelData.parent ? "  ←  " + modelData.parent : "  • baseline"); color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.cardTitle; font.weight: Font.DemiBold }
                                        Text { text: (modelData.snapshot || "Tanpa snapshot") + " • " + (modelData.change_role || "UNKNOWN") + " • " + modelData.file_state; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.meta }
                                    }
                                    PA.PAStatusPill { visible: modelData.active; text: "ACTIVE"; tone: "success" }
                                    PA.PAStatusPill { visible: modelData.selected; text: "SELECTED"; tone: "draft" }
                                }
                                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.revisionSelected(modelData.id) }
                            }
                            Text { visible: index < (root.officialRevisions ? root.officialRevisions.length - 1 : 0); text: "↓"; width: parent.width; horizontalAlignment: Text.AlignHCenter; color: PATheme.Theme.textSecondary; font.pixelSize: 16 }
                        }
                    }
                    Rectangle { width: parent.width; height: 1; color: PATheme.Theme.border; visible: (root.drafts || []).length > 0 }
                    Text { text: "Draft / Experiment"; visible: (root.drafts || []).length > 0; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.meta; font.weight: Font.Bold }
                    Repeater {
                        model: root.drafts || []
                        delegate: Rectangle {
                            required property var modelData
                            width: treeColumn.width - 24
                            x: 24
                            height: 58
                            radius: PATheme.Metrics.radius8
                            color: modelData.selected ? PATheme.Theme.primaryPale : PATheme.Theme.neutralPale
                            border.width: 1
                            border.color: PATheme.Theme.selectedBorder
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                Column { Layout.fillWidth: true; spacing: 2
                                    Text { text: modelData.title; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body; font.weight: Font.DemiBold }
                                    Text { text: "Parent " + (modelData.parent || "—") + " • bukan nomor R resmi"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.meta }
                                }
                                PA.PAStatusPill { text: "DRAFT"; tone: "draft" }
                            }
                            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.revisionSelected(modelData.id) }
                        }
                    }
                    Text {
                        visible: (root.drafts || []).length === 0
                        text: "Belum ada draft/experiment pada canonical data."
                        width: parent.width
                        wrapMode: Text.WordWrap
                        color: PATheme.Theme.textSecondary
                        font.family: PATheme.Typography.fontFamily
                        font.pixelSize: PATheme.Typography.caption
                    }
                }
            }
        }
    }
}
