from threading import Thread
from PySide2.QtWidgets import QFileDialog, QMessageBox
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QObject, Slot, Signal, QDir

from musicsync.core.controller import *
from musicsync.core.file_copiers import *
from musicsync.core.filters import *

class MainWindow(QObject):
    show_summary_signal = Signal(int, int, int)
    show_copy_failed_signal = Signal(str)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.copying_flag = False
        self.load_ui()
        self.setup_actions()

    def load_ui(self):
        loader = QUiLoader()
        self.window = loader.load("musicsync\\resources\\ui\\main_window.ui")

    def setup_actions(self):
        self.window.srcBrowseButton.clicked.connect(self.browse_src_dirs)
        self.window.destBrowseButton.clicked.connect(self.browse_dest_dirs)
        self.window.syncButton.clicked.connect(self.sync)
        self.show_summary_signal.connect(self.show_summary)
        self.show_copy_failed_signal.connect(self.show_copy_failed)
        self.window.transferProtocolBox.currentTextChanged.connect(self.update_src_line)

    @Slot()
    def browse_src_dirs(self):
        self.put_existing_dir_path_in_lineedit(self.window.srcLine)

    def put_existing_dir_path_in_lineedit(self, lineedit):
        path = QDir.toNativeSeparators(QFileDialog.getExistingDirectoryUrl(self.window).path())
        if (os.name == "nt"):
            #Remove the root slash
            path = path[1:]
        lineedit.setText(path)

    @Slot()
    def browse_dest_dirs(self):
        self.put_existing_dir_path_in_lineedit(self.window.destLine)

    @Slot()
    def sync(self):
        if (self.copying_flag):
            QMessageBox.critical(self.window, "Copy not allowed", "There is already a copy task in progress.")
            return
        if (not self.confirm_copy()):
            return
        file_copier = self.get_file_copier()
        filters = self.get_filters()
        src = self.window.srcLine.text()
        dest = self.window.destLine.text()
        self.start_copy_process(file_copier, filters, src, dest)

    def get_file_copier(self):
        transfer_protocol_box_index = self.window.transferProtocolBox.currentIndex()
        if (transfer_protocol_box_index == 0):
            return MSCFileCopier()
        elif (transfer_protocol_box_index == 1):
            return ADBFileCopier()
        raise RuntimeError("Transfer protocol not selected")

    def get_filters(self):
        filters = []
        #Rating filter
        if (self.window.minimumRatingCheckBox.isChecked()):
            minimum_rating = self.window.minimumRatingSpinBox.value()
            filters.append(RatingFilter(minimum_rating))
        #Year filter
        if (self.window.minimumYearCheckBox.isChecked()):
            minimum_year = str(self.window.minimumYearSpinBox.value())
            filters.append(YearFilter(minimum_year))
        return filters

    def confirm_copy(self):
        answer = QMessageBox.question(self.window, "Copy confirmation", "Do you want to start the copy?")
        return (QMessageBox.StandardButton.Yes == answer)

    def start_copy_process(self, file_copier, filters, src, dest):
        thread = Thread(target=self.manage_copy, args=(file_copier, filters, src, dest))
        thread.start()
    
    def manage_copy(self, file_copier, filters, src, dest):
        self.copying_flag = True
        self.window.statusbar.showMessage("Syncing songs...")
        try:
            controller = Controller(file_copier, filters)
            songs_counts = controller.sync(src, dest)
            copied_songs_count, no_inspectable_songs_count, corrupted_song_files_count = songs_counts
            self.show_summary_signal.emit(copied_songs_count, no_inspectable_songs_count, corrupted_song_files_count)
        except MusicSyncError as exc:
            self.show_copy_failed_Signal.emit(str(exc))
        finally:
            self.window.statusbar.showMessage("")
            self.copying_flag = False

    @Slot(int, int)
    def show_summary(self, copied_songs_count, no_inspectable_songs_count, corrupted_song_files_count):
        QMessageBox.information(self.window, "Summary", f"Copied songs: {copied_songs_count}\nNot inspected songs: {no_inspectable_songs_count}\nCorrupted song files: {corrupted_song_files_count}")

    @Slot(str)
    def show_copy_failed(self, message):
        QMessageBox.critical(self.window, "Copy failed", message)

    @Slot()
    def update_src_line(self):
        adb_text = "ADB device"
        if (self.window.transferProtocolBox.currentIndex() == 1): #ADB seleted
            self.window.srcBrowseButton.setEnabled(False)
            self.window.srcLine.setEnabled(False)
            self.window.srcLine.setText(adb_text)
        else:
            self.window.srcBrowseButton.setEnabled(True)
            self.window.srcLine.setEnabled(True)
            if (self.window.srcLine.text() == adb_text):
                self.window.srcLine.setText("")

    def show(self):
        self.window.show()
