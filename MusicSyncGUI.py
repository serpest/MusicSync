import sys
import os
from threading import Thread
from types import SimpleNamespace
from PySide2.QtWidgets import QApplication, QFileDialog, QMessageBox
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QObject, Slot, Signal, QDir

import MusicSync

class MainWindow(QObject):

    showSummarySignal = Signal(int, int)
    showCopyFailedSignal = Signal(str)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.copyingFlag = False
        self.loadUi()
        self.setupActions()

    def loadUi(self):
        loader = QUiLoader()
        uiPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MainWindow.ui")
        self.window = loader.load(uiPath)

    def setupActions(self):
        self.window.srcBrowseButton.clicked.connect(self.browseSrcDirs)
        self.window.destBrowseButton.clicked.connect(self.browseDestDirs)
        self.window.copyButton.clicked.connect(self.copy)
        self.showSummarySignal.connect(self.showSummary)
        self.showCopyFailedSignal.connect(self.showCopyFailed)
        self.window.transferProtocolBox.currentTextChanged.connect(self.updateSrcLine)

    @Slot()
    def browseSrcDirs(self):
        self.putExistingDirPathInLineEdit(self.window.srcLine)

    def putExistingDirPathInLineEdit(self, lineEdit):
        path = QDir.toNativeSeparators(QFileDialog.getExistingDirectoryUrl(self.window).path())
        if (os.name == "nt"):
            #Remove the root slash
            path = path[1:]
        lineEdit.setText(path)

    @Slot()
    def browseDestDirs(self):
        self.putExistingDirPathInLineEdit(self.window.destLine)

    @Slot()
    def copy(self):
        if (self.copyingFlag):
            QMessageBox.critical(self.window, "Copy not allowed", "There is already a copy task in progress.")
            return
        if (not self.confirmCopy()):
            return
        args = self.getCopyArgs()
        self.startCopyProcess(args)

    def confirmCopy(self):
        answer = QMessageBox.question(self.window, "Copy confirmation", "Do you want to start the copy?")
        return (QMessageBox.StandardButton.Yes == answer)

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
            namespace.minimumYear = str(self.window.minimumYearSpinBox.value())
        else:
            namespace.minimumYear = None
        return namespace

    def startCopyProcess(self, args):
        thread = Thread(target=self.manageCopy, args=(args, ))
        thread.start()
    
    def manageCopy(self, args):
        self.copyingFlag = True
        self.window.statusbar.showMessage("Copying songs...")
        try:
            songsCount = MusicSync.startCopy(args)
            self.showSummarySignal.emit(songsCount[0], songsCount[1])
        except MusicSync.MusicSyncError as exc:
            self.showCopyFailedSignal.emit(str(exc))
        finally:
            self.window.statusbar.showMessage("")
            self.copyingFlag = False

    @Slot(int, int)
    def showSummary(self, copiedSongsNumber, notInspectedSongsNumber):
        QMessageBox.information(self.window, "Summary", f"Copied songs: {copiedSongsNumber}\nNot inspected songs: {notInspectedSongsNumber}")

    @Slot(str)
    def showCopyFailed(self, message):
        QMessageBox.critical(self.window, "Copy failed", message)

    @Slot()
    def updateSrcLine(self):
        adbText = "ADB device"
        if (self.window.transferProtocolBox.currentIndex() == 1): #ADB seleted
            self.window.srcBrowseButton.setEnabled(False)
            self.window.srcLine.setEnabled(False)
            self.window.srcLine.setText(adbText)
        else:
            self.window.srcBrowseButton.setEnabled(True)
            self.window.srcLine.setEnabled(True)
            if (self.window.srcLine.text() == adbText):
                self.window.srcLine.setText("")

    def show(self):
        self.window.show()



def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()