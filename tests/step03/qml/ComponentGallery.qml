import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import "../../../src/prompt_action/ui/qml/components" as PA
import "../../../src/prompt_action/ui/qml/theme" as PATheme

Window {
    id: root
    objectName: "componentGallery"
    width: 1000
    height: 640
    visible: true
    color: PATheme.Theme.pageBackground
    property string galleryMode: "buttons"

    Loader {
        anchors.fill: parent
        anchors.margins: 28
        sourceComponent: root.galleryMode === "inputs" ? inputsGallery : root.galleryMode === "nav" ? navGallery : root.galleryMode === "status" ? statusGallery : buttonsGallery
    }

    Component {
        id: buttonsGallery
        Item {
            Column {
                spacing: 18
                Text { text: "Buttons & Cards"; font.family: PATheme.Typography.fontFamily; font.pixelSize: 22; font.weight: Font.DemiBold; color: PATheme.Theme.textPrimary }
                Row {
                    spacing: 12
                    PA.PAButton { objectName: "button_primary"; text: "Primary" }
                    PA.PAButton { objectName: "button_secondary"; text: "Secondary"; variant: "secondary" }
                    PA.PAButton { objectName: "button_disabled"; text: "Disabled"; interactive: false }
                    PA.PAButton { objectName: "button_loading"; text: "Loading"; loading: true }
                }
                Row {
                    spacing: 12
                    PA.PACard { objectName: "card_default"; width: 205; height: 120; Text { anchors.centerIn: parent; text: "Default"; color: PATheme.Theme.textPrimary } }
                    PA.PACard { objectName: "card_selected"; selected: true; width: 205; height: 120; Text { anchors.centerIn: parent; text: "Selected"; color: PATheme.Theme.textPrimary } }
                    PA.PACard { objectName: "card_warning"; tone: "warning"; width: 205; height: 120; Text { anchors.centerIn: parent; text: "Warning"; color: PATheme.Theme.textPrimary } }
                    PA.PACard { objectName: "card_error"; tone: "error"; width: 205; height: 120; Text { anchors.centerIn: parent; text: "Error"; color: PATheme.Theme.textPrimary } }
                }
            }
        }
    }

    Component {
        id: inputsGallery
        Item {
            Column {
                width: 620
                spacing: 16
                Text { text: "Inputs"; font.family: PATheme.Typography.fontFamily; font.pixelSize: 22; font.weight: Font.DemiBold; color: PATheme.Theme.textPrimary }
                PA.PAInput { objectName: "input_empty"; width: 420; placeholderText: "Nama snapshot" }
                PA.PAInput { objectName: "input_error"; width: 420; placeholderText: "Input bermasalah"; text: "Nilai"; invalid: true; errorText: "Contoh error" }
                PA.PAInput { objectName: "input_disabled"; width: 420; placeholderText: "Disabled"; enabled: false }
                PA.PASearchField { objectName: "search_field"; width: 420 }
            }
        }
    }

    Component {
        id: navGallery
        Item {
            Rectangle {
                width: 350
                height: 360
                radius: 14
                color: PATheme.Theme.sidebar
                Column {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 8
                    Text { text: "Navigation"; color: "white"; font.family: PATheme.Typography.fontFamily; font.pixelSize: 20; font.weight: Font.DemiBold }
                    PA.PANavItem { objectName: "nav_selected"; width: 300; text: "Dashboard"; route: "dashboard"; selected: true; iconSource: "../../../src/prompt_action/ui/assets/icons/dashboard.svg" }
                    PA.PANavItem { objectName: "nav_default"; width: 300; text: "Sejarah Sistem"; route: "system_history"; iconSource: "../../../src/prompt_action/ui/assets/icons/history.svg" }
                    PA.PAIconButton { objectName: "icon_button"; iconSource: "../../../src/prompt_action/ui/assets/icons/info.svg"; tooltipText: "Informasi"; accessibleName: "Buka informasi" }
                }
            }
        }
    }

    Component {
        id: statusGallery
        Item {
            Column {
                spacing: 16
                Text { text: "Status & Feedback"; font.family: PATheme.Typography.fontFamily; font.pixelSize: 22; font.weight: Font.DemiBold; color: PATheme.Theme.textPrimary }
                Row { spacing: 10
                    PA.PABadge { objectName: "badge_neutral"; text: "Neutral"; tone: "neutral" }
                    PA.PABadge { objectName: "badge_success"; text: "Success"; tone: "success" }
                    PA.PABadge { objectName: "badge_warning"; text: "Warning"; tone: "warning" }
                    PA.PABadge { objectName: "badge_error"; text: "Error"; tone: "error" }
                    PA.PABadge { objectName: "badge_draft"; text: "Draft"; tone: "draft" }
                    PA.PABadge { objectName: "badge_legacy"; text: "Legacy"; tone: "legacy" }
                }
                Row { spacing: 10
                    PA.PAStatusPill { objectName: "pill_success"; text: "Aman"; tone: "success" }
                    PA.PAStatusPill { objectName: "pill_warning"; text: "Perlu cek"; tone: "warning" }
                    PA.PAStatusPill { objectName: "pill_error"; text: "Gagal"; tone: "error" }
                }
                PA.PAErrorBanner { width: 620; text: "Contoh pesan error yang tetap terbaca tanpa mengandalkan warna." }
                PA.PASkeleton { width: 420 }
                PA.PASkeleton { width: 300 }
            }
        }
    }
}
