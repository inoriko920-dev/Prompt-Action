import QtQuick
import "../theme" as PATheme

Item {
    id: header
    property string title: "Section"
    property string subtitle: ""
    implicitWidth: 480
    implicitHeight: subtitle.length > 0 ? 52 : 28

    Text {
        id: titleText
        anchors.left: parent.left
        anchors.top: parent.top
        text: header.title
        color: PATheme.Theme.textPrimary
        font.family: PATheme.Typography.fontFamily
        font.pixelSize: PATheme.Typography.sectionTitle
        font.weight: Font.DemiBold
    }
    Text {
        visible: header.subtitle.length > 0
        anchors.left: parent.left
        anchors.top: titleText.bottom
        anchors.topMargin: 5
        text: header.subtitle
        color: PATheme.Theme.textSecondary
        font.family: PATheme.Typography.fontFamily
        font.pixelSize: PATheme.Typography.body
    }
}
