import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme" as PATheme

RowLayout {
    id: row
    property string label: ""
    property string detail: ""
    property bool checked: false
    property bool locked: false
    property string accessibleName: label
    signal changed(bool value)
    Layout.fillWidth: true
    spacing: 12

    Switch {
        id: toggle
        checked: row.checked
        enabled: !row.locked
        focusPolicy: Qt.StrongFocus
        activeFocusOnTab: true
        Accessible.name: row.accessibleName
        onToggled: if (!row.locked) row.changed(checked)
    }
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 2
        Text {
            text: row.label + (row.locked ? "  •  Wajib" : "")
            color: PATheme.Theme.textPrimary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.body
            font.weight: Font.DemiBold
            Layout.fillWidth: true
        }
        Text {
            text: row.detail
            color: PATheme.Theme.textSecondary
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.meta
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }
}
