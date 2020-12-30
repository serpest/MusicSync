import abc
from mutagen.id3 import ID3

class Filter:
    @abc.abstractmethod
    def check(self, song_path, song):
        pass

class IntervalFilter(Filter):
    def check_interval(self, value, minimum, maximum):
        if value is None:
            return False
        minimum_check = True
        maximum_check = True
        if minimum is not None:
            minimum_check = value >= minimum
        if maximum is not None:
            maximum_check = value <= maximum
        return minimum_check and maximum_check


class RatingFilter(IntervalFilter):
    def __init__(self, minimum_rating = None, maximum_rating = None):
        self.minimum_rating = minimum_rating
        self.maximum_rating = maximum_rating

    def set_minimum_rating(self, minimum_rating):
        self.minimum_rating = minimum_rating

    def set_maximum_rating(self, maximum_rating):
        self.maximum_rating = maximum_rating

    def check(self, song_path, song):
        rating = self._get_rating(song_path, song)
        return self.check_interval(rating, minimum_rating, maximum_rating)

    def _get_rating(self, song_path, song):
        if song_path.endswith(".mp3"):
            return self._get_mp3_rating(song_path)
        elif song_path.endswith(".flac"):
            return self._get_flac_rating(song)
        return None

    def _get_mp3_rating(self, song_path):
        id3 = ID3(song_path)
        popm_key = self._get_first_popm_key(id3.keys())
        if popm_key:
            popm = id3.get(popm_key)
            rating = popm.rating / 51.0
            return rating
        return None

    def _get_first_popm_key(self, str_list):
        for key in str_list:
            if key.startswith("POPM:"):
                return key
        return None

    def _get_flac_rating(self, song):
        rating_list = song.get("rating")
        if rating_list:
            rating = int(rating_list[0]) / 20.0
            return rating
        return None


class YearFilter(IntervalFilter):
    def __init__(self, minimum_year = None, maximum_year = None):
        self.minimum_year = minimum_year
        self.maximum_year = maximum_year

    def set_minimum_year(self, minimum_year):
        self.minimum_year = minimum_year

    def set_maximum_year(self, maximum_year):
        self.maximum_year = maximum_year

    def check(self, song_path, song):
        year = self._get_year(song)
        return self.check_interval(year, minimum_year, maximum_year)

    def _get_year(self, song):
        try:
            return song["year"][0]
        except KeyError:
            pass
        try:
            return song["date"][0].split('-')[0]
        except KeyError:
            pass
        return None


class GenreFilter(Filter):
    pass


class ArtistFilter(Filter):
    pass
