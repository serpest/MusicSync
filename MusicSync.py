import argparse
import os
import shutil
import mutagen
from mutagen.id3 import ID3
from ppadb.client import Client as AdbClient

supportedFormats = (".mp3", ".flac") #If you add new formats you can see easily the functions to modify

copiedSongsCount = 0

songsNotInspectedCount = 0

device = 0

def main():
    parser = setupParser()
    args = parser.parse_args()
    filters = setupFilters(parser, args)
    copySongFunction = setupCopySongFunction(args)
    verifySourceDir(args.src)
    initAll(args)
    syncSongs(args.src, args.dest, filters, copySongFunction)
    closeAll(args)
    printSummary()

def setupParser():
    parser = argparse.ArgumentParser(description="Sync music automatically. You can use filters to select the songs to copy.")
    parser.add_argument("src", metavar="<source>", type=str, help="the music source directory")
    parser.add_argument("dest", metavar="<destination>", type=str, help="the music destination directory")
    parser.add_argument("-r", "--rating", metavar="<arg>", action="store", dest="minimumRating", type=float, help="set up minimum stars rating of the songs (0-5)")
    parser.add_argument("-y", "--year", metavar="<arg>", action="store", dest="minimumYear", type=str, help="set up minimum release year of the songs")
    transferProtocol = parser.add_mutually_exclusive_group(required=True)
    transferProtocol.add_argument("-m", "--msc", action='store_true', dest="msc", help="Mass Storage Class (MSC)")
    transferProtocol.add_argument("-a", "--adb", action='store_true', dest="adb", help="Android Debug Bridge (ADB)")
    return parser

def setupFilters(parser, args):
    filters = []
    if (args.minimumRating):
        filters.append(setupMinimumRatingFilter(parser, args))
    if (args.minimumYear):
        filters.append(setupMinimumYearFilter(args))
    return filters

def setupMinimumRatingFilter(parser, args):
    if (not isRatingValid(args.minimumRating)):
        parser.error("The minimum stars rating value must be between 0 and 5.")
    return lambda file : ratingFilter(file, args.minimumRating)

def isRatingValid(rating):
    return (rating >= 0 or rating <= 5)

def setupMinimumYearFilter(args):
    return lambda file : yearFilter(file, args.minimumYear)

def ratingFilter(song, minimumRating):
    rating = getRating(song)
    if (rating):
        return rating >= minimumRating
    return False

def getRating(song):
    mp3, flac = supportedFormats
    songPath = song[0]
    if songPath.endswith(mp3):
        return getMP3Rating(songPath)
    elif songPath.endswith(flac):
        return getFLACRating(song)
    return None

def getMP3Rating(songPath):
    id3 = ID3(songPath)
    popmKey = getFirstPOPMKey(id3.keys())
    if (popmKey):
        popm = id3.get(popmKey)
        rating = popm.rating / 51
        return rating
    return None

def getFLACRating(song):
    ratingList = song[1].get("rating")
    if (ratingList):
        rating = int(ratingList[0]) / 20.0
        return rating
    return None

def yearFilter(song, minimumYear):
    year = getYear(song)
    if (year):
        return year >= minimumYear 
    return False

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

def setupCopySongFunction(args):
    if (args.msc):
        return lambda srcFilePath, destFilePath : manageSongCopying(srcFilePath, destFilePath, copySongMSC)
    elif (args.adb):
        return lambda srcFilePath, destFilePath : manageSongCopying(srcFilePath, destFilePath, copySongADB)
    raise RuntimeError("Trasfer protocol not selected.")

def verifySourceDir(src):
    if not (os.path.isdir(src)):
        raise FileNotFoundError("The source directory isn't valid.")

def manageSongCopying(srcFilePath, destFilePath, copySongFunction):
    if (copySongFunction(srcFilePath, destFilePath)):
        addSongToCopiedSongs(srcFilePath)

def addSongToCopiedSongs(songPath):
    addSongToCopiedSongsFile(os.path.abspath(songPath))
    global copiedSongsCount
    copiedSongsCount += 1

def addSongToCopiedSongsFile(songPath):
    copiedSongsFile.write(songPath + '\n')

def copySongMSC(srcFilePath, destFilePath):
    if (os.path.isfile(destFilePath)):
        return False
    destDirPath = os.path.dirname(destFilePath)
    createDirectoryIfNecessaryMSC(destDirPath)
    shutil.copy2(srcFilePath, destDirPath)
    return True

def createDirectoryIfNecessaryMSC(dirPath):
    if not (os.path.isdir(dirPath)):
        os.makedirs(dirPath)

def copySongADB(srcFilePath, destFilePath):
    #TODO Check if file already exists
    destFilePath = convertWindowsPathToUnixPath(destFilePath)
    destDirPath = os.path.dirname(destFilePath)
    createDirectoryIfNecessaryADB(destDirPath)
    device.push(srcFilePath, destFilePath)
    return True

def convertWindowsPathToUnixPath(windowsPath):
    return windowsPath.replace("\\","/")

def createDirectoryIfNecessaryADB(dirPath):
    device.shell("mkdir -p $'{}'".format(dirPath.replace("'","\\'")))

def initAll(args):
    initInfoFiles()
    if (args.adb):
        connectADBDevice()

def initInfoFiles():
    global copiedSongsFile
    global songsNotInspectedFile
    copiedSongsFile = open("copiedSongs.txt", "a+", encoding="utf-8")
    songsNotInspectedFile = open("songsNotInspected.txt", "a+", encoding="utf-8")

def connectADBDevice():
    global device
    client = AdbClient()
    devices = client.devices()
    if (len(devices) < 1):
        raise RuntimeError("ADB device not detected.")
    firstDeviceSerialNumber = devices[0].get_serial_no()
    device = client.device(firstDeviceSerialNumber)

def syncSongs(src, dest, filters, copySongFunction):
    for root, _, files in os.walk(src):
        for file in files:
            if (isFileSupported(file)):
                songPathDest = os.path.join(dest, os.path.relpath(os.path.join(root, file), src))
                songPathSrc = os.path.join(root, file)
                if (checkFilters(songPathSrc, filters)):
                    copySongFunction(songPathSrc, songPathDest)

def isFileSupported(file):
    return file.lower().endswith(supportedFormats)

def checkFilters(songPath, filters):
    song = mutagen.File(songPath, easy=True)
    if (not song and len(filters) != 0):
        addSongToSongsNotInspected(songPath)
        return False
    for filter in filters:
        if (not filter((songPath, song))):
            return False
    return True

def addSongToSongsNotInspected(songPath):
    addSongToSongsNotInspectedFile(os.path.abspath(songPath))
    global songsNotInspectedCount
    songsNotInspectedCount += 1

def addSongToSongsNotInspectedFile(songPath):
    songsNotInspectedFile.write(songPath + '\n')

def getFirstPOPMKey(strList):
    for key in strList:
        if (key.startswith("POPM:")):
            return key
    return None

def closeAll(args):
    closeInfoFiles()

def closeInfoFiles():
    copiedSongsFile.close()
    songsNotInspectedFile.close()

def printSummary():
    print("Copied songs:", copiedSongsCount)
    print("Not inspected songs:", songsNotInspectedCount)

if (__name__ == "__main__"):
    main()
