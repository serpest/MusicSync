import sys
import argparse

from musicsync.core.file_copiers import *
from musicsync.core.filters import *
from musicsync.core.controller import Controller

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
    controller = Controller(file_copier, filters)
    controller.sync(args.src, args.dest)

def _setup_parser():
    parser = argparse.ArgumentParser(description="Sync music library between devices and folders")
    parser.add_argument("src", metavar="<source>", type=str, help="the music source directory")
    parser.add_argument("dest", metavar="<destination>", type=str, help="the music destination directory")
    parser.add_argument("-r", "--rating", metavar="<arg>", action="store", dest="minimum_rating", type=float, help="set up minimum stars rating of the songs (0-5)")
    parser.add_argument("-y", "--year", metavar="<arg>", action="store", dest="minimum_year", type=str, help="set up minimum release year of the songs")
    #parser.add_argument("-l", "--log", action="store_true", help="create a log file")
    transfer_protocol = parser.add_mutually_exclusive_group(required=True)
    transfer_protocol.add_argument("-m", "--msc", action='store_true', dest="msc", help="Mass Storage Class (MSC)")
    transfer_protocol.add_argument("-a", "--adb", action='store_true', dest="adb", help="Android Debug Bridge (ADB)")
    return parser

def _validate_args(args):
    if (args.minimum_rating):
        _validate_rating(args.minimum_rating)

def _validate_rating(rating):
    if (not _is_rating_valid(rating)):
        raise ValueError("The rating value must be between 0 and 5.")

def _is_rating_valid(rating):
    return (rating >= 0 and rating <= 5)

def _setup_file_copier(args):
    file_copier = None
    if (args.msc):
        file_copier = MSCFileCopier()
    elif (args.adb):
        file_copier = ADBFileCopier()
    assert file_copier != None, "Trasfer protocol not selected."
    return file_copier

def _setup_filters(args):
    filters = []
    if (args.minimum_rating):
        filters.append(RatingFilter(args.minimum_rating))
    if (args.minimum_year):
        filters.append(YearFilter(args.minimum_year))
    return filters

if __name__ == "__main__":
    main()
