import sys
import argparse

from musicsync.core.file_copiers import MSCFileCopier, ADBFileCopier
from musicsync.core.filters import RatingFilter, YearFilter, GenreFilter, ArtistFilter
from musicsync.core.controller import ControllerLogProxy

MIN_RATING_VALUE = 0
MAX_RATING_VALUE = 5

def main():
    parser = _setup_parser()
    args = parser.parse_args()
    try:
        _validate_args(args)
    except ValueError as exc:
        parser.error(str(exc))
        sys.exit(1)
    file_copier = _setup_file_copier(args)
    filters = _setup_filters(args)
    controller = ControllerLogProxy(file_copier, filters, args.log)
    controller.sync(args.src, args.dest)

def _setup_parser():
    parser = argparse.ArgumentParser(description="Sync music library between devices and folders")
    parser.add_argument("src", metavar="<source>", type=str, help="music library source directory")
    parser.add_argument("dest", metavar="<destination>", type=str, help="music library destination directory")
    rating_filters_group = parser.add_argument_group("rating filters", "set up minimum and/or maximum stars rating of the songs")
    rating_filters_group.add_argument("-r", "--min-rating", metavar="<arg>", action="store", dest="minimum_rating", type=float, help="minimum rating (0-5)")
    rating_filters_group.add_argument("-t", "--max-rating", metavar="<arg>", action="store", dest="maximum_rating", type=float, help="maximum rating (0-5)")
    year_filters_group = parser.add_argument_group("year filters", "set up minimum and/or maximum release year of the songs")
    year_filters_group.add_argument("-y", "--min-year", metavar="<arg>", action="store", dest="minimum_year", type=str, help="minimum release year")
    year_filters_group.add_argument("-u", "--max-year", metavar="<arg>", action="store", dest="maximum_year", type=str, help="maximum release year")
    other_filters_group = parser.add_argument_group("other filters")
    other_filters_group.add_argument("-g", "--genres", metavar="<arg>", action="store", dest="genres", type=str, nargs="+", help="type(s) of music")
    other_filters_group.add_argument("-i", "--artists", metavar="<arg>", action="store", dest="artists", type=str, nargs="+", help="song artist(s)")
    transfer_protocol_group = parser.add_argument_group("transfer protocol")
    transfer_protocol_mutually_exclusive_group = transfer_protocol_group.add_mutually_exclusive_group(required=True)
    transfer_protocol_mutually_exclusive_group.add_argument("-m", "--msc", action='store_true', dest="msc", help="Mass Storage Class (MSC)")
    transfer_protocol_mutually_exclusive_group.add_argument("-a", "--adb", action='store_true', dest="adb", help="Android Debug Bridge (ADB)")
    parser.add_argument("-l", "--log", action="store_true", help="create a log file")
    return parser

def _validate_args(args):
    if args.minimum_rating is not None:
        _validate_rating(args.minimum_rating)
    if args.maximum_rating is not None:
        _validate_rating(args.maximum_rating)

def _validate_rating(rating):
    if not _is_rating_valid(rating):
        raise ValueError(f"The rating value must be between {MIN_RATING_VALUE} and {MAX_RATING_VALUE}.")

def _is_rating_valid(rating):
    return rating >= MIN_RATING_VALUE and rating <= MAX_RATING_VALUE

def _setup_file_copier(args):
    if args.msc:
        return MSCFileCopier()
    elif args.adb:
        return ADBFileCopier()
    assert False, "Trasfer protocol not selected."

def _setup_filters(args):
    filters = []
    rating_filter = _setup_rating_filter(args)
    if rating_filter is not None:
        filters.append(rating_filter)
    year_filter = _setup_year_filter(args)
    if year_filter is not None:
        filters.append(year_filter)
    genre_filter = _setup_genre_filter(args)
    if genre_filter is not None:
        filters.append(genre_filter)
    artist_filter = _setup_artist_filter(args)
    if artist_filter is not None:
        filters.append(artist_filter)
    return filters

def _setup_rating_filter(args):
    if args.minimum_rating is not None or args.maximum_rating is not None:
        rating_filter = RatingFilter()
        if args.minimum_rating is not None:
            rating_filter.set_minimum_rating(args.minimum_rating)
        if args.maximum_rating is not None:
            rating_filter.set_maximum_rating(args.maximum_rating)
        return rating_filter
    return None

def _setup_year_filter(args):
    if args.minimum_year is not None or args.maximum_year is not None:
        year_filter = YearFilter()
        if args.minimum_year is not None:
            year_filter.set_minimum_year(args.minimum_year)
        if args.maximum_year is not None:
            year_filter.set_maximum_year(args.maximum_year)
        return year_filter
    return None

def _setup_genre_filter(args):
    if args.genres:
        return args.genres
    return None

def _setup_artist_filter(args):
    if args.artists:
        return args.artists
    return None

if __name__ == "__main__":
    main()
