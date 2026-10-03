import QtQuick
import QtQuick.Layouts
import "../components" as PA
import "../theme" as PATheme

PA.PACard {
    id: root
    property string backupHealth: "UNKNOWN"
    property string recoveryHealth: "UNKNOWN"
    property var checklist: []
    property var capabilities: ({})
    property var viewModel: null
    tone: backupHealth === "PERLU BACKUP" ? "warning" : backupHealth === "ERROR" ? "error" : "default"
    implicitHeight: 206

    Column {
        anchors.fill: parent
        spacing: 9

        RowLayout {
            width: parent.width
            Text {
                text: "Status Backup"
                color: PATheme.Theme.textPrimary
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.cardTitle
                font.weight: Font.DemiBold
                Layout.fillWidth: true
            }
            PA.PAStatusPill {
                text: root.backupHealth
                tone: root.backupHealth === "AMAN" ? "success" : root.backupHealth === "PERLU BACKUP" ? "warning" : root.backupHealth === "ERROR" ? "error" : "neutral"
            }
        }

        Repeater {
            model: root.checklist || []
            delegate: RowLayout {
                required property var modelData
                width: parent.width
                spacing: 8
                Rectangle {
                    width: 18
                    height: 18
                    radius: 9
                    color: modelData.ok ? PATheme.Theme.successPale : PATheme.Theme.neutralPale
                    border.width: 1
                    border.color: modelData.ok ? PATheme.Theme.success : PATheme.Theme.border
                    Text {
                        anchors.centerIn: parent
                        text: modelData.ok ? "✓" : "–"
                        color: modelData.ok ? PATheme.Theme.success : PATheme.Theme.textSecondary
                        font.pixelSize: 11
                        font.weight: Font.Bold
                    }
                }
                Text {
                    text: modelData.label
                    color: PATheme.Theme.textPrimary
                    font.family: PATheme.Typography.fontFamily
                    font.pixelSize: PATheme.Typography.caption
                    Layout.fillWidth: true
                }
                Text {
                    text: modelData.detail || ""
                    color: PATheme.Theme.textSecondary
                    font.family: PATheme.Typography.fontFamily
                    font.pixelSize: PATheme.Typography.caption
                    elide: Text.ElideRight
                    Layout.maximumWidth: 150
                }
            }
        }

        RowLayout {
            width: parent.width
            spacing: 8
            PA.PAButton {
                text: "Buka Backup"
                variant: "secondary"
                interactive: Boolean(root.capabilities.can_open_backup_page && root.viewModel)
                onClicked: root.viewModel.openBackupPage()
            }
            PA.PAButton {
                text: "Buat Backup Sekarang"
                variant: "primary"
                interactive: Boolean(root.capabilities.can_request_backup && root.viewModel)
                Accessible.description: root.capabilities.reason_if_disabled || ""
                onClicked: root.viewModel.requestBackupNow()
            }
        }
    }
}
