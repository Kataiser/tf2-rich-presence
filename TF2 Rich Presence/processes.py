# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import copy
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
        self.has_cached_all_pids: bool = False
        self.used_tasklist: bool = False
        self.parsed_tasklist: dict = {}
        self.executables: Dict[str] = {'posix': ['hl2_linux', 'steam', 'Discord'],
                                       'nt': ['hl2.exe', 'Steam.exe', 'Discord'],
                                       'order': ['TF2', 'Steam', 'Discord']}
        self.process_data: Dict[str] = {'TF2': {'running': False, 'pid': None, 'path': None, 'time': None},
                                        'Steam': {'running': False, 'pid': None, 'path': None},
                                        'Discord': {'running': False, 'pid': None}}
        self.p_data_default: Dict[str] = copy.deepcopy(self.process_data)
        self.p_data_last: Dict[str] = copy.deepcopy(self.process_data)

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

        if not self.has_cached_all_pids:  # guaranteed on the first run
            self.parse_tasklist()
            self.used_tasklist = True

            if len(self.parsed_tasklist) == 3:
                self.has_cached_all_pids = True

            if 'hl2.exe' in self.parsed_tasklist:
                self.process_data['TF2']['pid'] = self.parsed_tasklist['hl2.exe']
            if 'Steam.exe' in self.parsed_tasklist:
                self.process_data['Steam']['pid'] = self.parsed_tasklist['Steam.exe']
            if 'Discord' in self.parsed_tasklist:
                self.process_data['Discord']['pid'] = self.parsed_tasklist['Discord']

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
                self.has_cached_all_pids = False

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
        tf2_data: Dict[str] = self.get_info_from_pid(self.process_data['TF2']['pid'], ('path', 'time'))
        steam_data: Dict[str] = self.get_info_from_pid(self.process_data['Steam']['pid'], ('path', 'cwd'))
        discord_data: Dict[str] = self.get_info_from_pid(self.process_data['Discord']['pid'], ())

        # ugly
        self.process_data['TF2']['running'], self.process_data['TF2']['path'], self.process_data['TF2']['time'] = tf2_data['running'], tf2_data['path'], tf2_data['time']
        self.process_data['Steam']['running'], self.process_data['Steam']['path'] = steam_data['running'], steam_data['path']
        self.process_data['Discord']['running'] = discord_data['running']

    # a mess of logic that gives process info from a PID
    def get_info_from_pid(self, pid: int, return_data: tuple = ('path', 'time')) -> Dict[str]:
        p_info: Dict[str] = {'running': False, 'path': None, 'time': None}
        p_info_nones: Dict[str] = {'running': False, 'path': None, 'time': None}

        if pid is None:
            return p_info

        try:
            try:
                process: psutil.Process = psutil.Process(pid=pid)
            except psutil.NoSuchProcess:
                self.log.debug(f"Cached PID {pid} is no longer running")
            else:
                p_info['running'] = [name for name in self.executables[os.name] if name in process.name()] != []

                if not p_info['running']:
                    self.log.error(f"PID {pid} has been recycled as {process.name()}")

                if 'path' in return_data:
                    if os.name == "posix":
                        if 'cwd' in return_data:
                            p_info['path'] = os.path.dirname(process.cwd()) + "/Steam"
                        else:
                            p_info['path'] = os.path.dirname(process.cmdline()[0])
                    else:
                        p_info['path'] = os.path.dirname(process.cmdline()[0])
                if 'time' in return_data:
                    p_info['time'] = int(process.create_time())
        except Exception:
            try:
                self.log.error(f"psutil error for {process}: {traceback.format_exc()}")
            except Exception:
                self.log.error(f"psutil error: {traceback.format_exc()}")

            return p_info_nones

        return p_info

    # https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/tasklist
    def parse_tasklist(self):
        try:
            processes: List[str] = str(subprocess.check_output('tasklist /fi "STATUS eq running"')).split(r'\r\n')
        except subprocess.CalledProcessError:
            processes: List[str] = []

        self.parsed_tasklist: dict = {}

        process_line: str
        ref_name: str
        for process_line in processes:
            process: list = process_line.split()

            for ref_name in ('hl2.exe', 'Steam.exe', 'Discord'):
                if ref_name in process[0]:
                    self.parsed_tasklist[ref_name] = int(process[1])

        parsed_tasklist_keys = self.parsed_tasklist.keys()
        self.process_data['TF2']['running'] = 'hl2.exe' in parsed_tasklist_keys
        self.process_data['Steam']['running'] = 'Steam.exe' in parsed_tasklist_keys
        self.process_data['Discord']['running'] = 'Discord' in parsed_tasklist_keys

        # don't detect gmod (or any other program named hl2.exe)
        if self.process_data['TF2']['running']:
            hl2_exe_path: str = self.get_info_from_pid(self.parsed_tasklist['hl2.exe'], ('path',))['path']

            if 'Team Fortress 2' not in hl2_exe_path:
                self.log.error(f"Found non-TF2 hl2.exe at {hl2_exe_path}")
                self.process_data['TF2'] = copy.deepcopy(self.p_data_default['TF2'])
                del self.parsed_tasklist['hl2.exe']


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
