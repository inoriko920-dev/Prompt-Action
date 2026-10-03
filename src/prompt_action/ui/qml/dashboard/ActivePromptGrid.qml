import QtQuick
import QtQuick.Controls
import "../components" as PA
import "../theme" as PATheme

PA.PACard {
    id: root
    property var prompts: []
    property var viewModel: null
    readonly property int columnCount: width >= 920 ? 4 : width >= 620 ? 3 : 2
    implicitHeight: 214

    Text {
        id: title
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        text: "Prompt Aktif"
        color: PATheme.Theme.textPrimary
        font.family: PATheme.Typography.fontFamily
        font.pixelSize: PATheme.Typography.cardTitle
        font.weight: Font.DemiBold
    }

    GridView {
        id: grid
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: title.bottom
        anchors.topMargin: 12
        anchors.bottom: parent.bottom
        clip: true
        interactive: contentHeight > height
        model: root.prompts || []
        cellWidth: width / root.columnCount
        cellHeight: 74

        delegate: Button {
            id: promptButton
            required property var modelData
            width: grid.cellWidth - 10
            height: 64
            focusPolicy: Qt.StrongFocus
            activeFocusOnTab: true
            hoverEnabled: true
            Accessible.name: "Buka " + modelData.display_name + " " + modelData.active_revision_label
            onClicked: if (root.viewModel) root.viewModel.openPrompt(modelData.prompt_id)

            background: Rectangle {
                radius: PATheme.Metrics.radius8
                color: promptButton.hovered ? PATheme.Theme.primaryPale : PATheme.Theme.pageBackground
                border.width: promptButton.activeFocus ? 2 : 1
                border.color: promptButton.activeFocus ? PATheme.Theme.focusRing : PATheme.Theme.border
            }

            contentItem: Column {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 4
                Text {
                    width: parent.width
                    text: promptButton.modelData.display_name || promptButton.modelData.prompt_id
                    color: PATheme.Theme.textPrimary
                    font.family: PATheme.Typography.fontFamily
                    font.pixelSize: PATheme.Typography.body
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Row {
                    spacing: 8
                    Text {
                        text: promptButton.modelData.active_revision_label || "—"
                        color: PATheme.Theme.primaryStrong
                        font.family: PATheme.Typography.fontFamily
                        font.pixelSize: PATheme.Typography.caption
                        font.weight: Font.DemiBold
                    }
                    Text {
                        text: promptButton.modelData.integrity_state === "VERIFIED_FILE" || promptButton.modelData.integrity_state === "VERIFIED_BASELINE" ? "Terverifikasi" : "Periksa integritas"
                        color: promptButton.modelData.integrity_state === "VERIFIED_FILE" || promptButton.modelData.integrity_state === "VERIFIED_BASELINE" ? PATheme.Theme.success : PATheme.Theme.warning
                        font.family: PATheme.Typography.fontFamily
                        font.pixelSize: PATheme.Typography.caption
                    }
                }
            }
        }
    }
}
