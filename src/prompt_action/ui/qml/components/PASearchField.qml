import QtQuick
import QtQuick.Controls
import "../theme" as PATheme

TextField {
    id: search
    property string accessibleName: "Cari"
    implicitHeight: PATheme.Metrics.controlHeight
    implicitWidth: 300
    leftPadding: 40
    rightPadding: 12
    placeholderText: "Cari prompt atau versi"
    color: PATheme.Theme.textPrimary
    placeholderTextColor: PATheme.Theme.textSecondary
    font.family: PATheme.Typography.fontFamily
    font.pixelSize: PATheme.Typography.body
    focusPolicy: Qt.StrongFocus
    activeFocusOnTab: true
    Accessible.role: Accessible.EditableText
    Accessible.name: accessibleName

    background: Rectangle {
        radius: PATheme.Metrics.radius8
        color: PATheme.Theme.surface
        border.width: search.activeFocus ? 2 : 1
        border.color: search.activeFocus ? PATheme.Theme.focusRing : PATheme.Theme.border
    }

    Image {
        width: 18
        height: 18
        anchors.left: parent.left
        anchors.leftMargin: 12
        anchors.verticalCenter: parent.verticalCenter
        source: "../../assets/icons/search.svg"
        fillMode: Image.PreserveAspectFit
        sourceSize.width: 18
        sourceSize.height: 18
    }
}
