import argparse
import os
import shutil
import mutagen
from mutagen.id3 import ID3

supportedFormats = (".mp3", ".flac") #Tuple of supported formats. It is useful if you add new formats because with that you can see the functions to modify to execute the program correctly

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
    song = mutagen.File(songPath, easy=True)
    if (not song and len(filters) != 0):
        addSongToSongsNotInspectedFile(os.path.abspath(songPath))
        global songsNotInspectedCount
        songsNotInspectedCount += 1
        return False
    for filter in filters:
        if (not filter((songPath, song))):
            return False
    return True

def syncSongs(src, dest, filters):
    verifySrcAndDest(src, dest)
    for root, _, files in os.walk(src):
        for file in files:
            if (file.lower().endswith(supportedFormats)):
                songPathDest = os.path.join(dest, os.path.relpath(os.path.join(root, file), src))
                if (checkFilters(os.path.join(root, file), filters)):
                    copySong(os.path.join(root, file), songPathDest)

def getFirstPOPMKey(strList):
    for key in strList:
        if (key.startswith("POPM:")):
            return key
    return None

def getRating(song):
    mp3, flac = supportedFormats #If there are new supported formats an exception will thrown
    if song[0].endswith(mp3):
        id3 = ID3(song[0])
        popmKey = getFirstPOPMKey(id3.keys())
        if (popmKey):
            popm = id3.get(popmKey)
            return popm.rating
    elif song[0].endswith(flac):
        rating = song[1].get("rating")
        if (rating):
            rating = int(rating[0]) / 20.0
    return None

def getYear(song):
    try:
        return song[1]["year"][0]
    except KeyError:
        pass
    try:
        return song[1]["date"][0].split('-')[0]
    except KeyError:
        pass
    return None

def ratingFilter(song, minimumRating):
    rating = getRating(song)
    if (rating):
        return rating >= minimumRating
    return False

def yearFilter(song, minimumYear):
    year = getYear(song)
    if (year):
        return year >= minimumYear 
    return False

def initParser():
    parser = argparse.ArgumentParser(description="Sync music automatically. You can use filters to select the songs to copy.")
    parser.add_argument("src", metavar="<source>", type=str, help="the music source directory")
    parser.add_argument("dest", metavar="<destination>", type=str, help="the music destination directory")
    parser.add_argument("-r", metavar="<arg>", action="store", dest="minimumRating", type=float, help="set up minimum stars rating of the songs (0-5)")
    parser.add_argument("-y", metavar="<arg>", action="store", dest="minimumYear", type=str, help="set up minimum release year of the songs")
    return parser

def setupFilters(parser, args):
    filters = []
    if (args.minimumRating):
        if (args.minimumRating < 0 or args.minimumRating > 5):
            parser.error("The minimum stars rating value must be between 0 and 5.")
        filters.append(lambda file : ratingFilter(file, args.minimumRating))
    if (args.minimumYear):
        filters.append(lambda file : yearFilter(file, args.minimumYear))
    return filters

def printSummary():
    print("Copied songs:", copiedSongsCount)
    print("Not inspected songs:", songsNotInspectedCount)

def main():
    parser = initParser()
    args = parser.parse_args()
    filters = setupFilters(parser, args)
    try:
        initInfoFiles()
        syncSongs(args.src, args.dest, filters)
        printSummary()
        closeInfoFiles()
    except FileNotFoundError as exc:
        parser.error(str(exc))

if (__name__ == "__main__"):
    main()
