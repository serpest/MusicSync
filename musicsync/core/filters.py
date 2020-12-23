from mutagen.id3 import ID3

class Filter:
    @abstractmethod
    def filter(self, song):
        pass


class RatingFilter(Filter):
    def __init__(self, minimum_rating):
        self.minimum_rating = minimum_rating

    def filter(self, song):
        rating = self.get_rating(song)
        if (rating):
            return rating >= self.minimum_rating
        return False

    def get_rating(self, song):
        mp3, flac = (".mp3", ".flac")
        song_path = song[0]
        if song_path.endswith(mp3):
            return get_mp3_rating(song_path)
        elif song_path.endswith(flac):
            return get_flac_rating(song)
        return None

    def get_mp3_rating(self, song_path):
        id3 = ID3(song_path)
        popm_key = get_first_popm_key(id3.keys())
        if (popm_key):
            popm = id3.get(popm_key)
            rating = popm.rating / 51
            return rating
        return None

    def get_first_popm_key(self, str_list):
        for key in str_list:
            if (key.startswith("POPM:")):
                return key
        return None

    def get_flac_rating(self, song):
        rating_list = song[1].get("rating")
        if (rating_list):
            rating = int(rating_list[0]) / 20.0
            return rating
        return None


class YearFilter(Filter):
    def __init__(self, minimum_year):
        self.minimum_year = minimum_year

    def filter(self, song):
        year = get_year(song)
        if (year):
            return year >= self.minimum_year 
        return False

    def get_year(self, song):
        try:
            return song[1]["year"][0]
        except KeyError:
            pass
        try:
            return song[1]["date"][0].split('-')[0]
        except KeyError:
            pass
        return None


class GenreFilter(Filter):
    pass


class ArtistFilter(Filter):
    pass
