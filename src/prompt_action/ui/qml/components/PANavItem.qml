import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme" as PATheme

Button {
    id: control
    property string route: ""
    property url iconSource
    property bool selected: false
    property string accessibleName: text

    implicitHeight: PATheme.Metrics.navHeight
    implicitWidth: 196
    leftPadding: 14
    rightPadding: 12
    focusPolicy: Qt.StrongFocus
    activeFocusOnTab: true
    hoverEnabled: true

    Accessible.role: Accessible.Button
    Accessible.name: accessibleName
    Accessible.description: selected ? "Halaman aktif" : ""
    Keys.onReturnPressed: function(event) { control.clicked(); event.accepted = true }
    Keys.onSpacePressed: function(event) { control.clicked(); event.accepted = true }

    background: Rectangle {
        radius: PATheme.Metrics.radius8
        color: control.selected ? PATheme.Theme.primary : control.pressed ? "#115AA8" : control.hovered ? "#0C4D91" : "transparent"
        border.width: control.activeFocus ? 2 : 0
        border.color: PATheme.Theme.focusRing
        Rectangle {
            visible: control.selected
            width: 3
            height: 24
            radius: 2
            color: "#FFFFFF"
            anchors.left: parent.left
            anchors.leftMargin: 5
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    contentItem: RowLayout {
        spacing: 10
        Image {
            source: control.iconSource
            sourceSize.width: 20
            sourceSize.height: 20
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
            fillMode: Image.PreserveAspectFit
        }
        Text {
            text: control.text
            color: PATheme.Theme.sidebarText
            font.family: PATheme.Typography.fontFamily
            font.pixelSize: PATheme.Typography.body
            font.weight: control.selected ? Font.DemiBold : Font.Medium
            elide: Text.ElideRight
            Layout.fillWidth: true
            verticalAlignment: Text.AlignVCenter
        }
    }
}
