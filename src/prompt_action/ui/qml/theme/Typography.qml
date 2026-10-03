pragma Singleton
import QtQuick

QtObject {
    // Use a Windows-standard UI-compatible family that is present on Windows 11
    // and on the CI Windows image. No font files are bundled with Prompt Action.
    readonly property string fontFamily: "Arial"
    readonly property string monoFamily: "Consolas"
    readonly property int pageTitle: 24
    readonly property int sectionTitle: 17
    readonly property int cardTitle: 14
    readonly property int body: 13
    readonly property int caption: 12
    readonly property int meta: 11
    readonly property int button: 13
}
