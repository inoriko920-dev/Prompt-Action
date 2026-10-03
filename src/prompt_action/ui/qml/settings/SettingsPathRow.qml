import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as PA
import "../theme" as PATheme

ColumnLayout {
    id: row
    property string label: ""
    property string pathText: ""
    property string errorText: ""
    property string warningText: ""
    property string statusText: ""
    property string accessibleName: label
    signal pathEdited(string value)
    signal browseRequested()
    spacing: 5
    Layout.fillWidth: true

    Text {
        text: row.label
        color: PATheme.Theme.textPrimary
        font.family: PATheme.Typography.fontFamily
        font.pixelSize: PATheme.Typography.caption
        font.weight: Font.DemiBold
        Layout.fillWidth: true
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        PA.PAInput {
            id: input
            objectName: "settings_path_" + row.label.replace(/\s+/g, "_").toLowerCase()
            Layout.fillWidth: true
            text: row.pathText
            invalid: row.errorText.length > 0
            errorText: row.errorText
            accessibleName: row.accessibleName
            onEditingFinished: row.pathEdited(text)
        }
        PA.PAButton {
            text: "Pilih Folder"
            variant: "secondary"
            accessibleName: "Pilih folder untuk " + row.label
            onClicked: row.browseRequested()
        }
        Text {
            text: row.errorText.length > 0 ? "✕" : row.warningText.length > 0 ? "!" : "●"
            color: row.errorText.length > 0 ? PATheme.Theme.error : row.warningText.length > 0 ? PATheme.Theme.warning : PATheme.Theme.success
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: 13
        }
    }
    Text {
        visible: row.errorText.length > 0 || row.warningText.length > 0 || row.statusText.length > 0
        text: row.errorText.length > 0 ? row.errorText : row.warningText.length > 0 ? row.warningText : row.statusText
        color: row.errorText.length > 0 ? PATheme.Theme.error : row.warningText.length > 0 ? PATheme.Theme.warning : PATheme.Theme.textSecondary
        font.family: PATheme.Typography.fontFamily
        font.pixelSize: PATheme.Typography.meta
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }
}
