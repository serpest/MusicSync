import argparse
import os
import shutil
import eyed3

copiedSongsCount = 0

songsNotInspectedCount = 0

def initInfoFiles():
    global copiedSongsFile
    global songsNotInspectedFile
    copiedSongsFile = open("copiedSongs.txt", "a+")
    songsNotInspectedFile = open("songsNotInspected.txt", "a+")

def closeInfoFiles():
    copiedSongsFile.close()
    songsNotInspectedFile.close()

def addSongToCopiedSongsFile(song):
    copiedSongsFile.write(song + '\n')

def addSongToSongsNotInspectedFile(song):
    songsNotInspectedFile.write(song + '\n')

def verifySrcAndDest(src, dest):
    if not (os.path.isdir(src)):
        raise FileNotFoundError("The source directory doesn't exist.")
    if not (os.path.isdir(dest)):
        os.makedirs(dest)

def copySong(srcFilePath, destFilePath):
    if (os.path.isfile(destFilePath)):
        return
    destDirPath = os.path.dirname(destFilePath)
    if not (os.path.isdir(destDirPath)):
        os.makedirs(destDirPath)
    shutil.copy2(srcFilePath, destDirPath)
    addSongToCopiedSongsFile(os.path.abspath(srcFilePath))
    global copiedSongsCount
    copiedSongsCount += 1

def checkFilters(songPath, filters):
    song = eyed3.load(songPath)
    if (not song and len(filters) != 0):
        addSongToSongsNotInspectedFile(os.path.abspath(songPath))
        global songsNotInspectedCount
        songsNotInspectedCount += 1
        return False
    for filter in filters:
        if (not filter(song)):
            return False
    return True

def syncSongs(src, dest, filters):
    verifySrcAndDest(src, dest)
    for root, _, files in os.walk(src):
        for file in files:
            if (file.lower().endswith((".mp3", ".aac", ".ogg", ".flac", ".wav"))):
                songPathDest = os.path.join(dest, os.path.relpath(os.path.join(root, file), src))
                if (checkFilters(os.path.join(root, file), filters)):
                    copySong(os.path.join(root, file), songPathDest)

def ratingFilter(song, minimumRating):
    for popm in song.tag.popularities:
        if popm.rating >= minimumRating:
            return True
    return False

def yearFilter(song, minimumYear):
    date = song.tag.getBestDate()
    if (date):
        return date.year >= minimumYear 
    return False

def initParser():
    parser = argparse.ArgumentParser(description="Sync music automatically. You can use filters to select the songs to copy.")
    parser.add_argument("src", metavar="<source>", type=str, help="the music source directory")
    parser.add_argument("dest", metavar="<destination>", type=str, help="the music destination directory")
    rating = parser.add_mutually_exclusive_group(required=False)
    rating.add_argument("-r", metavar="<arg>", action="store", dest="minimumByteRating", type=int, help="set up minimum rating of the songs (1-255)")
    rating.add_argument("-s", metavar="<arg>", action="store", dest="minimumStarsRating", type=int, help="set up minimum stars rating of the songs (1-5)")
    parser.add_argument("-y", metavar="<arg>", action="store", dest="minimumYear", type=int, help="set up minimum release year of the songs")
    return parser

def setupFilters(parser, args):
    filters = []
    if (args.minimumByteRating):
        filters.append(lambda file : ratingFilter(file, args.minimumByteRating))
    elif (args.minimumStarsRating):
        if (args.minimumStarsRating < 1 or args.minimumStarsRating > 5):
            parser.error("The minimum stars rating value must be between 1 and 5.")
        setupFilters.starsToRating = [1, 32, 96, 160, 224] #Windows Explorer standards (https://en.wikipedia.org/wiki/ID3#ID3v2_rating_tag_issue)
        filters.append(lambda file : ratingFilter(file, setupFilters.starsToRating[args.minimumStarsRating - 1]))
    if (args.minimumYear):
        filters.append(lambda file : yearFilter(file, args.minimumYear))
    return filters

def printSummary():
    print("Copied songs:", copiedSongsCount)
    print("Not inspected songs:", songsNotInspectedCount)

def main():
    eyed3.log.setLevel("ERROR")
    parser = initParser()
    args = parser.parse_args()
    filters = setupFilters(parser, args)
    try:
        initInfoFiles()
        syncSongs(args.src, args.dest, filters)
        closeInfoFiles()
        printSummary()
    except FileNotFoundError as exc:
        parser.error(str(exc))

if (__name__ == "__main__"):
    main()
