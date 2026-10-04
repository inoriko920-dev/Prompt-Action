import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as PA
import "../theme" as PATheme

Dialog {
    id: root
    objectName: "releaseResultDialog"
    property var viewModel: null
    readonly property var stateData: viewModel ? viewModel.state : ({})
    readonly property bool success: stateData.stage === "success"
    readonly property bool recoveryMode: stateData.stage === "recovery_required"
    modal: true
    focus: true
    width: 620
    height: 430
    closePolicy: Popup.NoAutoClose
    title: success ? "Release Berhasil" : recoveryMode ? "Recovery Diperlukan" : "Release Gagal"

    background: Rectangle {
        color: PATheme.Theme.surface
        radius: PATheme.Metrics.radius16
        border.width: 1
        border.color: PATheme.Theme.border
    }

    contentItem: ColumnLayout {
        spacing: PATheme.Metrics.space12

        PA.PAStatusPill {
            Layout.alignment: Qt.AlignHCenter
            text: root.success ? "COMMITTED • BACKUP_REQUIRED" : root.recoveryMode ? "RECOVERY_REQUIRED" : String(root.stateData.error_code || "ERROR")
            tone: root.success ? "warning" : "error"
        }

        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: root.success ? "5. Result — Snapshot resmi sudah tercatat" : root.recoveryMode ? "Outcome transaksi belum boleh dianggap sukses atau gagal" : "Release tidak berhasil"
            color: PATheme.Theme.textPrimary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.sectionTitle
            font.weight: Font.DemiBold
            wrapMode: Text.WordWrap
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: resultColumn.implicitHeight + 24
            radius: PATheme.Metrics.radius8
            color: root.success ? PATheme.Theme.warningPale : PATheme.Theme.errorPale
            border.width: 1
            border.color: root.success ? PATheme.Theme.warning : PATheme.Theme.error
            ColumnLayout {
                id: resultColumn
                anchors.fill: parent
                anchors.margins: 12
                visible: root.success
                Text { text: "Snapshot: " + String(root.stateData.result && root.stateData.result.snapshot_id || "—"); color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.weight: Font.DemiBold }
                Text { text: "Status: BACKUP_REQUIRED"; color: PATheme.Theme.warning; font.family: PATheme.Typography.fontFamily; font.weight: Font.Bold }
                Text { Layout.fillWidth: true; text: "Revision baru sudah ACTIVE sesuai snapshot ini. Release berikutnya diblok sampai STEP 11 membuat Full Backup, SHA256, verifikasi ZIP, dan salinan kedua lalu mengubah status menjadi COMPLETE."; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; wrapMode: Text.WordWrap }
            }
            Text {
                anchors.fill: parent
                anchors.margins: 12
                visible: !root.success
                text: (root.stateData.error_code ? String(root.stateData.error_code) + "\n" : "") + String(root.stateData.error_message || "Tidak ada detail tambahan.")
                color: PATheme.Theme.textPrimary
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.body
                wrapMode: Text.WordWrap
            }
        }

        RowLayout {
            Layout.fillWidth: true
            visible: root.recoveryMode
            Item { Layout.fillWidth: true }
            PA.PAButton { text: "Abort Aman"; variant: "secondary"; onClicked: if (root.viewModel) root.viewModel.recover("abort") }
            PA.PAButton { text: "Resume & Verifikasi"; variant: "primary"; onClicked: if (root.viewModel) root.viewModel.recover("resume") }
            Item { Layout.fillWidth: true }
        }

        Item { Layout.fillHeight: true }
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            PA.PAButton {
                text: root.success ? "Tutup" : "Kembali"
                variant: root.success ? "primary" : "secondary"
                visible: !root.recoveryMode
                onClicked: {
                    if (root.viewModel) root.viewModel.reset()
                    root.close()
                }
            }
        }
    }
}
