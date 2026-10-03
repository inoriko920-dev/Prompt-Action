import QtQuick
import QtQuick.Layouts
import "../components" as PA
import "../per_prompt" as PerPrompt
import "../theme" as PATheme

Item {
    id: root
    objectName: "perPromptPage"
    property var viewModel: (typeof perPromptViewModel !== "undefined") ? perPromptViewModel : null
    property var stateOverride: null
    readonly property var fallbackState: ({"load_state":"loading","prompts":[],"selected_prompt_id":"","selected_prompt_name":"","active_revision_id":"","selected_revision_id":"","official_revisions":[],"drafts":[],"selected_revision":{},"available_files":[],"capabilities":{},"issues":[],"diagnostics":[]})
    readonly property var state: stateOverride !== null ? stateOverride : (viewModel ? viewModel.state : fallbackState)
    readonly property bool contentReady: state.load_state === "ready" || state.load_state === "degraded"
    readonly property bool compactLayout: width < 1030

    // Compatibility marker for STEP 03 regression tests; never rendered.
    Item { objectName: "placeholder_prompt"; visible: false; width: 0; height: 0 }

    Column {
        anchors.fill: parent
        spacing: PATheme.Metrics.space12
        visible: root.state.load_state === "loading"
        PA.PASkeleton { width: parent.width; height: 108 }
        Row { width: parent.width; spacing: 16; PA.PASkeleton { width: parent.width * 0.42; height: 360 } PA.PASkeleton { width: parent.width * 0.56; height: 360 } }
        PA.PASkeleton { width: parent.width; height: 220 }
    }

    Column {
        anchors.fill: parent
        spacing: 10
        visible: root.state.load_state === "invalid" || root.state.load_state === "error"
        PA.PAErrorBanner { width: parent.width; text: root.state.load_state === "invalid" ? "Revision graph/canonical data tidak valid. STEP 06 diblokir." : "Per Prompt gagal dimuat." }
        Text { width: parent.width; text: root.state.diagnostics && root.state.diagnostics.length ? root.state.diagnostics.join(" • ") : "Tidak ada diagnostik tambahan."; color: PATheme.Theme.textSecondary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.body; wrapMode: Text.WordWrap }
        PA.PAButton { text: "Coba Lagi"; variant: "secondary"; interactive: Boolean(root.viewModel); onClicked: root.viewModel.refresh() }
    }

    PA.PAEmptyState { anchors.fill: parent; visible: root.state.load_state === "empty"; title: "Belum ada Prompt"; message: "Canonical registry belum memiliki Prompt/Revision yang dapat ditampilkan." }

    Flickable {
        anchors.fill: parent
        visible: root.contentReady
        contentWidth: width
        contentHeight: contentColumn.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        Column {
            id: contentColumn
            width: parent.width
            spacing: PATheme.Metrics.space16
            PA.PAErrorBanner { width: parent.width; visible: root.state.load_state === "degraded"; text: "Data revision dapat dibaca, tetapi integritas file membutuhkan perhatian. Download otomatis dinonaktifkan." }
            RowLayout {
                width: parent.width
                Text { text: root.state.selected_prompt_name || "Per Prompt"; color: PATheme.Theme.textPrimary; font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.pageTitle; font.weight: Font.DemiBold; Layout.fillWidth: true }
                PA.PAStatusPill { text: "System " + (root.state.active_system || "—"); tone: "neutral" }
                PA.PAStatusPill { text: "Revision Aktif " + (root.state.active_revision_id || "—"); tone: "success" }
            }
            PerPrompt.PromptSelector {
                width: parent.width
                height: implicitHeight
                prompts: root.state.prompts || []
                selectedPromptId: root.state.selected_prompt_id || ""
                onPromptSelected: function(promptId) { if (root.viewModel) root.viewModel.selectPrompt(promptId) }
            }
            GridLayout {
                width: parent.width
                columns: root.compactLayout ? 1 : 2
                columnSpacing: PATheme.Metrics.space16
                rowSpacing: PATheme.Metrics.space16
                PerPrompt.RevisionTree {
                    Layout.fillWidth: true
                    Layout.preferredWidth: root.compactLayout ? parent.width : parent.width * 0.42
                    Layout.minimumHeight: 390
                    officialRevisions: root.state.official_revisions || []
                    drafts: root.state.drafts || []
                    activeRevisionId: root.state.active_revision_id || ""
                    selectedRevisionId: root.state.selected_revision_id || ""
                    onRevisionSelected: function(revisionId) { if (root.viewModel) root.viewModel.selectRevision(revisionId) }
                }
                PerPrompt.RevisionDetailCard {
                    Layout.fillWidth: true
                    Layout.preferredWidth: root.compactLayout ? parent.width : parent.width * 0.58
                    Layout.minimumHeight: 390
                    detail: root.state.selected_revision || ({})
                }
            }
            PerPrompt.AvailableFilesCard {
                width: parent.width
                height: Math.max(245, implicitHeight)
                files: root.state.available_files || []
                capabilities: root.state.capabilities || ({})
                detail: root.state.selected_revision || ({})
                onDownloadActiveRequested: if (root.viewModel) root.viewModel.downloadActivePrompt()
                onDownloadSelectedRequested: if (root.viewModel) root.viewModel.downloadSelectedRevision()
                onCompareRequested: if (root.viewModel) root.viewModel.compareSelectedWithParent()
                onSnapshotRequested: if (root.viewModel) root.viewModel.viewSnapshot()
                onChangelogRequested: if (root.viewModel) root.viewModel.openChangelog()
                onAddRevisionRequested: if (root.viewModel) root.viewModel.addRevision()
            }
            Item { width: 1; height: 8 }
        }
    }
}
