import os
import logging
import musicsync.core.file_copiers as file_copiers
import musicsync.core.format_conversion as format_conversion

SUPPORTED_FORMATS = (".mp3", ".flac") # Make sure to modify songs_metadata.py implementation before changing this value

class Controller():
    def __init__(self, file_copier, filters=[], output_format=None, output_bitrate=None):
        self.file_copier = file_copier
        self.filters = filters
        self.output_format = output_format
        self.output_bitrate = output_bitrate
        self.copied_songs_count = 0
        self.no_inspectable_songs_count = 0 # TODO: count corrupted files in self.no_inspectable_songs_count and display filenames in ControllerLogProxy log

    def sync(self, src, dest):
        try:
            self._manage_sync(src, dest)
        except (FileNotFoundError, file_copiers.FileCopierError) as exc:
            raise MusicSyncError(str(exc))

    def _manage_sync(self, src, dest):
        self._verify_source_dir(src)
        self._sync_songs(src, dest)
        return (self.copied_songs_count, self.no_inspectable_songs_count)

    def _verify_source_dir(self, src):
        if not os.path.isdir(src):
            raise FileNotFoundError("The source directory is not valid.")

    def _sync_songs(self, src, dest):
        for root, _, files in os.walk(src):
            for filename in files:
                if self._is_file_supported(filename):
                    song_path_src = os.path.join(root, filename)
                    song_path_dest = os.path.join(dest, os.path.relpath(song_path_src, src))
                    if not self.filters or self._check_filters(song_path_src):
                        self._copy_song(song_path_src, song_path_dest)
                        self._copy_song_lyrics(song_path_src, song_path_dest)

    def _copy_song(self, song_path_src, song_path_dest):
        self.file_copier.copy(_get_copy_file_function(song_path_src), song_path_dest)
        self.copied_songs_count += 1

    def _get_copy_file_function(self, song_path_src):
        if output_format is not None:
            return format_conversion.get_convert_and_copy_song_function(song_path_src, self.output_format, self.output_bitrate)
        return file_copiers.get_copy_file_function(song_path_src)

    def _copy_song_lyrics(self, song_path_src, song_path_dest):
        lyrics_path_src = self._get_lyrics_path(song_path_src)
        lyrics_path_dest = self._get_lyrics_path(song_path_dest)
        self.file_copier.copy(file_copiers.get_copy_file_function(lyrics_path_src), lyrics_path_dest)

    def _get_lyrics_path(self, song_path):
        # Same filename, different extension
        return os.path.splitext(song_path)[0] + ".lrc"

    def _is_file_supported(self, filename):
        return filename.lower().endswith(SUPPORTED_FORMATS)

    def _check_filters(self, song_path):
        for current_filter in self.filters:
            if not current_filter.check(song_path):
                return False
        return True


# This class does not implement the proxy pattern, so technically it is not a proxy, but the "Proxy" suffix in its name gives a good idea of what it does
class ControllerLogProxy(Controller):
    def __init__(self, file_copier, filters=[], output_format=None, output_bitrate=None, file_log=False):
        super().__init__(file_copier, filters, output_format, output_bitrate)
        self._init_logger()
        self._init_console_log()
        if file_log:
            self._init_file_log()

    def _init_logger(self):
        log_name = "MusicSync"
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(logging.INFO)

    def _init_console_log(self):
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _init_file_log(self):
        path = "MusicSync.log"
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler = logging.FileHandler(path, "a+", "utf-8")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def sync(self, src, dest):
        try:
            self._manage_sync(src, dest)
        except (FileNotFoundError, file_copiers.FileCopierError) as exc:
            self.logger.error(str(exc))
            raise MusicSyncError(str(exc))

    def _copy_song(self, song_path_src, song_path_dest):
        super()._copy_song(song_path_src, song_path_dest)
        logger.info("{} copied.".format(song_path_src))


class MusicSyncError(RuntimeError):
    pass
