import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as PA
import "../theme" as PATheme

Item {
    id: root
    objectName: "backupRecoveryPage"
    property var stateOverride: null
    readonly property var vm: (typeof backupViewModel !== "undefined") ? backupViewModel : null
    readonly property var pageState: stateOverride !== null ? stateOverride : (vm ? vm.state : ({"load_state":"loading","checklist":[],"history":[],"actions":{}}))

    Item { objectName: "placeholder_backup"; visible: false }

    ScrollView {
        anchors.fill: parent
        clip: true
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            width: Math.max(root.width - 4, 940)
            spacing: PATheme.Metrics.space16

            PA.PACard {
                Layout.fillWidth: true
                implicitHeight: 136
                tone: root.pageState.recovery_health === "SAFE" ? "default" : "warning"
                RowLayout {
                    anchors.fill: parent
                    spacing: 18
                    Rectangle {
                        width: 56; height: 56; radius: 28
                        color: root.pageState.recovery_health === "SAFE" ? PATheme.Theme.successPale : PATheme.Theme.warningPale
                        Text { anchors.centerIn: parent; text: root.pageState.recovery_health === "SAFE" ? "✓" : "!"; color: root.pageState.recovery_health === "SAFE" ? PATheme.Theme.success : PATheme.Theme.warning; font.pixelSize: 28; font.bold: true }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text { text: "STATUS PEMULIHAN"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.meta; font.bold: true }
                        Text { text: root.pageState.recovery_label || "MEMUAT"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: 24; font.bold: true }
                        Text { Layout.fillWidth: true; text: root.pageState.recovery_message || "Membaca status recovery…"; wrapMode: Text.WordWrap; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body }
                    }
                    PA.PAStatusPill { text: root.pageState.snapshot_status || "LOADING"; tone: root.pageState.snapshot_status === "COMPLETE" ? "success" : "warning" }
                }
            }

            GridLayout {
                Layout.fillWidth: true
                columns: root.width < 1280 ? 1 : 2
                columnSpacing: PATheme.Metrics.space16
                rowSpacing: PATheme.Metrics.space16

                PA.PACard {
                    Layout.fillWidth: true
                    implicitHeight: 356
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 8
                        Text { text: "Kelengkapan Recovery"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.sectionTitle; font.bold: true }
                        Repeater {
                            model: root.pageState.checklist || []
                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                spacing: 10
                                Rectangle { width: 22; height: 22; radius: 11; color: modelData.ok ? PATheme.Theme.successPale : PATheme.Theme.warningPale; Text { anchors.centerIn: parent; text: modelData.ok ? "✓" : "!"; color: modelData.ok ? PATheme.Theme.success : PATheme.Theme.warning; font.bold: true } }
                                ColumnLayout { Layout.fillWidth: true; spacing: 1
                                    Text { text: modelData.label; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body }
                                    Text { Layout.fillWidth: true; text: modelData.detail; elide: Text.ElideRight; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.meta }
                                }
                            }
                        }
                    }
                }

                PA.PACard {
                    Layout.fillWidth: true
                    implicitHeight: 356
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10
                        Text { text: "Backup Terbaru"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.sectionTitle; font.bold: true }
                        Text { Layout.fillWidth: true; text: root.pageState.latest_backup ? root.pageState.latest_backup.file_name : "Belum ada Full Backup untuk snapshot aktif"; wrapMode: Text.WordWrap; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body; font.bold: true }
                        Text { text: "System " + (root.pageState.active_system || "—") + " • Snapshot " + (root.pageState.active_snapshot || "—"); color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
                        PA.PAStatusPill { text: root.pageState.latest_backup && root.pageState.latest_backup.valid ? "VALID" : "BELUM VALID"; tone: root.pageState.latest_backup && root.pageState.latest_backup.valid ? "success" : "warning" }
                        Text { text: "SHA256: " + (root.pageState.latest_backup && root.pageState.latest_backup.hash_valid ? "VALID" : "belum valid"); color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
                        Text { text: "Verifikasi ZIP: " + (root.pageState.latest_backup && root.pageState.latest_backup.verified ? "PASS" : "belum terverifikasi"); color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
                        Text { text: "Salinan kedua: " + (root.pageState.latest_backup && root.pageState.latest_backup.second_copy ? "tersedia" : "belum tersedia"); color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 8
                            PA.PAButton { text: "Download Full Backup"; variant: "secondary"; interactive: !!root.pageState.actions.can_download_backup }
                            PA.PAButton { text: "Download SHA256"; variant: "secondary"; interactive: !!root.pageState.actions.can_download_sha256 }
                            PA.PAButton { text: "Verifikasi Backup"; variant: "secondary"; interactive: !!root.pageState.actions.can_verify_backup }
                        }
                    }
                }
            }

            PA.PACard {
                Layout.fillWidth: true
                implicitHeight: 190
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 8
                    Text { text: "Riwayat Backup"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.sectionTitle; font.bold: true }
                    Repeater {
                        model: root.pageState.history || []
                        delegate: RowLayout {
                            required property var modelData
                            Layout.fillWidth: true
                            Text { Layout.fillWidth: true; text: modelData.snapshot + " • System " + modelData.system + (modelData.active ? " • AKTIF" : ""); color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body }
                            PA.PAStatusPill { text: modelData.status; tone: modelData.status === "VALID" ? "success" : modelData.status === "FAILED" ? "error" : "warning" }
                        }
                    }
                    Text { visible: (root.pageState.history || []).length === 0; text: "Belum ada riwayat snapshot."; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body }
                }
            }

            PA.PACard {
                Layout.fillWidth: true
                implicitHeight: 150
                tone: "warning"
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 8
                    Text { text: "Perubahan belum dianggap selesai sebelum Full Backup + SHA256 + verifikasi dibuat."; Layout.fillWidth: true; wrapMode: Text.WordWrap; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body; font.bold: true }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        PA.PAButton { text: "Buka Recovery Guide"; variant: "secondary"; interactive: !!root.pageState.actions.can_open_recovery_guide; onClicked: if (root.vm) root.vm.openRecoveryGuide() }
                        PA.PAButton { text: "Buka Folder Backup"; variant: "secondary"; interactive: !!root.pageState.actions.can_open_folder }
                        PA.PAButton { text: "Buat Backup Baru"; interactive: !!root.pageState.actions.can_create_backup; onClicked: if (root.vm) root.vm.requestCreateBackup() }
                        PA.PAButton { text: "Restore Backup"; variant: "secondary"; interactive: !!root.pageState.actions.can_restore_backup; onClicked: if (root.vm) root.vm.requestRestoreBackup() }
                    }
                    Text { Layout.fillWidth: true; text: !root.pageState.actions.can_create_backup ? (root.pageState.actions.disabled_reason_create || "") : ""; wrapMode: Text.WordWrap; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.meta }
                }
            }
        }
    }
}
