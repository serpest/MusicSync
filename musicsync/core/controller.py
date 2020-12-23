import os
import sys
import logging
import mutagen

SUPPORTED_FORMATS = (".mp3", ".flac")

class Controller():
    def __init__(self, copy_song_function, filters):
        self.copy_song_function = copy_song_function
        self.filters = filters

    def sync(self):
        initAll(args)
        try:
            verify_source_dir(args.src)
            syncSongs(args.src, args.dest, self.filters, copy_song_function)
            return (copiedSongsCount, songsNotInspectedCount)
        except (FileNotFoundError, ConnectionError) as exc:
            logger.error(str(exc))
            raise MusicSyncError(str(exc))

def verifyADBDeviceConnection(stderrStr):
    if ((b"no devices/emulators found" in stderrStr) or (b"device unauthorized" in stderrStr)):
        raise ConnectionError("The device is not connected correctly.")

def manageSongCopying(srcSongPath, destSongPath, copyFileFunction):
    if (copyFileFunction(srcSongPath, destSongPath)):
        copyFileFunction(convertSongPathToLRCFilePath(srcSongPath), convertSongPathToLRCFilePath(destSongPath))
        addSongToCopiedSongs(srcSongPath)

def convertSongPathToLRCFilePath(songPath):
    #Same file name, different extension
    return os.path.splitext(songPath)[0] + ".lrc"

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
    initLog()
    initLogConsole()
    if (args.log):
        initLogFile()

def initLog():
    logName = "MusicSync"
    global logger
    logger = logging.getLogger(logName)
    logger.setLevel(logging.INFO)

def initLogConsole():
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)
    global logger
    logger.addHandler(consoleHandler)

def initLogFile():
    logFileName = "MusicSync.log"
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fileHandler = logging.FileHandler(logFileName, "a+", "utf-8")
    fileHandler.setFormatter(formatter)
    global logger
    logger.addHandler(fileHandler)

def verify_source_dir(src):
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

def printSummary():
    print("Copied songs:", copiedSongsCount)
    print("Not inspected songs:", songsNotInspectedCount)
