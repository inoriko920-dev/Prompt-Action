import QtQuick
import "../theme" as PATheme

Rectangle {
    id: root
    property string title: "Belum ada konten"
    property string message: "Konten akan tersedia pada tahap implementasi berikutnya."
    color: PATheme.Theme.surface
    border.width: 1
    border.color: PATheme.Theme.border
    radius: PATheme.Metrics.radius12
    implicitWidth: 420
    implicitHeight: 190

    Column {
        anchors.centerIn: parent
        width: Math.min(parent.width - 48, 360)
        spacing: 10
        Image {
            width: 32
            height: 32
            anchors.horizontalCenter: parent.horizontalCenter
            source: "../../assets/icons/info.svg"
            fillMode: Image.PreserveAspectFit
        }
        Text {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: root.title
            color: PATheme.Theme.textPrimary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.cardTitle
            font.weight: Font.DemiBold
        }
        Text {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            text: root.message
            color: PATheme.Theme.textSecondary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.body
        }
    }
}
