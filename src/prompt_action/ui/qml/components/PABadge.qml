import QtQuick
import "../theme" as PATheme

Rectangle {
    id: badge
    property string text: "Label"
    property string tone: "neutral"
    readonly property color toneColor: tone === "success" ? PATheme.Theme.success : tone === "warning" ? PATheme.Theme.warning : tone === "error" ? PATheme.Theme.error : tone === "draft" ? PATheme.Theme.primary : tone === "legacy" ? "#7957A8" : PATheme.Theme.neutral
    readonly property color toneBackground: tone === "success" ? PATheme.Theme.successPale : tone === "warning" ? PATheme.Theme.warningPale : tone === "error" ? PATheme.Theme.errorPale : tone === "draft" ? PATheme.Theme.primaryPale : tone === "legacy" ? "#F4EEFB" : PATheme.Theme.neutralPale

    implicitHeight: 26
    implicitWidth: label.implicitWidth + 20
    radius: 13
    color: toneBackground
    border.width: 1
    border.color: Qt.rgba(toneColor.r, toneColor.g, toneColor.b, 0.28)

    Text {
        id: label
        anchors.centerIn: parent
        text: badge.text
        color: badge.toneColor
        font.family: PATheme.Typography.fontFamily
        font.pixelSize: PATheme.Typography.caption
        font.weight: Font.DemiBold
    }
}
