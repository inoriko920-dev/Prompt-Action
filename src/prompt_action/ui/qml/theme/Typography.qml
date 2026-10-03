pragma Singleton
import QtQuick

QtObject {
    // Empty family delegates to Qt's application/system default font.
    // On Windows 11 this follows the native Windows UI font without bundling font files.
    readonly property string fontFamily: ""
    readonly property string monoFamily: "Consolas"
    readonly property int pageTitle: 24
    readonly property int sectionTitle: 17
    readonly property int cardTitle: 14
    readonly property int body: 13
    readonly property int caption: 12
    readonly property int meta: 11
    readonly property int button: 13
}
