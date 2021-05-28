import os
import shutil
import tempfile
import subprocess
import abc

def get_copy_file_function(src_file_path):
    return lambda dest_dir_path : shutil.copy2(src_file_path, dest_dir_path)


class FileCopier():
    @abc.abstractmethod
    def copy(self, copy_file_function, dest_file_path):
        pass


class MSCFileCopier():
    def copy(self, copy_file_function, dest_file_path):
        if os.path.isfile(dest_file_path):
            return False
        dest_dir_path = os.path.dirname(dest_file_path)
        self._create_directory_if_necessary(dest_dir_path)
        copy_file_function(dest_file_path)
        return True

    def _create_directory_if_necessary(self, dir_path):
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)


class ADBFileCopier():
    def __init__(self):
        self._connect_adb_server()

    def __del__(self):
        self._disconnect_adb_server()

    def copy(self, copy_file_function, dest_file_path):
        if os.name == "nt":
            dest_file_path = self._convert_windows_path_to_unix_path(dest_file_path)
        if self._adb_does_path_exist(dest_file_path):
            return False
        dest_dir_path = os.path.dirname(dest_file_path)
        self._create_directory_if_necessary(dest_dir_path)
        with tempfile.NamedTemporaryFile() as temporary_file:
            copy_file_function(temporary_file.name) 
            self._push_file(temporary_file.name, dest_file_path)
        return True

    def _convert_windows_path_to_unix_path(self, windows_path):
        return windows_path.replace("\\","/")

    def _connect_adb_server(self):
        subprocess.run(["adb", "start-server"])

    def _disconnect_adb_server(self):
        subprocess.run(["adb", "kill-server"])

    def _adb_does_path_exist(self, path):
        return _get_subprocess_call_stdout_size(["adb", "shell", "find", "${}".format(_convert_string_to_literal(path))]) != 0

    def _convert_string_to_literal(self, string):
        return "'{}'".format(string.replace("'","\\'"))

    def _get_subprocess_call_stdout_size(self, args):
        popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_str, stderr_str = popen.communicate()
        _verify_device_connection(stderr_str)
        return len(stdout_str)

    def _create_directory_if_necessary(self, dir_path):
        subprocess.run(["adb", "shell", "mkdir", "-p", "${}".format(_convert_string_to_literal(dir_path))])

    def _push_file(self, src_file_path, dest_file_path):
        subprocess.run(["adb", "push", src_file_path, dest_file_path])

    def _verify_device_connection(self, stderr_str):
        if ((b"no devices/emulators found" in stderr_str) or (b"device unauthorized" in stderr_str)):
            raise FileCopierError("The device is not connected correctly.")


class FileCopierError(RuntimeError):
    pass
