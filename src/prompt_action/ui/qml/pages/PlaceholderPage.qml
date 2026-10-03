import QtQuick
import "../theme" as PATheme
import "../components" as PA

Item {
    id: page
    property string pageTitle: "Foundation"
    property string stepLabel: "STEP"
    property string detail: "Konten final belum diimplementasikan pada STEP 03."

    PA.PASectionHeader {
        id: sectionHeader
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        title: page.pageTitle
        subtitle: "Design system dan UI shell aktif. Tidak ada data bisnis palsu pada placeholder ini."
    }

    PA.PACard {
        id: foundationCard
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: sectionHeader.bottom
        anchors.topMargin: PATheme.Metrics.space16
        height: Math.min(300, parent.height - sectionHeader.height - PATheme.Metrics.space16)

        PA.PAEmptyState {
            anchors.fill: parent
            anchors.margins: PATheme.Metrics.space16
            title: page.pageTitle + " content — " + page.stepLabel
            message: page.detail
        }
    }
}
