import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme" as PATheme
import "../components" as PA

Dialog {
    id: root
    objectName: "compareSnapshotDialog"
    property var compareData: ({})
    modal: true
    focus: true
    width: 800
    height: 600
    closePolicy: Popup.CloseOnEscape
    standardButtons: Dialog.Close
    title: "Bandingkan Snapshot"

    background: Rectangle {
        color: PATheme.Theme.surface
        radius: PATheme.Metrics.radius16
        border.width: 1
        border.color: PATheme.Theme.border
    }

    contentItem: ColumnLayout {
        spacing: PATheme.Metrics.space12
        RowLayout {
            Layout.fillWidth: true
            Text {
                Layout.fillWidth: true
                text: String(root.compareData.left_snapshot || "—") + " vs " + String(root.compareData.right_snapshot || "—")
                color: PATheme.Theme.textPrimary
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.sectionTitle
                font.weight: Font.DemiBold
            }
            PA.PAStatusPill {
                text: root.compareData.cross_system_warning ? "BEDA SYSTEM" : String(root.compareData.right_system || "SYSTEM")
                tone: root.compareData.cross_system_warning ? "warning" : "draft"
            }
        }
        Text {
            Layout.fillWidth: true
            text: String(root.compareData.summary || "")
            color: PATheme.Theme.textSecondary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.body
        }
        Rectangle { Layout.fillWidth: true; height: 1; color: PATheme.Theme.border }
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Column {
                width: parent.width
                spacing: 8
                Repeater {
                    model: root.compareData.changed || []
                    delegate: Rectangle {
                        required property var modelData
                        width: parent.width
                        height: 54
                        radius: PATheme.Metrics.radius8
                        color: PATheme.Theme.neutralPale
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            Text { text: String(modelData.prompt_id || ""); color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body; font.weight: Font.DemiBold; Layout.preferredWidth: 110 }
                            Text { text: String(modelData.from || "—") + "  →  " + String(modelData.to || "—"); color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body; Layout.fillWidth: true }
                            PA.PAStatusPill { text: String(modelData.role || "CHANGE"); tone: modelData.role === "PRIMARY" ? "draft" : modelData.role === "SYNC" ? "warning" : "neutral" }
                        }
                    }
                }
                Text {
                    visible: !(root.compareData.changed || []).length
                    width: parent.width
                    text: "Tidak ada perubahan composition map."
                    color: PATheme.Theme.textSecondary
                    font.family: PATheme.Typography.fontFamily
                    font.pixelSize: PATheme.Typography.body
                }
            }
        }
        Text {
            Layout.fillWidth: true
            text: "Read-only • composition map canonical • tidak ada tombol mutasi"
            color: PATheme.Theme.textSecondary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.caption
        }
    }
}
