import QtQuick
import QtQuick.Controls
import "../theme" as PATheme

TextField {
    id: field
    property bool invalid: false
    property string errorText: ""
    property string accessibleName: placeholderText

    implicitHeight: PATheme.Metrics.controlHeight
    leftPadding: 12
    rightPadding: 12
    color: PATheme.Theme.textPrimary
    placeholderTextColor: PATheme.Theme.textSecondary
    selectionColor: PATheme.Theme.primaryPale
    selectedTextColor: PATheme.Theme.textPrimary
    font.family: PATheme.Typography.fontFamily
    font.pixelSize: PATheme.Typography.body
    focusPolicy: Qt.StrongFocus
    activeFocusOnTab: true

    Accessible.role: Accessible.EditableText
    Accessible.name: accessibleName
    Accessible.description: invalid ? errorText : ""

    background: Rectangle {
        radius: PATheme.Metrics.radius8
        color: field.enabled ? PATheme.Theme.surface : PATheme.Theme.neutralPale
        border.width: field.activeFocus ? 2 : 1
        border.color: field.invalid ? PATheme.Theme.error : field.activeFocus ? PATheme.Theme.focusRing : PATheme.Theme.border
    }
}
