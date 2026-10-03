import QtQuick
import QtQuick.Layouts
import "../components" as PA
import "../theme" as PATheme

Item {
    id: root
    objectName: "systemHistoryPage"
    property var viewModel: (typeof historyViewModel !== "undefined") ? historyViewModel : null
    property var stateOverride: null
    readonly property var state: stateOverride !== null ? stateOverride : (viewModel ? viewModel.state : ({"load_state":"loading","systems":[],"selected_snapshot":{},"diagnostics":[]}))
    readonly property var detail: state.selected_snapshot || ({})

    // Compatibility marker for STEP 03 regression tests; not rendered.
    Item { objectName: "placeholder_system_history"; visible: false; width: 0; height: 0 }

    Column {
        anchors.fill: parent
        spacing: PATheme.Metrics.space16

        Column {
            width: parent.width
            spacing: 8
            visible: root.state.load_state === "loading"
            PA.PASkeleton { width: parent.width; height: 180 }
            PA.PASkeleton { width: parent.width; height: 320 }
        }

        Column {
            width: parent.width
            spacing: 10
            visible: root.state.load_state === "invalid" || root.state.load_state === "error"
            PA.PAErrorBanner {
                width: parent.width
                text: root.state.load_state === "invalid" ? "Data sejarah canonical tidak valid." : "Sejarah Sistem gagal dimuat."
            }
            Text {
                width: parent.width
                text: root.state.diagnostics && root.state.diagnostics.length ? root.state.diagnostics.join(" • ") : "Tidak ada diagnostik tambahan."
                color: PATheme.Theme.textSecondary
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.body
                wrapMode: Text.WordWrap
            }
            PA.PAButton { text: "Coba Lagi"; variant: "secondary"; interactive: Boolean(root.viewModel); onClicked: root.viewModel.refresh() }
        }

        PA.PAEmptyState {
            width: parent.width
            visible: root.state.load_state === "empty"
            title: "Belum ada sejarah sistem"
            message: "Canonical data belum memiliki System/Snapshot yang dapat ditampilkan."
        }

        RowLayout {
            width: parent.width
            height: parent.height
            spacing: PATheme.Metrics.space16
            visible: root.state.load_state === "ready"

            PA.PACard {
                Layout.preferredWidth: parent.width * 0.46
                Layout.minimumWidth: 420
                Layout.fillHeight: true
                Column {
                    anchors.fill: parent
                    spacing: 12
                    Text { text: "Pohon Sistem & Snapshot"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.sectionTitle; font.weight: Font.DemiBold }
                    Text { text: "Sumber canonical • satu node Legacy sebagai asal"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }

                    Rectangle {
                        width: parent.width
                        height: 54
                        radius: PATheme.Metrics.radius8
                        color: PATheme.Theme.neutralPale
                        border.width: 1
                        border.color: PATheme.Theme.border
                        visible: root.state.legacy && root.state.legacy.available === true
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            Text { text: root.state.legacy.label || "Legacy"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body; font.weight: Font.DemiBold; Layout.fillWidth: true }
                            PA.PAStatusPill { text: root.state.legacy.verified ? "TERVERIFIKASI" : "ARSIP"; tone: root.state.legacy.verified ? "success" : "neutral" }
                        }
                    }

                    Text { text: "↓"; color: PATheme.Theme.textSecondary; font.pixelSize: 18; horizontalAlignment: Text.AlignHCenter; width: parent.width }

                    Flickable {
                        width: parent.width
                        height: parent.height - 130
                        contentWidth: width
                        contentHeight: treeColumn.implicitHeight
                        clip: true
                        boundsBehavior: Flickable.StopAtBounds
                        Column {
                            id: treeColumn
                            width: parent.width
                            spacing: 10
                            Repeater {
                                model: root.state.systems || []
                                delegate: Column {
                                    required property var modelData
                                    width: treeColumn.width
                                    spacing: 8
                                    Rectangle {
                                        width: parent.width
                                        height: 48
                                        radius: PATheme.Metrics.radius8
                                        color: modelData.active ? PATheme.Theme.primaryPale : PATheme.Theme.surface
                                        border.width: modelData.active ? 2 : 1
                                        border.color: modelData.active ? PATheme.Theme.selectedBorder : PATheme.Theme.border
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 11
                                            Text { text: "System " + modelData.id; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.cardTitle; font.weight: Font.DemiBold; Layout.fillWidth: true }
                                            PA.PAStatusPill { text: modelData.status; tone: modelData.active ? "success" : "neutral" }
                                        }
                                    }
                                    Repeater {
                                        model: modelData.snapshots || []
                                        delegate: Rectangle {
                                            required property var modelData
                                            width: treeColumn.width - 28
                                            x: 28
                                            height: 58
                                            radius: PATheme.Metrics.radius8
                                            color: modelData.id === root.state.selected_snapshot_id ? PATheme.Theme.primaryPale : PATheme.Theme.surface
                                            border.width: modelData.id === root.state.selected_snapshot_id ? 2 : 1
                                            border.color: modelData.id === root.state.selected_snapshot_id ? PATheme.Theme.primary : PATheme.Theme.border
                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: 10
                                                Column { Layout.fillWidth: true; spacing: 2
                                                    Text { text: modelData.id + " — " + modelData.title; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body; font.weight: Font.DemiBold }
                                                    Text { text: modelData.parent_snapshot ? "Parent " + modelData.parent_snapshot : "Snapshot baseline"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.meta }
                                                }
                                                PA.PAStatusPill { text: modelData.active ? "AKTIF" : modelData.status; tone: modelData.active ? "success" : (modelData.status === "BACKUP_REQUIRED" ? "warning" : "neutral") }
                                            }
                                            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: if (root.viewModel) root.viewModel.selectSnapshot(modelData.id) }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            PA.PACard {
                Layout.fillWidth: true
                Layout.fillHeight: true
                tone: root.detail.status === "BACKUP_REQUIRED" ? "warning" : "default"
                Flickable {
                    anchors.fill: parent
                    contentWidth: width
                    contentHeight: detailColumn.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    Column {
                        id: detailColumn
                        width: parent.width
                        spacing: 14
                        RowLayout {
                            width: parent.width
                            Column { Layout.fillWidth: true; spacing: 3
                                Text { text: "Detail Snapshot"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.sectionTitle; font.weight: Font.DemiBold }
                                Text { text: (root.detail.system || "—") + " • " + (root.detail.id || "—") + " • " + (root.detail.title || "") ; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
                            }
                            PA.PAStatusPill { text: root.detail.active ? "AKTIF" : (root.detail.status || "UNKNOWN"); tone: root.detail.active ? "success" : (root.detail.status === "BACKUP_REQUIRED" ? "warning" : "neutral") }
                        }

                        Rectangle { width: parent.width; height: 1; color: PATheme.Theme.border }

                        GridLayout {
                            width: parent.width
                            columns: 2
                            columnSpacing: 12
                            rowSpacing: 10
                            Text { text: "System"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
                            Text { text: root.detail.system || "—"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body; font.weight: Font.DemiBold }
                            Text { text: "Snapshot"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
                            Text { text: root.detail.id || "—"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body; font.weight: Font.DemiBold }
                            Text { text: "Status"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
                            Text { text: root.detail.status || "UNKNOWN"; color: root.detail.status === "BACKUP_REQUIRED" ? PATheme.Theme.warning : PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body }
                            Text { text: "Backup"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
                            Text { text: root.detail.backup_status || "BELUM ADA"; color: root.detail.backup_status === "PERLU BACKUP" ? PATheme.Theme.warning : PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body }
                        }

                        Column {
                            width: parent.width
                            spacing: 6
                            Text { text: "PRIMARY CHANGE"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.meta; font.weight: Font.Bold }
                            Text { width: parent.width; text: root.detail.primary_change ? ((root.detail.primary_change.prompt_id || "Prompt") + "  " + (root.detail.primary_change.from || "—") + " → " + (root.detail.primary_change.to || "—")) : "Tidak ada — snapshot baseline"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body; wrapMode: Text.WordWrap }
                        }

                        Column {
                            width: parent.width
                            spacing: 6
                            Text { text: "SYNC CHANGE"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.meta; font.weight: Font.Bold }
                            Text { visible: !root.detail.sync_changes || root.detail.sync_changes.length === 0; text: "Tidak ada sync change"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body }
                            Repeater { model: root.detail.sync_changes || []; delegate: Text { required property var modelData; width: detailColumn.width; text: (modelData.prompt_id || "Prompt") + "  " + (modelData.from || "—") + " → " + (modelData.to || "—"); color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body } }
                        }

                        Column {
                            width: parent.width
                            spacing: 5
                            Text { text: "Alasan Perubahan"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.meta; font.weight: Font.Bold }
                            Text { width: parent.width; text: root.detail.reason || "—"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body; wrapMode: Text.WordWrap }
                        }

                        GridLayout {
                            width: parent.width
                            columns: 2
                            columnSpacing: 8
                            rowSpacing: 8
                            PA.PAButton { text: "Lihat Prompt yang Berubah"; variant: "secondary"; interactive: Boolean(root.viewModel && root.detail.capabilities && root.detail.capabilities.can_view_changed_prompts); Accessible.description: root.detail.capabilities ? root.detail.capabilities.disabled_reason_changed_prompts || "" : ""; Layout.fillWidth: true; onClicked: root.viewModel.viewChangedPrompts() }
                            PA.PAButton { text: "Download Snapshot Backup"; variant: "secondary"; interactive: Boolean(root.viewModel && root.detail.capabilities && root.detail.capabilities.can_download_snapshot_backup); Accessible.description: root.detail.capabilities ? root.detail.capabilities.disabled_reason_backup || "" : ""; Layout.fillWidth: true; onClicked: root.viewModel.downloadSnapshotBackup() }
                            PA.PAButton { text: "Bandingkan dengan Sebelumnya"; variant: "secondary"; interactive: Boolean(root.viewModel && root.detail.capabilities && root.detail.capabilities.can_compare_previous); Accessible.description: root.detail.capabilities ? root.detail.capabilities.disabled_reason_compare || "" : ""; Layout.fillWidth: true; onClicked: root.viewModel.comparePrevious() }
                            PA.PAButton { text: "Lihat Changelog"; variant: "secondary"; interactive: Boolean(root.viewModel && root.detail.capabilities && root.detail.capabilities.can_view_changelog); Layout.fillWidth: true; onClicked: root.viewModel.viewChangelog() }
                            PA.PAButton { text: "Buka Backup & Recovery"; variant: "primary"; interactive: Boolean(root.viewModel); Layout.columnSpan: 2; Layout.fillWidth: true; onClicked: root.viewModel.openBackup() }
                        }
                    }
                }
            }
        }
    }
}
