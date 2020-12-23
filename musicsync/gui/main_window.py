import sys
import os
from threading import Thread
from types import SimpleNamespace
from PySide2.QtWidgets import QApplication, QFileDialog, QMessageBox
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QObject, Slot, Signal, QDir

import musicsync.core.controller

class MainWindow(QObject):

    show_summary_signal = Signal(int, int)
    show_copy_failed_Signal = Signal(str)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.copying_flag = False
        self.load_ui()
        self.setup_actions()

    def load_ui(self):
        loader = QUiLoader()
        self.window = loader.load("resources\\ui\\main_window.ui")

    def setup_actions(self):
        self.window.srcBrowseButton.clicked.connect(self.browseSrcDirs)
        self.window.destBrowseButton.clicked.connect(self.browseDestDirs)
        self.window.copyButton.clicked.connect(self.copy)
        self.show_summary_signal.connect(self.showSummary)
        self.show_copy_failed_Signal.connect(self.showCopyFailed)
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
        self.copying_flag = True
        self.window.statusbar.showMessage("Copying songs...")
        try:
            songsCount = Controller.copy(args)
            self.show_summary_signal.emit(songsCount[0], songsCount[1])
        except MusicSync.MusicSyncError as exc:
            self.show_copy_failed_Signal.emit(str(exc))
        finally:
            self.window.statusbar.showMessage("")
            self.copying_flag = False

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