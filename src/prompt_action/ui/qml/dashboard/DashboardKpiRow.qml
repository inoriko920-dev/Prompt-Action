import QtQuick
import "../components" as PA
import "../theme" as PATheme

Item {
    id: root
    property var state: ({})
    implicitHeight: grid.implicitHeight

    function backupTone(value) {
        if (value === "AMAN") return "default"
        if (value === "PERLU BACKUP") return "warning"
        if (value === "ERROR") return "error"
        return "default"
    }

    Grid {
        id: grid
        width: parent.width
        columns: width >= 900 ? 4 : 2
        spacing: PATheme.Metrics.space12

        Repeater {
            model: [
                { label: "System Aktif", value: root.state.system_label || "—", caption: "System canonical", tone: "default" },
                { label: "Snapshot Aktif", value: root.state.snapshot_label || "—", caption: "Snapshot canonical", tone: "default" },
                { label: "Prompt Aktif", value: String(root.state.active_prompt_count ?? 0), caption: "Resolved revision aktif", tone: "default" },
                { label: "Backup", value: root.state.backup_health || "UNKNOWN", caption: "Recovery readiness", tone: root.backupTone(root.state.backup_health) }
            ]

            delegate: PA.PACard {
                required property var modelData
                width: (grid.width - (grid.columns - 1) * grid.spacing) / grid.columns
                height: 104
                tone: modelData.tone

                Column {
                    anchors.fill: parent
                    spacing: 6
                    Text {
                        text: modelData.label
                        color: PATheme.Theme.textSecondary
                        font.family: PATheme.Typography.fontFamily
                        font.pixelSize: PATheme.Typography.caption
                    }
                    Text {
                        width: parent.width
                        text: modelData.value
                        color: PATheme.Theme.textPrimary
                        font.family: PATheme.Typography.fontFamily
                        font.pixelSize: PATheme.Typography.pageTitle
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Text {
                        width: parent.width
                        text: modelData.caption
                        color: PATheme.Theme.textSecondary
                        font.family: PATheme.Typography.fontFamily
                        font.pixelSize: PATheme.Typography.caption
                        elide: Text.ElideRight
                    }
                }
            }
        }
    }
}
