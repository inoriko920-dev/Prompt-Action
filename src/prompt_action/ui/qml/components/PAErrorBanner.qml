import QtQuick
import "../theme" as PATheme

Rectangle {
    id: banner
    property string text: "Terjadi masalah."
    implicitHeight: 44
    radius: PATheme.Metrics.radius8
    color: PATheme.Theme.errorPale
    border.width: 1
    border.color: PATheme.Theme.error

    Text {
        anchors.fill: parent
        anchors.leftMargin: 14
        anchors.rightMargin: 14
        text: banner.text
        color: PATheme.Theme.error
        font.family: PATheme.Typography.fontFamily
        font.pixelSize: PATheme.Typography.body
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
