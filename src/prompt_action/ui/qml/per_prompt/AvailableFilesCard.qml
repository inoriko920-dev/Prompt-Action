import QtQuick
import QtQuick.Layouts
import "../components" as PA
import "../theme" as PATheme

Item {
    id: root
    objectName: "perPromptAvailableFiles"
    property var files: []
    property var capabilities: ({})
    property var detail: ({})
    signal downloadActiveRequested()
    signal downloadSelectedRequested()
    signal compareRequested()
    signal snapshotRequested()
    signal changelogRequested()
    signal addRevisionRequested()

    PA.PACard {
        anchors.fill: parent
        Column {
            anchors.fill: parent
            spacing: PATheme.Metrics.space12
            Text { text: "File Tersedia"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.sectionTitle; font.weight: Font.DemiBold }
            Repeater {
                model: root.files || []
                delegate: Rectangle {
                    required property var modelData
                    width: parent.width
                    height: 58
                    radius: PATheme.Metrics.radius8
                    color: PATheme.Theme.neutralPale
                    border.width: 1
                    border.color: PATheme.Theme.border
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        Column { Layout.fillWidth: true; spacing: 2
                            Text { text: modelData.label + " • " + modelData.revision_id; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body; font.weight: Font.DemiBold }
                            Text { text: modelData.file_name + (modelData.sha256 ? " • SHA256 " + modelData.sha256.substring(0, 12) + "…" : ""); elide: Text.ElideMiddle; width: parent.width; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.monoFamily; font.pixelSize: PATheme.Typography.meta }
                        }
                        PA.PAStatusPill { text: modelData.file_state; tone: modelData.file_state === "VALID" ? "success" : modelData.file_state === "HASH_MISMATCH" ? "error" : modelData.file_state === "MISSING" ? "warning" : "neutral" }
                    }
                }
            }
            GridLayout {
                width: parent.width
                columns: width < 900 ? 2 : 3
                columnSpacing: 8
                rowSpacing: 8
                PA.PAButton { text: "Download Prompt Aktif"; variant: "secondary"; interactive: Boolean(root.capabilities.can_download_active); Accessible.description: root.capabilities.disabled_reason_active_download || ""; Layout.fillWidth: true; onClicked: root.downloadActiveRequested() }
                PA.PAButton { text: "Download Revision Ini"; variant: "secondary"; interactive: Boolean(root.capabilities.can_download_selected); Accessible.description: root.capabilities.disabled_reason_selected_download || ""; Layout.fillWidth: true; onClicked: root.downloadSelectedRequested() }
                PA.PAButton { text: root.capabilities.compare_parent ? "Bandingkan " + root.capabilities.compare_parent + " vs " + (root.detail.id || "Revision") : "Bandingkan dengan Parent"; variant: "secondary"; interactive: Boolean(root.capabilities.can_compare); Accessible.description: root.capabilities.disabled_reason_compare || ""; Layout.fillWidth: true; onClicked: root.compareRequested() }
                PA.PAButton { text: root.detail.snapshot ? "Lihat Snapshot " + root.detail.snapshot : "Lihat Snapshot"; variant: "secondary"; interactive: Boolean(root.capabilities.can_view_snapshot); Layout.fillWidth: true; onClicked: root.snapshotRequested() }
                PA.PAButton { text: "Buka Changelog"; variant: "secondary"; interactive: Boolean(root.capabilities.can_view_changelog); Accessible.description: root.capabilities.disabled_reason_changelog || ""; Layout.fillWidth: true; onClicked: root.changelogRequested() }
                PA.PAButton { text: "Tambah Revisi"; variant: "primary"; interactive: Boolean(root.capabilities.can_add_revision); Accessible.description: root.capabilities.disabled_reason_add_revision || ""; Layout.fillWidth: true; onClicked: root.addRevisionRequested() }
            }
        }
    }
}
