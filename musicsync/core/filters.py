import abc

from musicsync.core.songs_metadata import get_rating, get_year, NoGettableMetadata


def _check_interval(value, minimum, maximum):
    if value is None:
        return False
    minimum_check = True
    maximum_check = True
    if minimum is not None:
        minimum_check = value >= minimum
    if maximum is not None:
        maximum_check = value <= maximum
    return minimum_check and maximum_check


class Filter:
    @abc.abstractmethod
    def check(self, song_path):
        pass


class RatingFilter(Filter):
    def __init__(self, minimum_rating=None, maximum_rating=None):
        self._minimum_rating = minimum_rating
        self._maximum_rating = maximum_rating

    def set_minimum_rating(self, minimum_rating):
        self._minimum_rating = minimum_rating

    def set_maximum_rating(self, maximum_rating):
        self._maximum_rating = maximum_rating

    def check(self, song_path):
        try:
            rating = get_rating(song_path)
            return _check_interval(rating, self._minimum_rating, self._maximum_rating)
        except NoGettableMetadata:
            return False


class YearFilter(Filter):
    def __init__(self, minimum_year=None, maximum_year=None):
        self._minimum_year = minimum_year
        self._maximum_year = maximum_year

    def set_minimum_year(self, minimum_year):
        self._minimum_year = minimum_year

    def set_maximum_year(self, maximum_year):
        self._maximum_year = maximum_year

    def check(self, song_path):
        try:
            year = get_year(song_path)
            return _check_interval(year, self._minimum_year, self._maximum_year)
        except NoGettableMetadata:
            return False


class GenreFilter(Filter):
    pass


class ArtistFilter(Filter):
    pass
