import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as PA
import "../theme" as PATheme

Dialog {
    id: root
    objectName: "releaseProgressDialog"
    property var viewModel: null
    readonly property var stateData: viewModel ? viewModel.state : ({})
    modal: true
    focus: true
    width: 520
    height: 260
    closePolicy: Popup.NoAutoClose
    title: "Memproses Release"

    background: Rectangle {
        color: PATheme.Theme.surface
        radius: PATheme.Metrics.radius16
        border.width: 1
        border.color: PATheme.Theme.border
    }

    contentItem: ColumnLayout {
        spacing: PATheme.Metrics.space16
        Item { Layout.fillHeight: true }
        BusyIndicator { Layout.alignment: Qt.AlignHCenter; running: root.stateData.stage === "committing" }
        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: "Menempatkan file Revision secara immutable dan melakukan commit canonical atomik…"
            color: PATheme.Theme.textPrimary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.body
            wrapMode: Text.WordWrap
        }
        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: "Jangan tutup aplikasi. Jika proses terputus, journal STEP 10 akan memaksa recovery saat startup berikutnya."
            color: PATheme.Theme.textSecondary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.caption
            wrapMode: Text.WordWrap
        }
        Item { Layout.fillHeight: true }
    }
}
