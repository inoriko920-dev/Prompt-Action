import QtQuick
import QtQuick.Layouts
import "../components" as PA
import "../theme" as PATheme

Item {
    id: root
    objectName: "perPromptRevisionDetail"
    property var detail: ({})

    PA.PACard {
        anchors.fill: parent
        tone: root.detail && root.detail.file_state === "HASH_MISMATCH" ? "error" : "default"
        Flickable {
            anchors.fill: parent
            contentWidth: width
            contentHeight: detailColumn.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Column {
                id: detailColumn
                width: parent.width
                spacing: PATheme.Metrics.space12
                RowLayout {
                    width: parent.width
                    Column { Layout.fillWidth: true; spacing: 3
                        Text { text: "Detail Revision"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.sectionTitle; font.weight: Font.DemiBold }
                        Text { text: (root.detail.prompt_name || "Prompt") + " • " + (root.detail.id || "—"); color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
                    }
                    PA.PAStatusPill { visible: root.detail.active === true; text: "ACTIVE"; tone: "success" }
                    PA.PAStatusPill { visible: root.detail.selected === true && root.detail.active !== true; text: "SELECTED"; tone: "draft" }
                    PA.PAStatusPill { visible: root.detail.is_draft === true; text: "DRAFT"; tone: "draft" }
                }
                Rectangle { width: parent.width; height: 1; color: PATheme.Theme.border }
                GridLayout {
                    width: parent.width
                    columns: 2
                    columnSpacing: 14
                    rowSpacing: 8
                    Text { text: "Parent"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
                    Text { text: root.detail.parent || "—"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body }
                    Text { text: "Snapshot"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
                    Text { text: root.detail.snapshot || "—"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body }
                    Text { text: "Status"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
                    Text { text: root.detail.status || "UNKNOWN"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body }
                    Text { text: "Peran Perubahan"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
                    PA.PAStatusPill { text: root.detail.change_role || "UNKNOWN"; tone: root.detail.change_role === "PRIMARY" ? "draft" : root.detail.change_role === "SYNC" ? "warning" : "neutral" }
                }
                Column {
                    width: parent.width
                    spacing: 6
                    Text { text: "Apa yang berubah?"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.meta; font.weight: Font.Bold }
                    Repeater {
                        model: root.detail.summary && root.detail.summary.length ? root.detail.summary : ["Tidak ada change summary tambahan pada revision ini."]
                        delegate: Text { required property var modelData; width: detailColumn.width; text: "• " + modelData; wrapMode: Text.WordWrap; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body }
                    }
                }
                Column {
                    width: parent.width
                    spacing: 6
                    Text { text: "Alasan"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.meta; font.weight: Font.Bold }
                    Text { width: parent.width; text: root.detail.reason || "Tidak ada alasan tambahan."; wrapMode: Text.WordWrap; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body }
                }
                Column {
                    width: parent.width
                    spacing: 6
                    Text { text: "Dampak PRIMARY / SYNC"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.meta; font.weight: Font.Bold }
                    Text { visible: !root.detail.sync_impacts || root.detail.sync_impacts.length === 0; text: "Tidak ada dampak sinkronisasi lain pada snapshot revision ini."; width: parent.width; wrapMode: Text.WordWrap; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
                    Repeater {
                        model: root.detail.sync_impacts || []
                        delegate: Text { required property var modelData; width: detailColumn.width; text: "• " + (modelData.role || "CHANGE") + " — " + (modelData.prompt_id || "Prompt") + "  " + (modelData.from || "—") + " → " + (modelData.to || "—"); wrapMode: Text.WordWrap; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body }
                    }
                }
            }
        }
    }
}
