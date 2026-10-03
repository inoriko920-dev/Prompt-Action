import QtQuick
import QtQuick.Controls
import "../components" as PA
import "../dashboard" as Dashboard
import "../theme" as PATheme

Item {
    id: root
    objectName: "dashboardPage"
    property var viewModel: (typeof dashboardViewModel !== "undefined") ? dashboardViewModel : null
    property var stateOverride: null
    readonly property var state: stateOverride !== null ? stateOverride : (viewModel ? viewModel.state : ({
        "load_state": "loading",
        "system_label": "—",
        "snapshot_label": "—",
        "active_prompt_count": 0,
        "backup_health": "UNKNOWN",
        "latest_change": {},
        "active_prompts": [],
        "backup_checklist": [],
        "recovery_health": "UNKNOWN",
        "action_capabilities": {},
        "diagnostics": []
    }))

    // Compatibility marker for STEP 03 shell regression tests; this is not rendered UI.
    Item { objectName: "placeholder_dashboard"; visible: false; width: 0; height: 0 }

    Flickable {
        id: flick
        anchors.fill: parent
        contentWidth: width
        contentHeight: contentColumn.implicitHeight + 8
        clip: true
        interactive: contentHeight > height
        boundsBehavior: Flickable.StopAtBounds

        Column {
            id: contentColumn
            width: flick.width
            spacing: PATheme.Metrics.space16

            Column {
                width: parent.width
                spacing: 8
                visible: root.state.load_state === "loading"
                PA.PASkeleton { width: parent.width; height: 104 }
                PA.PASkeleton { width: parent.width; height: 206 }
                PA.PASkeleton { width: parent.width; height: 214 }
            }

            Column {
                width: parent.width
                spacing: 10
                visible: root.state.load_state === "invalid" || root.state.load_state === "error"
                PA.PAErrorBanner {
                    width: parent.width
                    text: root.state.load_state === "invalid" ? "Data canonical tidak valid. Dashboard healthy diblokir." : "Dashboard gagal memuat data canonical."
                }
                Text {
                    width: parent.width
                    text: root.state.diagnostics && root.state.diagnostics.length ? root.state.diagnostics.join(" • ") : "Tidak ada diagnostik tambahan."
                    color: PATheme.Theme.textSecondary
                    font.family: PATheme.Typography.fontFamily
                    font.pixelSize: PATheme.Typography.body
                    wrapMode: Text.WordWrap
                }
                PA.PAButton {
                    text: "Coba Lagi"
                    variant: "secondary"
                    interactive: Boolean(root.viewModel)
                    onClicked: root.viewModel.refresh()
                }
            }

            PA.PAEmptyState {
                width: parent.width
                visible: root.state.load_state === "empty"
                title: "Belum ada sistem aktif"
                message: "Dashboard tidak mengarang baseline. Lengkapi canonical data yang valid lalu muat ulang."
            }

            Rectangle {
                width: parent.width
                height: visible ? 44 : 0
                visible: root.state.load_state === "degraded"
                radius: PATheme.Metrics.radius8
                color: PATheme.Theme.warningPale
                border.width: 1
                border.color: PATheme.Theme.warning
                Text {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14
                    text: "Sebagian sumber aktif perlu pemeriksaan integritas. Aksi tertentu dinonaktifkan."
                    color: PATheme.Theme.warning
                    font.family: PATheme.Typography.fontFamily
                    font.pixelSize: PATheme.Typography.body
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
            }

            Rectangle {
                width: parent.width
                height: visible ? 44 : 0
                visible: (root.state.load_state === "ready" || root.state.load_state === "degraded") && root.state.backup_health === "PERLU BACKUP"
                radius: PATheme.Metrics.radius8
                color: PATheme.Theme.warningPale
                border.width: 1
                border.color: PATheme.Theme.warning
                Text {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14
                    text: "Snapshot aktif memerlukan backup. Dashboard tidak akan menampilkan status AMAN sampai evidence recovery tervalidasi."
                    color: PATheme.Theme.warning
                    font.family: PATheme.Typography.fontFamily
                    font.pixelSize: PATheme.Typography.body
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
            }

            Dashboard.DashboardKpiRow {
                width: parent.width
                visible: root.state.load_state === "ready" || root.state.load_state === "degraded"
                state: root.state
            }

            Row {
                width: parent.width
                spacing: PATheme.Metrics.space16
                visible: root.state.load_state === "ready" || root.state.load_state === "degraded"
                Dashboard.RecentChangeCard {
                    width: parent.width * 0.59
                    latestChange: root.state.latest_change || ({})
                    viewModel: root.viewModel
                }
                Dashboard.BackupStatusCard {
                    width: parent.width - parent.spacing - parent.width * 0.59
                    backupHealth: root.state.backup_health || "UNKNOWN"
                    recoveryHealth: root.state.recovery_health || "UNKNOWN"
                    checklist: root.state.backup_checklist || []
                    capabilities: root.state.action_capabilities || ({})
                    viewModel: root.viewModel
                }
            }

            Dashboard.ActivePromptGrid {
                width: parent.width
                visible: root.state.load_state === "ready" || root.state.load_state === "degraded"
                prompts: root.state.active_prompts || []
                viewModel: root.viewModel
            }

            Dashboard.QuickActions {
                width: parent.width
                visible: root.state.load_state === "ready" || root.state.load_state === "degraded"
                state: root.state
                viewModel: root.viewModel
            }
        }
    }
}
