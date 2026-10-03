import QtQuick
import QtQuick.Controls
import "../theme" as PATheme

ToolTip {
    delay: 350
    timeout: 3000
    padding: 8
    contentItem: Text {
        text: parent.text
        color: "#FFFFFF"
        font.family: PATheme.Typography.fontFamily
        font.pixelSize: PATheme.Typography.caption
    }
    background: Rectangle {
        color: PATheme.Theme.textPrimary
        radius: PATheme.Metrics.radius8
    }
}
