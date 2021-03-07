import os
from threading import Thread
from PySide2.QtWidgets import QFileDialog, QMessageBox
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QObject, Slot, Signal, QDir
from PySide2.QtGui import QIcon

from musicsync.core.controller import Controller, MusicSyncError
from musicsync.core.file_copiers import ADBFileCopier, MSCFileCopier
from musicsync.core.filters import RatingFilter, YearFilter, GenreFilter, ArtistFilter

ITEMS_SEPARATOR = ", "

class MainWindow(QObject):
    show_summary_signal = Signal(int, int)
    show_copy_failed_signal = Signal(str)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.copying_flag = False
        self.load_ui()
        self.setup_window_icon()
        self.setup_actions()

    def load_ui(self):
        loader = QUiLoader()
        self.window = loader.load("musicsync\\resources\\ui\\main_window.ui")

    def setup_window_icon(self):
        icon = QIcon("musicsync\\resources\\images\\icon.png")
        self.window.setWindowIcon(icon)

    def setup_actions(self):
        self.window.srcBrowseButton.clicked.connect(self.browse_src_dirs)
        self.window.destBrowseButton.clicked.connect(self.browse_dest_dirs)
        self.window.syncButton.clicked.connect(self.sync)
        self.show_summary_signal.connect(self.show_summary)
        self.show_copy_failed_signal.connect(self.show_copy_failed)
        self.window.transferProtocolBox.currentTextChanged.connect(self.update_srcline)
        self.window.artistsCheckBox.clicked.connect(self.update_artistsline)
        self.window.genresCheckBox.clicked.connect(self.update_genresline)
        self.window.minimumRatingCheckBox.clicked.connect(self.update_minimumratingspinbox)
        self.window.maximumRatingCheckBox.clicked.connect(self.update_maximumratingspinbox)
        self.window.minimumYearCheckBox.clicked.connect(self.update_minimumyearspinbox)
        self.window.maximumYearCheckBox.clicked.connect(self.update_maximumyearspinbox)


    @Slot()
    def browse_src_dirs(self):
        self.put_existing_dir_path_in_lineedit(self.window.srcLine)

    def put_existing_dir_path_in_lineedit(self, lineedit):
        path = QDir.toNativeSeparators(QFileDialog.getExistingDirectoryUrl(self.window).path())
        if (os.name == "nt"):
            # Remove the root slash
            path = path[1:]
        lineedit.setText(path)

    @Slot()
    def browse_dest_dirs(self):
        self.put_existing_dir_path_in_lineedit(self.window.destLine)

    @Slot()
    def sync(self):
        if self.copying_flag:
            QMessageBox.critical(self.window, "Copy not allowed", "There is already a copy task in progress.")
            return
        if not self.confirm_copy():
            return
        file_copier = self.get_file_copier()
        filters = self.get_filters()
        src = self.window.srcLine.text()
        dest = self.window.destLine.text()
        self.start_copy_process(file_copier, filters, src, dest)

    def get_file_copier(self):
        transfer_protocol_box_index = self.window.transferProtocolBox.currentIndex()
        if transfer_protocol_box_index == 0:
            return MSCFileCopier()
        elif transfer_protocol_box_index == 1:
            return ADBFileCopier()
        assert False, "Trasfer protocol not selected."

    def get_filters(self):
        filters = []
        rating_filter = self._setup_rating_filter()
        if rating_filter is not None:
            filters.append(rating_filter)
        year_filter = self._setup_year_filter()
        if year_filter is not None:
            filters.append(year_filter)
        genre_filter = self._setup_genre_filter()
        if genre_filter is not None:
            filters.append(genre_filter)
        artist_filter = self._setup_artist_filter()
        if artist_filter is not None:
            filters.append(artist_filter)
        return filters

    def _setup_rating_filter(self):
        if self.window.minimumRatingCheckBox.isChecked() or self.window.maximumRatingCheckBox.isChecked():
            rating_filter = RatingFilter()
            if self.window.minimumRatingCheckBox.isChecked():
                rating_filter.set_minimum_rating(self.window.minimumRatingSpinBox.value())
            if self.window.maximumRatingCheckBox.isChecked():
                rating_filter.set_maximum_rating(self.window.maximumRatingSpinBox.value())
            return rating_filter
        return None

    def _setup_year_filter(self):
        if self.window.minimumYearCheckBox.isChecked() or self.window.maximumYearCheckBox.isChecked():
            year_filter = YearFilter()
            if self.window.minimumYearCheckBox.isChecked():
                year_filter.set_minimum_year(self.window.minimumYearSpinBox.value())
            if self.window.maximumYearCheckBox.isChecked():
                year_filter.set_maximum_year(self.window.maximumYearSpinBox.value())
            return year_filter
        return None

    def _setup_genre_filter(self):
        if self.window.genresCheckBox.isChecked():
            # TODO: Put item separators tip in GUI
            genres = self.window.genresLine.text().split(ITEMS_SEPARATOR)
            return GenreFilter(genres)
        return None

    def _setup_artist_filter(self):
        if self.window.artistsCheckBox.isChecked():
            artists = self.window.artistsLine.text().split(ITEMS_SEPARATOR)
            return ArtistFilter(artists)
        return None

    def confirm_copy(self):
        answer = QMessageBox.question(self.window, "Copy confirmation", "Do you want to start the copy?")
        return QMessageBox.StandardButton.Yes == answer

    def start_copy_process(self, file_copier, filters, src, dest):
        thread = Thread(target=self.manage_copy, args=(file_copier, filters, src, dest))
        thread.start()
    
    def manage_copy(self, file_copier, filters, src, dest):
        self.copying_flag = True
        self.window.statusbar.showMessage("Syncing songs...")
        try:
            controller = Controller(file_copier, filters)
            songs_counts = controller.sync(src, dest)
            copied_songs_count, no_inspectable_songs_count = songs_counts
            self.show_summary_signal.emit(copied_songs_count, no_inspectable_songs_count)
        except MusicSyncError as exc:
            self.show_copy_failed_signal.emit(str(exc))
        finally:
            self.window.statusbar.showMessage("")
            self.copying_flag = False

    @Slot(int, int)
    def show_summary(self, copied_songs_count, no_inspectable_songs_count):
        QMessageBox.information(self.window, "Summary", f"Copied songs: {copied_songs_count}\nNo inspectable songs: {no_inspectable_songs_count}")

    @Slot(str)
    def show_copy_failed(self, message):
        QMessageBox.critical(self.window, "Copy failed", message)

    @Slot()
    def update_srcline(self):
        adb_text = "ADB device"
        if self.window.transferProtocolBox.currentIndex() == 0: # MSC seleted
            self.window.destBrowseButton.setEnabled(True)
            self.window.destLine.setEnabled(True)
            self.window.destLine.setText("")
        else: # ADB seleted
            self.window.destBrowseButton.setEnabled(False)
            self.window.destLine.setEnabled(False)
            self.window.destLine.setText(adb_text)

    @Slot()
    def update_artistsline(self):
        self.window.artistsLine.setEnabled(self.window.artistsCheckBox.isChecked())

    @Slot()
    def update_genresline(self):
        self.window.genresLine.setEnabled(self.window.genresCheckBox.isChecked())

    @Slot()
    def update_minimumratingspinbox(self):
        self.window.minimumRatingSpinBox.setEnabled(self.window.minimumRatingCheckBox.isChecked())

    @Slot()
    def update_maximumratingspinbox(self):
        self.window.maximumRatingSpinBox.setEnabled(self.window.maximumRatingCheckBox.isChecked())

    @Slot()
    def update_minimumyearspinbox(self):
        self.window.minimumYearSpinBox.setEnabled(self.window.minimumYearCheckBox.isChecked())

    @Slot()
    def update_maximumyearspinbox(self):
        self.window.maximumYearSpinBox.setEnabled(self.window.maximumYearCheckBox.isChecked())

    def show(self):
        self.window.show()
