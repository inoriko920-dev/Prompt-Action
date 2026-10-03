import QtQuick
import "../theme" as PATheme

Rectangle {
    id: card
    property bool selected: false
    property string tone: "default"
    default property alias contentData: content.data
    readonly property color resolvedBorder: selected ? PATheme.Theme.selectedBorder : tone === "warning" ? PATheme.Theme.warning : tone === "error" ? PATheme.Theme.error : PATheme.Theme.border
    readonly property color resolvedBackground: tone === "warning" ? PATheme.Theme.warningPale : tone === "error" ? PATheme.Theme.errorPale : PATheme.Theme.surface

    color: resolvedBackground
    radius: PATheme.Metrics.radius12
    border.width: selected ? 2 : PATheme.Metrics.borderWidth
    border.color: resolvedBorder
    implicitWidth: 240
    implicitHeight: 120

    Item {
        id: content
        anchors.fill: parent
        anchors.margins: PATheme.Metrics.space16
    }
}
