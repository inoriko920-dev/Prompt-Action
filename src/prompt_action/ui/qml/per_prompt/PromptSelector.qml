import QtQuick
import QtQuick.Layouts
import "../components" as PA
import "../theme" as PATheme

Item {
    id: root
    objectName: "perPromptSelector"
    property var prompts: []
    property string selectedPromptId: ""
    signal promptSelected(string promptId)
    implicitHeight: Math.max(104, selectorFlow.implicitHeight + 58)

    PA.PACard {
        anchors.fill: parent
        Column {
            anchors.fill: parent
            spacing: PATheme.Metrics.space12
            Text {
                text: "Pilih Prompt"
                color: PATheme.Theme.textPrimary
                font.family: PATheme.Typography.fontFamily
                font.pixelSize: PATheme.Typography.cardTitle
                font.weight: Font.DemiBold
            }
            Flow {
                id: selectorFlow
                width: parent.width
                spacing: PATheme.Metrics.space8
                Repeater {
                    model: root.prompts || []
                    delegate: PA.PAButton {
                        required property var modelData
                        text: modelData.display_name + (modelData.active_revision ? "  " + modelData.active_revision : "")
                        variant: modelData.id === root.selectedPromptId ? "primary" : "secondary"
                        accessibleName: "Pilih " + modelData.display_name
                        onClicked: root.promptSelected(modelData.id)
                    }
                }
            }
        }
    }
}
