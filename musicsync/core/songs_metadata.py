import mutagen

def get_rating(song_path):
    if song_path.endswith(".mp3"):
        return _get_mp3_rating(song_path)
    elif song_path.endswith(".flac"):
        return _get_flac_rating(song_path)
    return None

def _get_mp3_rating(song_path):
    id3 = mutagen.id3.ID3(song_path)
    popm_key = _get_first_popm_key(id3.keys())
    if popm_key:
        popm = id3.get(popm_key)
        rating = popm.rating / 51.0
        return rating
    return None

def _get_first_popm_key(str_list):
    for key in str_list:
        if key.startswith("POPM:"):
            return key
    return None

def _get_flac_rating(song_path):
    song = _get_mutagen_song(song_path)
    rating_list = song.get("rating")
    if rating_list:
        rating = int(rating_list[0]) / 20.0
        return rating
    return None

def _get_mutagen_song(song_path):
    try:
        return mutagen.File(song_path, easy=True)
    except (mutagen.mp3.HeaderNotFoundError, mutagen.flac.FLACNoHeaderError) as exc:
        raise NoGettableMetadata(str(exc))


def get_year(song_path):
    song = _get_mutagen_song(song_path)
    try:
        return int(song["year"][0])
    except KeyError:
        pass
    try:
        return int(song["date"][0].split('-')[0])
    except KeyError:
        pass
    return None


def get_artist(song_path):
    song = _get_mutagen_song(song_path)
    if "artist" in song:
        return song["artist"]
    return None


def get_genre(song_path):
    song = _get_mutagen_song(song_path)
    if "genre" in song:
        return song["genre"]
    return None


class NoGettableMetadata(RuntimeError):
    pass
