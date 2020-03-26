import sys
from PySide2.QtWidgets import QApplication, QFileDialog
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import Slot

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
        lineEdit.setText(QFileDialog.getExistingDirectoryUrl().path())

    @Slot()
    def browseDestDirs(self):
        self.putExistingDirPathInLineEdit(self.window.destLine)

    @Slot()
    def copy(self):
        pass

    def show(self):
        self.window.show()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()