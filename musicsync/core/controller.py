import os

from musicsync.core.file_copiers import MSCFileCopier, ADBFileCopier, FileCopierError

SUPPORTED_FORMATS = (".mp3", ".flac") # Make sure to modify songs_metadata.py implementation before changing this value

class Controller():
    def __init__(self, file_copier, filters):
        self.file_copier = file_copier
        self.filters = filters
        self.copied_songs_count = 0
        self.no_inspectable_songs_count = 0

    def sync(self, src, dest):
        try:
            self._verify_source_dir(src)
            self._sync_songs(src, dest)
            return (self.copied_songs_count, self.no_inspectable_songs_count)
        except (FileNotFoundError, FileCopierError) as exc:
            raise MusicSyncError(str(exc))

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
        self.file_copier.copy(song_path_src, song_path_dest)
        self.copied_songs_count += 1

    def _copy_song_lyrics(self, song_path_src, song_path_dest):
        lyrics_path_src = self._get_lyrics_path(song_path_src)
        lyrics_path_dest = self._get_lyrics_path(song_path_dest)
        self.file_copier.copy(lyrics_path_src, lyrics_path_dest)

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


class MusicSyncError(RuntimeError):
    pass
