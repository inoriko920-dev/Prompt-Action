import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "../components" as PA
import "../theme" as PATheme

Dialog {
    id: root
    objectName: "addRevisionDialog"
    property var viewModel: null
    readonly property var stateData: viewModel ? viewModel.state : ({})
    property string pendingSyncFile: ""
    modal: true
    focus: true
    width: 880
    height: 720
    closePolicy: Popup.NoAutoClose
    title: "Tambah Revisi"

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
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    text: "Release Revision + Snapshot"
                    color: PATheme.Theme.textPrimary
                    font.family: PATheme.Typography.fontFamily
                    font.pixelSize: PATheme.Typography.sectionTitle
                    font.weight: Font.DemiBold
                }
                Text {
                    text: "Import TXT • bukan editor Prompt • hasil STEP 10 selalu BACKUP_REQUIRED"
                    color: PATheme.Theme.textSecondary
                    font.family: PATheme.Typography.fontFamily
                    font.pixelSize: PATheme.Typography.caption
                }
            }
            PA.PAStatusPill {
                text: String(root.stateData.availability && root.stateData.availability.active_snapshot ? root.stateData.availability.active_snapshot : "Gate")
                tone: root.stateData.availability && root.stateData.availability.can_start ? "success" : "warning"
            }
        }

        PA.PAErrorBanner {
            Layout.fillWidth: true
            visible: Boolean(root.stateData.error_message)
            text: (root.stateData.error_code ? String(root.stateData.error_code) + " • " : "") + String(root.stateData.error_message || "")
        }

        Rectangle {
            Layout.fillWidth: true
            visible: root.stateData.stage === "blocked"
            implicitHeight: blockedColumn.implicitHeight + 24
            radius: PATheme.Metrics.radius8
            color: PATheme.Theme.neutralPale
            border.width: 1
            border.color: PATheme.Theme.border
            ColumnLayout {
                id: blockedColumn
                anchors.fill: parent
                anchors.margins: 12
                Text {
                    Layout.fillWidth: true
                    text: String(root.stateData.availability && root.stateData.availability.reason || "Release diblokir.")
                    color: PATheme.Theme.textPrimary
                    wrapMode: Text.WordWrap
                    font.family: PATheme.Typography.fontFamily
                    font.pixelSize: PATheme.Typography.body
                }
                RowLayout {
                    visible: Boolean(root.stateData.availability && root.stateData.availability.recovery_txn_id)
                    PA.PAButton { text: "Resume Recovery"; variant: "primary"; onClicked: if (root.viewModel) root.viewModel.recover("resume") }
                    PA.PAButton { text: "Abort Recovery"; variant: "secondary"; onClicked: if (root.viewModel) root.viewModel.recover("abort") }
                }
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.stateData.stage !== "blocked"
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: PATheme.Metrics.space16

                Text {
                    text: "1. Primary Revision"
                    color: PATheme.Theme.textPrimary
                    font.family: PATheme.Typography.fontFamily
                    font.pixelSize: PATheme.Typography.sectionTitle
                    font.weight: Font.DemiBold
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 12
                    rowSpacing: 8
                    Text { text: "Prompt PRIMARY"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily }
                    ComboBox {
                        id: primaryCombo
                        Layout.fillWidth: true
                        model: root.stateData.prompt_options || []
                        textRole: "display_name"
                        valueRole: "id"
                        Component.onCompleted: {
                            for (var i = 0; i < count; ++i) if (valueAt(i) === root.stateData.primary_prompt_id) currentIndex = i
                        }
                        onActivated: if (root.viewModel && currentValue) root.viewModel.selectPrimaryPrompt(String(currentValue))
                    }
                    Text { text: "Revision aktif"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily }
                    Text { text: String(root.stateData.primary_active_revision || "—"); color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.monoFamily; font.weight: Font.DemiBold }
                    Text { text: "TXT baru"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily }
                    RowLayout {
                        Layout.fillWidth: true
                        TextField {
                            Layout.fillWidth: true
                            readOnly: true
                            placeholderText: "Belum ada file dipilih"
                            text: String(root.stateData.primary_source_name || "")
                            Accessible.name: "File TXT PRIMARY"
                        }
                        PA.PAButton { text: "Pilih TXT"; variant: "secondary"; onClicked: primaryFileDialog.open() }
                    }
                }

                Text { text: "Ringkasan perubahan"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily }
                TextArea {
                    id: summaryField
                    Layout.fillWidth: true
                    implicitHeight: 72
                    placeholderText: "Contoh: memperbarui aturan Prompt 3 untuk alur baru"
                    wrapMode: TextEdit.Wrap
                    text: String(root.stateData.summary || "")
                    onTextChanged: if (root.viewModel && activeFocus) root.viewModel.setSummary(text)
                    background: Rectangle { color: PATheme.Theme.neutralPale; radius: PATheme.Metrics.radius8; border.width: 1; border.color: PATheme.Theme.border }
                }

                Text { text: "Alasan teknis / intent *"; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily }
                TextArea {
                    id: reasonField
                    Layout.fillWidth: true
                    implicitHeight: 76
                    placeholderText: "Wajib. Jelaskan mengapa Revision baru diperlukan."
                    wrapMode: TextEdit.Wrap
                    text: String(root.stateData.reason || "")
                    onTextChanged: if (root.viewModel && activeFocus) root.viewModel.setReason(text)
                    background: Rectangle { color: PATheme.Theme.neutralPale; radius: PATheme.Metrics.radius8; border.width: 1; border.color: PATheme.Theme.border }
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: PATheme.Theme.border }
                Text {
                    text: "2. Sync / Affected (opsional)"
                    color: PATheme.Theme.textPrimary
                    font.family: PATheme.Typography.fontFamily
                    font.pixelSize: PATheme.Typography.sectionTitle
                    font.weight: Font.DemiBold
                }
                Text {
                    Layout.fillWidth: true
                    text: "Tambahkan hanya Prompt lain yang file aktualnya ikut berubah. Prompt yang hanya terdampak secara konsep tidak mendapat Revision baru."
                    color: PATheme.Theme.textSecondary
                    font.family: PATheme.Typography.fontFamily
                    font.pixelSize: PATheme.Typography.caption
                    wrapMode: Text.WordWrap
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 12
                    rowSpacing: 8
                    ComboBox {
                        id: syncCombo
                        Layout.fillWidth: true
                        model: root.stateData.prompt_options || []
                        textRole: "display_name"
                        valueRole: "id"
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        TextField { Layout.fillWidth: true; readOnly: true; text: root.pendingSyncFile ? root.pendingSyncFile.split(/[\\/]/).pop() : ""; placeholderText: "TXT SYNC" }
                        PA.PAButton { text: "Pilih TXT"; variant: "secondary"; onClicked: syncFileDialog.open() }
                    }
                    TextField {
                        id: syncReason
                        Layout.columnSpan: 2
                        Layout.fillWidth: true
                        placeholderText: "Alasan SYNC (opsional; default mengikuti alasan PRIMARY)"
                    }
                    PA.PAButton {
                        text: "Tambahkan SYNC"
                        variant: "secondary"
                        interactive: Boolean(syncCombo.currentValue) && root.pendingSyncFile.length > 0
                        onClicked: {
                            if (!root.viewModel) return
                            root.viewModel.addSync(String(syncCombo.currentValue), root.pendingSyncFile, syncReason.text)
                            root.pendingSyncFile = ""
                            syncReason.text = ""
                        }
                    }
                }

                Repeater {
                    model: root.stateData.sync_changes || []
                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true
                        implicitHeight: 62
                        radius: PATheme.Metrics.radius8
                        color: PATheme.Theme.neutralPale
                        border.width: 1
                        border.color: PATheme.Theme.border
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: modelData.display_name + " • " + modelData.active_revision + " → next R"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.weight: Font.DemiBold }
                                Text { text: modelData.source_name; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.monoFamily; elide: Text.ElideMiddle; Layout.fillWidth: true }
                            }
                            PA.PAButton { text: "Hapus"; variant: "secondary"; onClicked: if (root.viewModel) root.viewModel.removeSync(modelData.prompt_id) }
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            PA.PAButton {
                text: "Batal"
                variant: "secondary"
                onClicked: {
                    if (root.viewModel) root.viewModel.reset()
                    root.close()
                }
            }
            PA.PAButton {
                text: "Review Release"
                variant: "primary"
                interactive: root.stateData.stage !== "blocked" && Boolean(root.stateData.primary_source_name) && String(root.stateData.reason || "").trim().length > 0
                onClicked: if (root.viewModel) root.viewModel.planRelease()
            }
        }
    }

    FileDialog {
        id: primaryFileDialog
        title: "Pilih TXT PRIMARY"
        nameFilters: ["Text files (*.txt)"]
        fileMode: FileDialog.OpenFile
        onAccepted: if (root.viewModel) root.viewModel.setPrimarySource(selectedFile.toString())
    }
    FileDialog {
        id: syncFileDialog
        title: "Pilih TXT SYNC"
        nameFilters: ["Text files (*.txt)"]
        fileMode: FileDialog.OpenFile
        onAccepted: root.pendingSyncFile = selectedFile.toString()
    }
}
