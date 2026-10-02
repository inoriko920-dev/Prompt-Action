import QtQuick
import QtQuick.Window

Window {
    id: root
    width: 1280
    height: 720
    minimumWidth: 640
    minimumHeight: 420
    visible: true
    title: "Prompt Action"
    color: "white"

    Text {
        anchors.centerIn: parent
        text: "Prompt Action — Foundation Build"
        font.pixelSize: 24
        color: "#1f2937"
    }
}
