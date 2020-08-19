# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import copy
import functools
import os
import subprocess
import time
import traceback
from typing import Dict, List, Union

import psutil

import logger


class ProcessScanner:
    def __init__(self, log: logger.Log):
        self.log: logger.Log = log
        self.all_pids_cached: bool = False
        self.used_tasklist: bool = False
        self.parsed_tasklist: Dict[str, int] = {}
        self.executables: Dict[str, list] = {'posix': ['hl2_linux', 'steam', 'Discord'],
                                             'nt': ['hl2.exe', 'steam.exe', 'discord'],
                                             'order': ['TF2', 'Steam', 'Discord']}
        self.process_data: Dict[str, dict] = {'TF2': {'running': False, 'pid': None, 'path': None, 'time': None},
                                              'Steam': {'running': False, 'pid': None, 'path': None},
                                              'Discord': {'running': False, 'pid': None}}
        self.p_data_default: Dict[str, dict] = copy.deepcopy(self.process_data)
        self.p_data_last: Dict[str, dict] = copy.deepcopy(self.process_data)

    def __repr__(self):
        return f"processes.ProcessScanner (all cached={self.all_pids_cached}, tf2={self.process_data['TF2']}, discord={self.process_data['Discord']}, steam={self.process_data['Steam']})"

    # scan all running processes to look for TF2, Steam, and Discord
    def scan(self) -> Dict[str, Dict[str, Union[bool, str, int, None]]]:
        # TODO: use sys.platform everywhere instead of os.name (if possible)
        if os.name == 'nt':
            self.scan_windows()
        else:
            self.scan_posix()

        if self.process_data == self.p_data_last:
            self.log.debug(f"Process scanning got same results (used tasklist: {self.used_tasklist})")
        else:
            self.log.debug(f"Process scanning (used tasklist: {self.used_tasklist}) results: {self.process_data}")

        self.p_data_last = copy.deepcopy(self.process_data)
        return self.process_data

    # basically psutil.process_iter(attrs=['pid', 'cmdline', 'create_time']) but WAY faster (and also highly specialized)
    def scan_windows(self):
        self.used_tasklist = False

        if not self.all_pids_cached:  # guaranteed on the first run
            self.parse_tasklist()
            self.used_tasklist = True

            if len(self.parsed_tasklist) == 3:
                self.all_pids_cached = True

            self.process_data['TF2']['pid'] = self.parsed_tasklist['hl2.exe'] if 'hl2.exe' in self.parsed_tasklist else None
            self.process_data['Steam']['pid'] = self.parsed_tasklist['steam.exe'] if 'steam.exe' in self.parsed_tasklist else None
            self.process_data['Discord']['pid'] = self.parsed_tasklist['discord'] if 'discord' in self.parsed_tasklist else None

            self.get_all_extended_info()
        else:
            # all the PIDs are known, so don't use tasklist, saves 0.2 - 0.3 seconds :)
            self.get_all_extended_info()

            p_data_old: Dict[str] = copy.deepcopy(self.process_data)

            if not self.process_data['TF2']['running']:
                self.process_data['TF2'] = self.p_data_default['TF2']
            if not self.process_data['Steam']['running']:
                self.process_data['Steam'] = self.p_data_default['Steam']
            if not self.process_data['Discord']['running']:
                self.process_data['Discord'] = self.p_data_default['Discord']

            if self.process_data != p_data_old:
                self.all_pids_cached = False

    # for Linux and MacOS (I think)
    def scan_posix(self):
        for proc in psutil.process_iter():
            try:
                details = proc.as_dict(attrs=['pid', 'name', 'cwd'])
                for pos, name in enumerate(self.executables[os.name]):
                    if self.process_data[self.executables['order'][pos]]['pid'] is not None:
                        continue

                    if name == details['name']:
                        self.process_data[self.executables['order'][pos]]['pid'] = details['pid']
            except psutil.NoSuchProcess:
                pass

        self.get_all_extended_info()

    # get only the needed info (exe path and process start time) for each, and then apply it to self.p_data
    def get_all_extended_info(self):
        tf2_data: Dict[str, Union[str, bool, int, None]] = self.get_info_from_pid(self.process_data['TF2']['pid'], ('path', 'time'))
        steam_data: Dict[str, Union[str, bool, int, None]] = self.get_info_from_pid(self.process_data['Steam']['pid'], ('path', 'cwd'))
        discord_data: Dict[str, Union[str, bool, int, None]] = self.get_info_from_pid(self.process_data['Discord']['pid'], ())

        # ugly
        self.process_data['TF2']['running'], self.process_data['TF2']['path'], self.process_data['TF2']['time'] = tf2_data['running'], tf2_data['path'], tf2_data['time']
        self.process_data['Steam']['running'], self.process_data['Steam']['path'] = steam_data['running'], steam_data['path']
        self.process_data['Discord']['running'] = discord_data['running']

    # a mess of logic that gives process info from a PID
    def get_info_from_pid(self, pid: int, return_data: tuple) -> Dict[str, Union[str, bool, int, None]]:
        p_info: Dict[str, Union[str, bool, None, int]] = {'running': False, 'path': None, 'time': None}
        p_info_nones: Dict[str, Union[str, bool, None, int]] = {'running': False, 'path': None, 'time': None}

        if pid is None:
            return p_info

        try:
            try:
                process: psutil.Process = psutil.Process(pid=pid)
                p_info['running'] = [name for name in self.executables[os.name] if name in process.name().lower()] != []

                if not p_info['running']:
                    self.log.error(f"PID {pid} has been recycled as {process.name()}")
                    return p_info_nones

                if 'path' in return_data:
                    if os.name == 'posix':
                        if 'cwd' in return_data:
                            p_info['path'] = os.path.dirname(process.cwd()) + '/Steam'
                        else:
                            p_info['path'] = os.path.dirname(process.cmdline()[0])
                    else:
                        p_info['path'] = os.path.dirname(process.cmdline()[0])

                    if not p_info['path']:
                        return p_info_nones

                if 'time' in return_data:
                    p_info['time'] = int(process.create_time())

                    if not p_info['time']:
                        return p_info_nones

                return p_info
            except psutil.NoSuchProcess:
                self.log.debug(f"Cached PID {pid} is no longer running")
                return p_info_nones
        except Exception:
            formatted_exception: str = traceback.format_exc()

            try:
                self.log.error(f"psutil error for {process}: {formatted_exception}")
            except NameError:
                self.log.error(f"psutil error: {formatted_exception}")

            return p_info_nones

    # https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/tasklist
    def parse_tasklist(self):
        try:
            processes: List[str] = str(subprocess.check_output('tasklist /fi "STATUS eq running" /fi "MEMUSAGE gt 10000" /nh')).split(r'\r\n')
        except subprocess.CalledProcessError as error:
            self.log.error(f"tasklist failed: CalledProcessError ({error})")
            processes = []
        except OSError as error:
            if "Insufficient system resources" in str(error):
                self.log.error(f"tasklist failed: {error}")
                processes = []
            else:
                raise

        self.parsed_tasklist = {}

        process_line: str
        ref_name: str
        for process_line in processes:
            process: list = process_line.split()

            for ref_name in ('hl2.exe', 'Steam.exe', 'steam.exe', 'Discord'):
                if ref_name in process[0]:
                    self.parsed_tasklist[ref_name.lower()] = int(process[1])

        self.process_data['TF2']['running'] = 'hl2.exe' in self.parsed_tasklist
        self.process_data['Steam']['running'] = 'steam.exe' in self.parsed_tasklist
        self.process_data['Discord']['running'] = 'discord' in self.parsed_tasklist

        # don't detect gmod (or any other program named hl2.exe)
        if self.process_data['TF2']['running']:
            if not self.hl2_exe_is_tf2(self.parsed_tasklist['hl2.exe']):
                self.process_data['TF2'] = copy.deepcopy(self.p_data_default['TF2'])
                del self.parsed_tasklist['hl2.exe']

    # makes sure a process's path is a TF2 install, not some other game
    @functools.lru_cache(maxsize=None)
    def hl2_exe_is_tf2(self, hl2_exe_pid: int) -> bool:
        hl2_exe_path: str = self.get_info_from_pid(hl2_exe_pid, ('path',))['path']
        is_tf2: bool = False

        if 'Team Fortress 2' in hl2_exe_path:
            appid_path: str = os.path.join(hl2_exe_path, 'steam_appid.txt')

            if os.path.isfile(appid_path):
                with open(appid_path, 'rb') as appid_file:
                    appid_read: bytes = appid_file.read()

                    if appid_read.startswith(b'440\n'):
                        is_tf2 = True
                    else:
                        self.log.debug(f"steam_appid.txt contains \"{appid_read}\" ")
            else:
                self.log.debug(f"steam_appid.txt doesn't exist (install folder: {os.listdir(hl2_exe_path)})")

        if is_tf2:
            self.log.debug(f"Found TF2 hl2.exe at {hl2_exe_path}")
            return True
        else:
            self.log.error(f"Found non-TF2 hl2.exe at {hl2_exe_path}")
            return False


if __name__ == '__main__':
    import pprint

    test_log = logger.Log()
    test_log.to_stderr = True
    test_process_scanner = ProcessScanner(test_log)

    while True:
        scan_results = test_process_scanner.scan()
        time.sleep(0.1)  # to wait for the log
        pprint.pprint(scan_results)
        time.sleep(2)
        print()
