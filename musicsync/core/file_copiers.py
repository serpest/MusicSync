import os
import shutil
import subprocess

class FileCopier():
    @abstractmethod
    def copy(self, src_file_path, dest_file_path):
        pass


class MSCFileCopier():
    def copy(self, src_file_path, dest_file_path):
        if ((not os.path.isfile(src_file_path)) or os.path.isfile(dest_file_path)):
            return False
        dest_dir_path = os.path.dirname(dest_file_path)
        self._msc_create_directory_if_necessary(dest_dir_path)
        shutil.copy2(src_file_path, dest_dir_path)
        return True

    def _create_directory_if_necessary(self, dir_path):
        if not (os.path.isdir(dir_path)):
            os.makedirs(dir_path)


class ADBFileCopier():
    def __init__(self):
        self._connectADBServer()

    def copy(self, src_file_path, dest_file_path):
        if (os.name == "nt"):
            dest_file_path = _convert_windows_path_to_unix_path(dest_file_path)
        if ((not os.path.isfile(src_file_path)) or _adb_does_path_exist(dest_file_path)):
            return False
        dest_dir_path = os.path.dirname(dest_file_path)
        createDirectoryIfNecessaryADB(dest_dir_path)
        pushSongADB(src_file_path, dest_file_path)
        return True
    
    def __del__(self):
        self._disconnectADBServer()

    def _connectADBServer(self):
        getSubprocessCallStdoutSize(["adb", "start-server"])

    def _disconnectADBServer(self):
        getSubprocessCallStdoutSize(["adb", "kill-server"])

    def _adb_does_path_exist(path):
        return (getSubprocessCallStdoutSize(["adb", "shell", "find", "${}".format(convert_string_to_Literal(path))]) != 0)

    def getSubprocessCallStdoutSize(args):
        popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutStr, stderrStr = popen.communicate()
        verifyADBDeviceConnection(stderrStr)
        return len(stdoutStr)

    def createDirectoryIfNecessaryADB(dirPath):
        getSubprocessCallStdoutSize(["adb", "shell", "mkdir", "-p", "${}".format(convert_string_to_Literal(dirPath))])

    def pushSongADB(srcFilePath, destFilePath):
        getSubprocessCallStdoutSize(["adb", "push", "{}".format(srcFilePath), "{}".format(destFilePath)])

    def convert_string_to_Literal(string):
        return "'{}'".format(string.replace("'","\\'"))
    
    def _convert_windows_path_to_unix_path(windowsPath):
        return windowsPath.replace("\\","/")
