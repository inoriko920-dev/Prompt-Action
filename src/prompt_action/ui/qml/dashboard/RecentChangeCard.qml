import QtQuick
import QtQuick.Layouts
import "../components" as PA
import "../theme" as PATheme

PA.PACard {
    id: root
    property var latestChange: ({})
    property var viewModel: null
    implicitHeight: 206

    Column {
        anchors.fill: parent
        spacing: PATheme.Metrics.space12

        RowLayout {
            width: parent.width
            Text {
                text: "Perubahan Terakhir"
                color: PATheme.Theme.textPrimary
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.cardTitle
                font.weight: Font.DemiBold
                Layout.fillWidth: true
            }
            PA.PAStatusPill {
                text: root.latestChange.primary_change ? "PRIMARY" : "BASELINE"
                tone: root.latestChange.primary_change ? "draft" : "neutral"
            }
        }

        Text {
            width: parent.width
            text: root.latestChange.display_title || "Belum ada perubahan"
            color: PATheme.Theme.textPrimary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.body
            font.weight: Font.DemiBold
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            elide: Text.ElideRight
        }

        Text {
            width: parent.width
            text: root.latestChange.reason_summary || "Tidak ada ringkasan perubahan."
            color: PATheme.Theme.textSecondary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.caption
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            elide: Text.ElideRight
        }

        Row {
            width: parent.width
            spacing: 8
            visible: Boolean(root.latestChange.sync_changes && root.latestChange.sync_changes.length > 0)
            Repeater {
                model: root.latestChange.sync_changes || []
                delegate: PA.PABadge {
                    required property var modelData
                    text: "SYNC " + (modelData.prompt_id || "")
                }
            }
        }

        Item { width: 1; height: 1 }

        RowLayout {
            width: parent.width
            Text {
                Layout.fillWidth: true
                text: root.latestChange.occurred_at ? root.latestChange.occurred_at : "Waktu tidak tercatat"
                color: PATheme.Theme.textSecondary
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.caption
            }
            PA.PAButton {
                text: "Lihat Snapshot"
                variant: "secondary"
                interactive: Boolean(root.latestChange.can_open_snapshot && root.viewModel)
                accessibleName: "Lihat snapshot perubahan terakhir"
                onClicked: root.viewModel.openSnapshot(root.latestChange.snapshot_id || "")
            }
        }
    }
}
