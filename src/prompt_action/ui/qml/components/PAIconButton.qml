import QtQuick
import QtQuick.Controls
import "../theme" as PATheme

Button {
    id: control
    property url iconSource
    property string tooltipText: ""
    property string accessibleName: tooltipText
    implicitWidth: PATheme.Metrics.iconButtonSize
    implicitHeight: PATheme.Metrics.iconButtonSize
    focusPolicy: Qt.StrongFocus
    activeFocusOnTab: true
    hoverEnabled: true

    Accessible.role: Accessible.Button
    Accessible.name: accessibleName
    ToolTip.visible: hovered && tooltipText.length > 0
    ToolTip.text: tooltipText
    ToolTip.delay: 350

    background: Rectangle {
        radius: PATheme.Metrics.radius8
        color: control.pressed ? PATheme.Theme.primaryPale : control.hovered ? "#F3F8FF" : PATheme.Theme.surface
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? PATheme.Theme.focusRing : PATheme.Theme.border
    }
    contentItem: Image {
        source: control.iconSource
        sourceSize.width: 18
        sourceSize.height: 18
        fillMode: Image.PreserveAspectFit
    }
}
