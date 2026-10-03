import QtQuick
import QtQuick.Layouts
import "../theme" as PATheme

Rectangle {
    id: pill
    property string text: "Status"
    property string tone: "neutral"
    readonly property color toneColor: tone === "success" ? PATheme.Theme.success : tone === "warning" ? PATheme.Theme.warning : tone === "error" ? PATheme.Theme.error : tone === "draft" ? PATheme.Theme.primary : tone === "legacy" ? "#7957A8" : PATheme.Theme.neutral
    readonly property color toneBackground: tone === "success" ? PATheme.Theme.successPale : tone === "warning" ? PATheme.Theme.warningPale : tone === "error" ? PATheme.Theme.errorPale : tone === "draft" ? PATheme.Theme.primaryPale : tone === "legacy" ? "#F4EEFB" : PATheme.Theme.neutralPale

    implicitHeight: 32
    implicitWidth: row.implicitWidth + 20
    radius: 16
    color: toneBackground
    border.width: 1
    border.color: Qt.rgba(toneColor.r, toneColor.g, toneColor.b, 0.28)

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 7
        Rectangle {
            width: 8
            height: 8
            radius: 4
            color: pill.toneColor
        }
        Text {
            text: pill.text
            color: PATheme.Theme.textPrimary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.caption
            font.weight: Font.DemiBold
        }
    }
}
