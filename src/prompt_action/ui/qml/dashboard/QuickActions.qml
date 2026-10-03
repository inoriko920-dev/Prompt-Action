import QtQuick
import QtQuick.Layouts
import "../components" as PA
import "../theme" as PATheme

PA.PACard {
    id: root
    property var state: ({})
    property var viewModel: null
    implicitHeight: 106

    RowLayout {
        anchors.fill: parent
        spacing: PATheme.Metrics.space12

        Column {
            Layout.fillWidth: true
            spacing: 4
            Text {
                text: "Aksi Cepat"
                color: PATheme.Theme.textPrimary
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.cardTitle
                font.weight: Font.DemiBold
            }
            Text {
                width: parent.width
                text: "Aksi hanya aktif bila capability tersedia."
                color: PATheme.Theme.textSecondary
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.caption
                elide: Text.ElideRight
            }
        }

        PA.PAButton {
            text: "Buka Prompt Aktif"
            variant: "secondary"
            interactive: Boolean(root.viewModel && root.state.active_prompt_count > 0)
            onClicked: root.viewModel.openActivePrompts()
        }
        PA.PAButton {
            text: "Perubahan Terakhir"
            variant: "secondary"
            interactive: Boolean(root.viewModel && root.state.action_capabilities && root.state.action_capabilities.can_open_latest_change)
            onClicked: root.viewModel.openLatestChange()
        }
        PA.PAButton {
            text: "Download Full Backup"
            variant: "secondary"
            interactive: Boolean(root.viewModel && root.state.action_capabilities && root.state.action_capabilities.can_download_full_backup)
            Accessible.description: root.state.action_capabilities ? (root.state.action_capabilities.reason_if_disabled || "") : ""
            onClicked: root.viewModel.downloadFullBackup()
        }
    }
}
