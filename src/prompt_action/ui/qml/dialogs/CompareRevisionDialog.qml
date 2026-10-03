import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme" as PATheme
import "../components" as PA

Dialog {
    id: root
    objectName: "compareRevisionDialog"
    property var compareData: ({})
    modal: true
    focus: true
    width: 820
    height: 620
    closePolicy: Popup.CloseOnEscape
    standardButtons: Dialog.Close
    title: "Bandingkan Revision"

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
            Text {
                Layout.fillWidth: true
                text: String(root.compareData.prompt_id || "Prompt") + " • " + String(root.compareData.left_revision || "—") + " vs " + String(root.compareData.right_revision || "—")
                color: PATheme.Theme.textPrimary
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.sectionTitle
                font.weight: Font.DemiBold
            }
            PA.PAStatusPill {
                text: root.compareData.eol_only ? "EOL ONLY" : root.compareData.whitespace_only ? "FORMAT" : String(root.compareData.status || "READ ONLY")
                tone: root.compareData.status === "SAME" ? "neutral" : "draft"
            }
        }
        Text {
            Layout.fillWidth: true
            text: "Read-only • source diverifikasi sebelum diff • tidak membuat Revision baru"
            color: PATheme.Theme.textSecondary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.caption
        }
        Rectangle { Layout.fillWidth: true; height: 1; color: PATheme.Theme.border }
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            TextArea {
                objectName: "revisionDiffText"
                readOnly: true
                wrapMode: TextEdit.NoWrap
                text: String(root.compareData.unified_diff || "Tidak ada perubahan isi.")
                color: PATheme.Theme.textPrimary
                background: Rectangle { color: PATheme.Theme.neutralPale; radius: PATheme.Metrics.radius8 }
                font.family: PATheme.Typography.monoFamily
                font.pixelSize: PATheme.Typography.caption
                Accessible.name: "Diff revision read-only"
            }
        }
    }
}
