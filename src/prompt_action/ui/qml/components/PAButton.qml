import QtQuick
import QtQuick.Controls
import "../theme" as PATheme

Button {
    id: control
    property string variant: "primary"
    property bool loading: false
    property bool interactive: true
    property string accessibleName: text
    readonly property color resolvedBackground: !enabled ? "#DCE5EF" : pressed ? (variant === "primary" ? PATheme.Theme.primaryStrong : PATheme.Theme.primaryPale) : hovered ? (variant === "primary" ? "#2E86FF" : "#F3F8FF") : (variant === "primary" ? PATheme.Theme.primary : PATheme.Theme.surface)
    readonly property color resolvedForeground: !enabled ? PATheme.Theme.textSecondary : (variant === "primary" ? "#FFFFFF" : PATheme.Theme.primaryStrong)

    implicitHeight: PATheme.Metrics.controlHeight
    implicitWidth: Math.max(112, contentItem.implicitWidth + 32)
    leftPadding: 16
    rightPadding: 16
    focusPolicy: Qt.StrongFocus
    activeFocusOnTab: true
    hoverEnabled: true
    enabled: interactive && !loading

    Accessible.role: Accessible.Button
    Accessible.name: accessibleName
    Accessible.description: loading ? "Sedang memproses" : ""
    Keys.onReturnPressed: function(event) { control.clicked(); event.accepted = true }
    Keys.onSpacePressed: function(event) { control.clicked(); event.accepted = true }

    background: Rectangle {
        radius: PATheme.Metrics.radius8
        color: control.resolvedBackground
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? PATheme.Theme.focusRing : (control.variant === "secondary" ? PATheme.Theme.border : control.resolvedBackground)
    }

    contentItem: Text {
        text: control.loading ? "Memproses…" : control.text
        color: control.resolvedForeground
        font.family: PATheme.Typography.fontFamily
        font.pixelSize: PATheme.Typography.button
        font.weight: Font.DemiBold
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
