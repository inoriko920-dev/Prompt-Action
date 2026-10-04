import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as PA
import "../theme" as PATheme

Dialog {
    id: root
    objectName: "releaseReviewDialog"
    property var viewModel: null
    readonly property var stateData: viewModel ? viewModel.state : ({})
    readonly property var plan: stateData.plan || ({})
    modal: true
    focus: true
    width: 860
    height: 650
    closePolicy: Popup.NoAutoClose
    title: "Review Release"

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
                Text { text: "3. Review & Compare"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.sectionTitle; font.weight: Font.DemiBold }
                Text { text: "Periksa Revision, Snapshot, file, dan warning sebelum commit resmi."; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption }
            }
            PA.PAStatusPill { text: String(root.plan.snapshot_id || "—") + " • BACKUP_REQUIRED"; tone: "warning" }
        }

        PA.PAErrorBanner {
            Layout.fillWidth: true
            visible: Boolean(root.stateData.error_message)
            text: (root.stateData.error_code ? String(root.stateData.error_code) + " • " : "") + String(root.stateData.error_message || "")
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            ColumnLayout {
                width: parent.width
                spacing: 12

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: primaryCol.implicitHeight + 24
                    radius: PATheme.Metrics.radius8
                    color: PATheme.Theme.neutralPale
                    border.width: 1
                    border.color: PATheme.Theme.border
                    ColumnLayout {
                        id: primaryCol
                        anchors.fill: parent
                        anchors.margins: 12
                        Text { text: "PRIMARY CHANGE"; color: PATheme.Theme.primaryStrong; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption; font.weight: Font.Bold }
                        Text {
                            text: String(root.plan.primary && root.plan.primary.prompt_id || "—") + " • " + String(root.plan.primary && root.plan.primary.from_revision || "—") + " → " + String(root.plan.primary && root.plan.primary.to_revision || "—")
                            color: PATheme.Theme.textPrimary
                            font.family: PATheme.Typography.fontFamily
                            font.pixelSize: PATheme.Typography.body
                            font.weight: Font.DemiBold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: String(root.plan.primary && root.plan.primary.target_relative || "")
                            color: PATheme.Theme.textSecondary
                            font.family: PATheme.Typography.monoFamily
                            font.pixelSize: PATheme.Typography.meta
                            elide: Text.ElideMiddle
                        }
                        Text {
                            text: "SHA256 " + String(root.plan.primary && root.plan.primary.source_sha256 ? root.plan.primary.source_sha256.substring(0, 20) + "…" : "—")
                            color: PATheme.Theme.textSecondary
                            font.family: PATheme.Typography.monoFamily
                            font.pixelSize: PATheme.Typography.meta
                        }
                    }
                }

                Text { text: "SYNC CHANGE"; visible: (root.plan.sync || []).length > 0; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.weight: Font.DemiBold }
                Repeater {
                    model: root.plan.sync || []
                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true
                        implicitHeight: 68
                        radius: PATheme.Metrics.radius8
                        color: PATheme.Theme.neutralPale
                        border.width: 1
                        border.color: PATheme.Theme.border
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            Text { text: modelData.prompt_id + " • " + modelData.from_revision + " → " + modelData.to_revision; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.weight: Font.DemiBold }
                            Text { Layout.fillWidth: true; text: modelData.target_relative; elide: Text.ElideMiddle; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.monoFamily; font.pixelSize: PATheme.Typography.meta }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    visible: (root.stateData.warnings || []).length > 0
                    implicitHeight: warningCol.implicitHeight + 24
                    radius: PATheme.Metrics.radius8
                    color: PATheme.Theme.warningPale || PATheme.Theme.neutralPale
                    border.width: 1
                    border.color: PATheme.Theme.border
                    ColumnLayout {
                        id: warningCol
                        anchors.fill: parent
                        anchors.margins: 12
                        Text { text: "Warning"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.weight: Font.DemiBold }
                        Repeater {
                            model: root.stateData.warnings || []
                            delegate: Text { required property var modelData; Layout.fillWidth: true; text: "• " + String(modelData); color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; wrapMode: Text.WordWrap }
                        }
                    }
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: PATheme.Theme.border }
                Text {
                    Layout.fillWidth: true
                    text: "4. Confirm Release\nCommit akan membuat file Revision immutable dan Snapshot " + String(root.plan.snapshot_id || "baru") + ". Snapshot TIDAK langsung aman: status setelah STEP 10 adalah BACKUP_REQUIRED dan release berikutnya diblok sampai STEP 11 selesai."
                    color: PATheme.Theme.textPrimary
                    font.family: PATheme.Typography.fontFamily
                    font.pixelSize: PATheme.Typography.body
                    wrapMode: Text.WordWrap
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
                text: "Konfirmasi & Release"
                variant: "primary"
                interactive: root.stateData.stage === "review"
                onClicked: if (root.viewModel) root.viewModel.commitRelease()
            }
        }
    }
}
