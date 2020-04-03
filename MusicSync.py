import argparse
import os
import sys
import shutil
import subprocess
import logging
import mutagen
from mutagen.id3 import ID3

supportedFormats = (".mp3", ".flac") #If you add new formats you can see easily the functions to modify



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

def verifyArgsValidity(args):
    if (args.minimumRating):
        verifyRatingValidity(args)

def verifyRatingValidity(args):
    if (not isRatingValid(args.minimumRating)):
        raise ValueError("The minimum stars rating value must be between 0 and 5.")

def isRatingValid(rating):
    return (rating >= 0 and rating <= 5)

def startCopy(args):
    filters = setupFilters(args)
    copySongFunction = setupCopySongFunction(args)
    initAll(args)
    try:
        verifySourceDir(args.src)
        syncSongs(args.src, args.dest, filters, copySongFunction)
        return (copiedSongsCount, songsNotInspectedCount)
    except (FileNotFoundError, ConnectionError) as exc:
        logger.error(str(exc))
        raise MusicSyncError(str(exc))
    finally:
        closeAll(args)

def setupFilters(args):
    filters = []
    if (args.minimumRating):
        filters.append(setupMinimumRatingFilter(args))
    if (args.minimumYear):
        filters.append(setupMinimumYearFilter(args))
    return filters

def setupMinimumRatingFilter(args):
    return lambda file : ratingFilter(file, args.minimumRating)

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

def getFirstPOPMKey(strList):
    for key in strList:
        if (key.startswith("POPM:")):
            return key
    return None

def getFLACRating(song):
    ratingList = song[1].get("rating")
    if (ratingList):
        rating = int(ratingList[0]) / 20.0
        return rating
    return None

def setupMinimumYearFilter(args):
    return lambda file : yearFilter(file, args.minimumYear)

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
    copySongFunction = None
    if (args.msc):
        copySongFunction = copySongMSC
    elif (args.adb):
        copySongFunction = copySongADB
    assert copySongFunction != None, "Trasfer protocol not selected."
    return lambda srcFilePath, destFilePath : manageSongCopying(srcFilePath, destFilePath, copySongFunction)

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
    if (os.name == "nt"):
        destFilePath = os.path.normpath(destFilePath)
    if (doesPathExistADB(destFilePath)):
        return False
    destDirPath = os.path.dirname(destFilePath)
    createDirectoryIfNecessaryADB(destDirPath)
    pushSongADB(srcFilePath, destFilePath)
    return True

def doesPathExistADB(path):
    return (getSubprocessCallStdoutSize(["adb", "shell", "find", "${}".format(convertStringToLiteral(path))]) != 0)

def convertStringToLiteral(string):
    return "'{}'".format(string.replace("'","\\'"))

def getSubprocessCallStdoutSize(args):
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdoutStr, stderrStr = popen.communicate()
    verifyADBDeviceConnection(stderrStr)
    return len(stdoutStr)

def verifyADBDeviceConnection(stderrStr):
    if ((b"no devices/emulators found" in stderrStr) or (b"device unauthorized" in stderrStr)):
        raise ConnectionError("The device is not connected correctly.")

def createDirectoryIfNecessaryADB(dirPath):
    getSubprocessCallStdoutSize(["adb", "shell", "mkdir", "-p", "${}".format(convertStringToLiteral(dirPath))])

def pushSongADB(srcFilePath, destFilePath):
    getSubprocessCallStdoutSize(["adb", "push", "{}".format(srcFilePath), "{}".format(destFilePath)])

def manageSongCopying(srcFilePath, destFilePath, copySongFunction):
    if (copySongFunction(srcFilePath, destFilePath)):
        addSongToCopiedSongs(srcFilePath)

def addSongToCopiedSongs(songPath):
    addCopiedSongToLog(os.path.abspath(songPath))
    global copiedSongsCount
    copiedSongsCount += 1

def addCopiedSongToLog(songPath):
    logger.info("{} copied.".format(songPath))

def initAll(args):
    global copiedSongsCount
    copiedSongsCount = 0
    global songsNotInspectedCount
    songsNotInspectedCount = 0
    initLogFile()
    if (args.adb):
        connectADBDevice()

def initLogFile():
    logName = "MusicSync"
    logFileName = logName + ".log"
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fileHandler = logging.FileHandler(logFileName, "a+", "utf-8")
    fileHandler.setFormatter(formatter)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)
    global logger
    logger = logging.getLogger(logName)
    logger.setLevel(logging.INFO)
    logger.addHandler(fileHandler)
    logger.addHandler(consoleHandler)

def connectADBDevice():
    connectADBServer()

def connectADBServer():
    getSubprocessCallStdoutSize(["adb", "start-server"])

def verifySourceDir(src):
    if not (os.path.isdir(src)):
        raise FileNotFoundError("The source directory isn't valid.")

def syncSongs(src, dest, filters, copySongFunction):
    for root, _, files in os.walk(src):
        for file in files:
            if (isFileSupported(file)):
                songPathSrc = os.path.join(root, file)
                songPathDest = os.path.join(dest, os.path.relpath(songPathSrc, src))
                if (len(filters) == 0 or checkFilters(songPathSrc, filters)):
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
    addSongNotInspectedToLog(os.path.abspath(songPath))
    global songsNotInspectedCount
    songsNotInspectedCount += 1

def addSongNotInspectedToLog(songPath):
    logger.warning("{} not inspected.".format(songPath))

class MusicSyncError(RuntimeError):
    def __init__(self, message):
        super().__init__(message)

def closeAll(args):
    if (args.adb):
        disconnectADBServer()

def disconnectADBServer():
    getSubprocessCallStdoutSize(["adb", "kill-server"])

def printSummary():
    print("Copied songs:", copiedSongsCount)
    print("Not inspected songs:", songsNotInspectedCount)

if (__name__ == "__main__"):
    parser = setupParser()
    args = parser.parse_args()
    try:
        verifyArgsValidity(args)
    except ValueError as exc:
        parser.error(str(exc))
        sys.exit(1)
    try:
        startCopy(args)
        printSummary()
    except MusicSyncError as exc:
        sys.exit(2)