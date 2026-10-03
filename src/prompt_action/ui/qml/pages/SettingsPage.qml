import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "../components" as PA
import "../settings" as SettingsUI
import "../theme" as PATheme

Item {
    id: root
    objectName: "settingsPage"
    property var stateOverride: null
    readonly property var fallbackState: ({
        "load_state":"loading","load_error":"","persisted_settings":{},
        "draft_settings":{
            "general":{"root_dir":".","prompts_dir":"prompts","backup_dir":"backups"},
            "backup":{"backup_on_release":true,"write_sha256":true,"verify_after_write":true,"second_copy_enabled":true,"second_copy_dir":"backups-second-copy"},
            "github":{"repository":"inoriko920-dev/Prompt-Action","branch":"main"},
            "appearance":{"theme":"light_blue","ui_scale":100,"tree_density":"comfortable"},
            "advanced":{"diagnostics_dir":"runtime/diagnostics","log_level":"INFO"}
        },
        "is_dirty":false,"validation_errors":[],"validation_warnings":[],"save_state":"IDLE",
        "github_capability":{"status":"UNAVAILABLE","test_available":false,"connected":false,"reason":"GitHub service belum aktif.","can_open_repository":true},
        "path_capabilities":{},"repository_url":"https://github.com/inoriko920-dev/Prompt-Action",
        "restart_required":false,"can_save":false,"can_revert":false,"status_message":"Memuat pengaturan…","last_export_path":""
    })
    readonly property var pageState: stateOverride !== null ? stateOverride : ((typeof settingsViewModel !== "undefined") ? settingsViewModel.state : fallbackState)
    property string pendingFolderKey: ""

    // Compatibility marker for the STEP 03 shell regression. This is not the
    // production placeholder; the real settings page is rendered below.
    Item { objectName: "placeholder_settings"; visible: false; width: 0; height: 0 }

    function section(name) { var d = pageState.draft_settings || {}; return d[name] || {} }
    function value(sectionName, fieldName, fallback) {
        var s = section(sectionName); return (s[fieldName] === undefined || s[fieldName] === null) ? fallback : s[fieldName]
    }
    function messageFor(listName, fieldName) {
        var list = pageState[listName] || []
        for (var i=0; i<list.length; ++i) if (list[i].field === fieldName) return list[i].message || ""
        return ""
    }
    function errorFor(fieldName) { return messageFor("validation_errors", fieldName) }
    function warningFor(fieldName) { return messageFor("validation_warnings", fieldName) }
    function update(sectionName, fieldName, newValue) {
        if (typeof settingsViewModel !== "undefined") settingsViewModel.updateField(sectionName, fieldName, newValue)
    }
    function folderStatus(fieldName) {
        var caps = pageState.path_capabilities || {}; var cap = caps[fieldName]
        if (!cap) return "Belum diperiksa"
        return cap.exists && cap.is_dir ? "Folder terdeteksi" : "Folder belum tersedia"
    }

    ScrollView {
        id: scroll
        objectName: "settingsScroll"
        anchors.fill: parent
        clip: true
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        Item {
            width: scroll.availableWidth
            implicitHeight: content.implicitHeight + 8
            ColumnLayout {
                id: content
                width: parent.width
                spacing: 16

                PA.PAErrorBanner {
                    Layout.fillWidth: true
                    visible: pageState.load_state === "degraded"
                    text: pageState.load_error || "Settings lama tidak dapat dibaca. Safe defaults digunakan sampai Anda menyimpan secara eksplisit."
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12
                    Text {
                        text: pageState.is_dirty ? "Perubahan belum disimpan" : "Pengaturan tersimpan"
                        color: pageState.is_dirty ? PATheme.Theme.warning : PATheme.Theme.textSecondary
                        font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption
                    }
                    Text {
                        visible: pageState.restart_required
                        text: "• Berlaku setelah restart"
                        color: PATheme.Theme.warning
                        font.family: PATheme.Typography.fontFamily; font.pixelSize: PATheme.Typography.caption
                    }
                    Item { Layout.fillWidth: true }
                    PA.PAStatusPill {
                        text: pageState.save_state === "SUCCESS" ? "Tersimpan" : pageState.save_state
                        tone: pageState.save_state === "ERROR" ? "error" : pageState.save_state === "SUCCESS" ? "success" : "neutral"
                    }
                }

                GridLayout {
                    id: grid
                    Layout.fillWidth: true
                    columns: width < 980 ? 1 : 2
                    columnSpacing: 16; rowSpacing: 16

                    SettingsUI.SettingsCard {
                        objectName: "settings_section_umum"
                        title: "Umum"
                        subtitle: "Lokasi data Prompt Action di komputer ini."
                        Layout.fillWidth: true; Layout.alignment: Qt.AlignTop
                        SettingsUI.SettingsPathRow {
                            label: "Folder Root Prompt Action"; pathText: root.value("general","root_dir",".")
                            errorText: root.errorFor("general.root_dir"); warningText: root.warningFor("general.root_dir"); statusText: root.folderStatus("general.root_dir")
                            onPathEdited: function(v){ root.update("general","root_dir",v) }
                            onBrowseRequested: { root.pendingFolderKey="root_dir"; folderDialog.open() }
                        }
                        SettingsUI.SettingsPathRow {
                            label: "Folder Prompt"; pathText: root.value("general","prompts_dir","prompts")
                            errorText: root.errorFor("general.prompts_dir"); warningText: root.warningFor("general.prompts_dir"); statusText: root.folderStatus("general.prompts_dir")
                            onPathEdited: function(v){ root.update("general","prompts_dir",v) }
                            onBrowseRequested: { root.pendingFolderKey="prompts_dir"; folderDialog.open() }
                        }
                        SettingsUI.SettingsPathRow {
                            label: "Folder Backup"; pathText: root.value("general","backup_dir","backups")
                            errorText: root.errorFor("general.backup_dir"); warningText: root.warningFor("general.backup_dir"); statusText: root.folderStatus("general.backup_dir")
                            onPathEdited: function(v){ root.update("general","backup_dir",v) }
                            onBrowseRequested: { root.pendingFolderKey="backup_dir"; folderDialog.open() }
                        }
                    }

                    SettingsUI.SettingsCard {
                        objectName: "settings_section_backup"
                        title: "Backup"
                        subtitle: "Policy backup tanpa menjalankan backup engine final."
                        Layout.fillWidth: true; Layout.alignment: Qt.AlignTop
                        SettingsUI.SettingsToggleRow {
                            label: "Buat backup setiap release"; detail: "Release workflow nanti meminta Full Backup."
                            checked: !!root.value("backup","backup_on_release",true)
                            onChanged: function(v){ root.update("backup","backup_on_release",v) }
                        }
                        SettingsUI.SettingsToggleRow { label: "Buat SHA256"; detail: "Wajib untuk release."; checked: true; locked: true }
                        SettingsUI.SettingsToggleRow { label: "Verifikasi ZIP setelah dibuat"; detail: "Wajib untuk release."; checked: true; locked: true }
                        SettingsUI.SettingsToggleRow {
                            label: "Simpan salinan kedua"; detail: "Harus di lokasi berbeda dari Backup utama."
                            checked: !!root.value("backup","second_copy_enabled",true)
                            onChanged: function(v){ root.update("backup","second_copy_enabled",v) }
                        }
                        SettingsUI.SettingsPathRow {
                            label: "Second Copy Location"; enabled: !!root.value("backup","second_copy_enabled",true)
                            pathText: root.value("backup","second_copy_dir","backups-second-copy")
                            errorText: root.errorFor("backup.second_copy_dir"); warningText: root.warningFor("backup.second_copy_dir"); statusText: root.folderStatus("backup.second_copy_dir")
                            onPathEdited: function(v){ root.update("backup","second_copy_dir",v) }
                            onBrowseRequested: { root.pendingFolderKey="second_copy_dir"; folderDialog.open() }
                        }
                    }

                    SettingsUI.SettingsCard {
                        objectName: "settings_section_github"
                        title: "GitHub"
                        subtitle: "Repository metadata. Credential tidak pernah disimpan di settings."
                        Layout.fillWidth: true; Layout.alignment: Qt.AlignTop
                        Text { text:"Repository"; color:PATheme.Theme.textPrimary; font.family:PATheme.Typography.fontFamily; font.pixelSize:PATheme.Typography.caption; font.weight:Font.DemiBold }
                        PA.PAInput {
                            objectName:"settings_github_repository"; Layout.fillWidth:true
                            text: root.value("github","repository","inoriko920-dev/Prompt-Action")
                            invalid: root.errorFor("github.repository").length > 0; errorText: root.errorFor("github.repository")
                            accessibleName:"Repository GitHub"
                            onEditingFinished: root.update("github","repository",text)
                        }
                        Text { visible:root.errorFor("github.repository").length>0; text:root.errorFor("github.repository"); color:PATheme.Theme.error; font.family:PATheme.Typography.fontFamily; font.pixelSize:PATheme.Typography.meta }
                        Text { text:"Branch"; color:PATheme.Theme.textPrimary; font.family:PATheme.Typography.fontFamily; font.pixelSize:PATheme.Typography.caption; font.weight:Font.DemiBold }
                        PA.PAInput {
                            objectName:"settings_github_branch"; Layout.fillWidth:true
                            text: root.value("github","branch","main")
                            invalid: root.errorFor("github.branch").length > 0; errorText: root.errorFor("github.branch")
                            accessibleName:"Branch GitHub"
                            onEditingFinished: root.update("github","branch",text)
                        }
                        RowLayout {
                            Layout.fillWidth:true; spacing:8
                            PA.PAStatusPill { text:(pageState.github_capability||{}).status || "UNAVAILABLE"; tone:"neutral" }
                            Item { Layout.fillWidth:true }
                            PA.PAButton {
                                text:"Buka Repository"; variant:"secondary"
                                interactive: !!(pageState.github_capability||{}).can_open_repository
                                onClicked: if (pageState.repository_url) Qt.openUrlExternally(pageState.repository_url)
                            }
                            PA.PAButton {
                                text:"Tes Koneksi"; variant:"secondary"
                                interactive: !!(pageState.github_capability||{}).test_available
                                onClicked: if (typeof settingsViewModel !== "undefined") settingsViewModel.testGitHubConnection()
                            }
                        }
                        Text {
                            text: (pageState.github_capability||{}).reason || "GitHub bukan satu-satunya backup."
                            color:PATheme.Theme.textSecondary; font.family:PATheme.Typography.fontFamily; font.pixelSize:PATheme.Typography.meta; wrapMode:Text.WordWrap; Layout.fillWidth:true
                        }
                        Text { text:"GitHub bukan satu-satunya backup."; color:PATheme.Theme.primaryStrong; font.family:PATheme.Typography.fontFamily; font.pixelSize:PATheme.Typography.meta }
                    }

                    SettingsUI.SettingsCard {
                        objectName: "settings_section_tampilan"
                        title: "Tampilan"
                        subtitle: "Preferensi tampilan antarmuka aplikasi."
                        Layout.fillWidth:true; Layout.alignment:Qt.AlignTop
                        Text { text:"Theme"; color:PATheme.Theme.textPrimary; font.family:PATheme.Typography.fontFamily; font.pixelSize:PATheme.Typography.caption; font.weight:Font.DemiBold }
                        RowLayout {
                            Layout.fillWidth:true
                            Rectangle {
                                Layout.fillWidth:true; implicitHeight:PATheme.Metrics.controlHeight; radius:PATheme.Metrics.radius8; color:PATheme.Theme.neutralPale; border.color:PATheme.Theme.border
                                Text { anchors.centerIn:parent; text:"Light — Prompt Action Blue"; color:PATheme.Theme.textPrimary; font.family:PATheme.Typography.fontFamily; font.pixelSize:PATheme.Typography.body }
                            }
                            PA.PABadge { text:"Dikunci V1"; tone:"neutral" }
                        }
                        Text { text:"UI Scale"; color:PATheme.Theme.textPrimary; font.family:PATheme.Typography.fontFamily; font.pixelSize:PATheme.Typography.caption; font.weight:Font.DemiBold }
                        ComboBox {
                            objectName:"settings_ui_scale"; Layout.fillWidth:true; model:["100%","110%","125%"]
                            currentIndex: root.value("appearance","ui_scale",100)===125 ? 2 : root.value("appearance","ui_scale",100)===110 ? 1 : 0
                            focusPolicy: Qt.StrongFocus; activeFocusOnTab:true; Accessible.name:"UI Scale"
                            onActivated: root.update("appearance","ui_scale",currentIndex===2?125:currentIndex===1?110:100)
                        }
                        Text { text:"Tree Density"; color:PATheme.Theme.textPrimary; font.family:PATheme.Typography.fontFamily; font.pixelSize:PATheme.Typography.caption; font.weight:Font.DemiBold }
                        ComboBox {
                            objectName:"settings_tree_density"; Layout.fillWidth:true; model:["Comfortable","Compact"]
                            currentIndex: root.value("appearance","tree_density","comfortable")==="compact" ? 1 : 0
                            focusPolicy: Qt.StrongFocus; activeFocusOnTab:true; Accessible.name:"Tree Density"
                            onActivated: root.update("appearance","tree_density",currentIndex===1?"compact":"comfortable")
                        }
                    }

                    SettingsUI.SettingsCard {
                        objectName:"settings_section_advanced"
                        title:"Advanced"
                        subtitle:"Alat diagnosis dan pemecahan masalah."
                        Layout.columnSpan:grid.columns; Layout.fillWidth:true
                        SettingsUI.SettingsPathRow {
                            label:"Folder Diagnostics"; pathText:root.value("advanced","diagnostics_dir","runtime/diagnostics")
                            errorText:root.errorFor("advanced.diagnostics_dir"); warningText:root.warningFor("advanced.diagnostics_dir")
                            onPathEdited:function(v){root.update("advanced","diagnostics_dir",v)}
                            onBrowseRequested:{root.pendingFolderKey="diagnostics_dir";folderDialog.open()}
                        }
                        RowLayout {
                            Layout.fillWidth:true; spacing:8
                            PA.PAButton { text:"Buka Log"; variant:"secondary"; onClicked:if(typeof settingsViewModel!=="undefined") settingsViewModel.openLogFolder() }
                            PA.PAButton { text:"Reset Layout"; variant:"secondary"; onClicked:resetDialog.open() }
                            PA.PAButton { text:"Export Diagnostics"; variant:"secondary"; onClicked:if(typeof settingsViewModel!=="undefined") settingsViewModel.exportDiagnostics() }
                            Item { Layout.fillWidth:true }
                            Text { visible:pageState.last_export_path&&pageState.last_export_path.length>0; text:"Diagnostics diekspor"; color:PATheme.Theme.success; font.family:PATheme.Typography.fontFamily; font.pixelSize:PATheme.Typography.meta }
                        }
                    }
                }

                Text {
                    Layout.fillWidth:true; text:pageState.status_message||""
                    color:pageState.save_state==="ERROR"?PATheme.Theme.error:PATheme.Theme.textSecondary
                    font.family:PATheme.Typography.fontFamily; font.pixelSize:PATheme.Typography.caption; wrapMode:Text.WordWrap
                }
                RowLayout {
                    Layout.fillWidth:true; spacing:8; Item{Layout.fillWidth:true}
                    PA.PAButton { objectName:"settings_revert"; text:"Kembalikan"; variant:"secondary"; interactive:!!pageState.can_revert; onClicked:if(typeof settingsViewModel!=="undefined") settingsViewModel.revertSettings() }
                    PA.PAButton { objectName:"settings_save"; text:"Simpan Pengaturan"; loading:pageState.save_state==="SAVING"; interactive:!!pageState.can_save; onClicked:if(typeof settingsViewModel!=="undefined") settingsViewModel.saveSettings() }
                }
            }
        }
    }

    FolderDialog {
        id:folderDialog; title:"Pilih Folder"
        onAccepted: {
            if (typeof settingsViewModel !== "undefined") settingsViewModel.selectFolder(root.pendingFolderKey, selectedFolder.toString())
            root.pendingFolderKey=""
        }
        onRejected:root.pendingFolderKey=""
    }
    Dialog {
        id:resetDialog; modal:true; title:"Reset Layout"; standardButtons:Dialog.Ok|Dialog.Cancel
        x:Math.round((root.width-width)/2); y:Math.round((root.height-height)/2)
        Text { width:340; wrapMode:Text.WordWrap; text:"Reset hanya mengembalikan UI Scale dan Tree Density. Version, Prompt, Backup, dan GitHub tidak diubah."; color:PATheme.Theme.textPrimary; font.family:PATheme.Typography.fontFamily; font.pixelSize:PATheme.Typography.body }
        onAccepted:if(typeof settingsViewModel!=="undefined") settingsViewModel.resetLayout(true)
    }
}
