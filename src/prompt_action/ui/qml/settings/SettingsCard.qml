import QtQuick
import QtQuick.Layouts
import "../theme" as PATheme

Rectangle {
    id: card
    property string title: ""
    property string subtitle: ""
    default property alias contentData: body.data
    color: PATheme.Theme.surface
    radius: PATheme.Metrics.radius12
    border.width: 1
    border.color: PATheme.Theme.border
    implicitHeight: body.implicitHeight + 32

    ColumnLayout {
        id: body
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12
        Text {
            text: card.title
            color: PATheme.Theme.textPrimary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.cardTitle
            font.weight: Font.DemiBold
            Layout.fillWidth: true
        }
        Text {
            visible: card.subtitle.length > 0
            text: card.subtitle
            color: PATheme.Theme.textSecondary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.caption
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }
}
