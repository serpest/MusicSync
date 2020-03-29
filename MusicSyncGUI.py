import sys
from types import SimpleNamespace
from PySide2.QtWidgets import QApplication, QFileDialog, QMessageBox
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import Slot

import MusicSync

class MainWindow():
    def __init__(self):
        self.loadUi()
        self.setupActions()

    def loadUi(self):
        loader = QUiLoader()
        self.window = loader.load("MainWindow.ui")

    def setupActions(self):
        self.window.srcBrowseButton.clicked.connect(self.browseSrcDirs)
        self.window.destBrowseButton.clicked.connect(self.browseDestDirs)
        self.window.copyButton.clicked.connect(self.copy)

    @Slot()
    def browseSrcDirs(self):
        self.putExistingDirPathInLineEdit(self.window.srcLine)

    def putExistingDirPathInLineEdit(self, lineEdit):
        lineEdit.setText(QFileDialog.getExistingDirectoryUrl(self.window).path())

    @Slot()
    def browseDestDirs(self):
        self.putExistingDirPathInLineEdit(self.window.destLine)

    @Slot()
    def copy(self):
        if (not self.confirmCopy()):
            return
        args = self.getCopyArgs()
        self.window.statusbar.showMessage("Copying songs...")
        songsCount = MusicSync.startCopy(args)
        self.window.statusbar.showMessage("")
        self.showSummary(songsCount)

    def confirmCopy(self):
        answer = QMessageBox.question(self.window, "Copy confirmation", "Do you want to start the copy?")
        return (QMessageBox.StandardButton.Yes == answer)
    
    def showSummary(self, songsCount):
        QMessageBox.information(self.window, "Summary", f"Copied songs: {songsCount[0]}\nNot inspected songs: {songsCount[1]}")

    def getCopyArgs(self):
        namespace = SimpleNamespace()
        #Source directory
        namespace.src = self.window.srcLine.text()
        #Destination directory
        namespace.dest = self.window.destLine.text()
        #Transfer protocol
        transferProtocolBoxIndex = self.window.transferProtocolBox.currentIndex()
        namespace.msc = (transferProtocolBoxIndex == 0)
        namespace.adb = (transferProtocolBoxIndex == 1)
        #Minimum rating filter
        if (self.window.minimumRatingCheckBox.isChecked()):
            namespace.minimumRating = self.window.minimumRatingSpinBox.value()
        else:
            namespace.minimumRating = None
        #Minimum year filter
        if (self.window.minimumYearCheckBox.isChecked()):
            namespace.minimumYear = self.window.minimumYearSpinBox.value()
        else:
            namespace.minimumYear = None
        return namespace

    def show(self):
        self.window.show()



def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()