# Copyright (C) 2018-2025 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import copy
import functools
import os
import subprocess
import time
import traceback
from typing import Dict, List, Tuple, Union

import psutil

import configs
import logger


class ProcessScanner:
    def __init__(self, log: logger.Log):
        self.log: logger.Log = log
        self.all_pids_cached: bool = False
        self.used_tasklist: bool = False
        self.tf2_without_condebug: bool = False
        self.parsed_tasklist: Dict[str, int] = {}
        self.executables: Dict[str, list] = {'posix': ['hl2_linux', 'steam', 'Discord'],
                                             'nt': ['tf_win64.exe', 'steam.exe', 'discord'],
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

            if not self.process_data['TF2']['running']:
                self.tf2_without_condebug = False

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

            self.process_data['TF2']['pid'] = self.parsed_tasklist['tf_win64.exe'] if 'tf_win64.exe' in self.parsed_tasklist else None
            self.process_data['Steam']['pid'] = self.parsed_tasklist['steam.exe'] if 'steam.exe' in self.parsed_tasklist else None
            self.process_data['Discord']['pid'] = self.parsed_tasklist['discord'] if 'discord' in self.parsed_tasklist else None

            self.get_all_extended_info()
        else:
            # all the PIDs are known, so don't use tasklist, saves 0.2 - 0.3 seconds :)
            self.get_all_extended_info()

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
        tf2_data: Dict[str, Union[str, bool, int, None]] = self.get_process_info('TF2', ('path', 'time'), True)
        steam_data: Dict[str, Union[str, bool, int, None]] = self.get_process_info('Steam', ('path', 'cwd'))
        discord_data: Dict[str, Union[str, bool, int, None]] = self.get_process_info('Discord', ())

        # ugly
        self.process_data['TF2']['running'], self.process_data['TF2']['path'], self.process_data['TF2']['time'] = tf2_data['running'], tf2_data['path'], tf2_data['time']
        self.process_data['Steam']['running'], self.process_data['Steam']['path'] = steam_data['running'], steam_data['path']
        self.process_data['Discord']['running'] = discord_data['running']

        if not self.process_data['TF2']['running']:
            self.process_data['TF2'] = copy.deepcopy(self.p_data_default['TF2'])
        if not self.process_data['Steam']['running']:
            self.process_data['Steam'] = copy.deepcopy(self.p_data_default['Steam'])
        if not self.process_data['Discord']['running']:
            self.process_data['Discord'] = copy.deepcopy(self.p_data_default['Discord'])

    # a mess of logic that gives process info from a process name (not exe name) or PID
    def get_process_info(self, process: Union[str, int], return_data: Tuple[str, ...], validate_condebug: bool = False) -> Dict[str, Union[str, bool, int, None]]:
        p_info: Dict[str, Union[str, bool, None, int]] = {'running': False, 'path': None, 'time': None}
        p_info_nones: Dict[str, Union[str, bool, None, int]] = {'running': False, 'path': None, 'time': None}

        if isinstance(process, str):
            pid: int = self.process_data[process]['pid']

            if pid is None:
                self.all_pids_cached = False
                return p_info
        else:
            pid = process

        try:
            process: psutil.Process = psutil.Process(pid=pid)
            running: bool = [name for name in self.executables[os.name] if name in process.name().lower()] != []
            p_info['running'] = running

            if not running:
                self.log.error(f"PID {pid} ({process}) has been recycled as {process.name()}")
                self.all_pids_cached = False
                return p_info_nones

            if 'path' in return_data:
                if os.name == 'posix':
                    if 'cwd' in return_data:
                        p_info['path'] = os.path.dirname(process.cwd()) + '/Steam'
                    else:
                        cmdline: List[str] = process.cmdline()
                        p_info['path'] = os.path.dirname(cmdline[0])
                else:
                    cmdline = process.cmdline()
                    p_info['path'] = os.path.dirname(cmdline[0])

                if validate_condebug and '-condebug' not in cmdline:
                    self.log.debug(f"TF2 is running without -condebug in cmdline: {cmdline}")
                    self.tf2_without_condebug = True

                if not p_info['path']:
                    self.all_pids_cached = False
                    return p_info_nones

            if 'time' in return_data:
                p_info['time'] = int(process.create_time())  # int instead of round to prevent future times

                if not p_info['time']:
                    self.all_pids_cached = False
                    return p_info_nones

            return p_info
        except psutil.NoSuchProcess:
            self.log.debug(f"Cached PID {pid} ({process}) is no longer running")
            self.all_pids_cached = False
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
            processes_command = subprocess.check_output('tasklist /fi "STATUS eq running" /fi "MEMUSAGE gt 10000" /nh', creationflags=0x08000000)
            processes: List[str] = str(processes_command).split(r'\r\n')
        except OSError as error:
            if "Insufficient system resources" in str(error):
                self.log.error(f"tasklist failed: {error}")
                processes = []
            else:
                raise
        except Exception as error:
            self.log.error(f"tasklist failed: {repr(error)}")
            processes = []

        self.parsed_tasklist = {}

        process_line: str
        ref_name: str
        for process_line in processes:
            process: list = process_line.split()

            for ref_name in ('tf_win64.exe', 'Steam.exe', 'steam.exe', 'Discord'):
                if ref_name in process[0]:
                    try:
                        self.parsed_tasklist[ref_name.lower()] = int(process[1])
                    except ValueError:
                        self.log.error(f"Couldn't parse PID from process {process}")

        self.process_data['TF2']['running'] = 'tf_win64.exe' in self.parsed_tasklist
        self.process_data['Steam']['running'] = 'steam.exe' in self.parsed_tasklist
        self.process_data['Discord']['running'] = 'discord' in self.parsed_tasklist

        # don't detect gmod (or any other program named tf_win64.exe)
        if self.process_data['TF2']['running']:
            if not self.hl2_exe_is_tf2(self.parsed_tasklist['tf_win64.exe']):
                self.log.debug(f"Found running non-TF2 tf_win64.exe with PID {self.parsed_tasklist['tf.exe']}")
                self.process_data['TF2'] = copy.deepcopy(self.p_data_default['TF2'])
                del self.parsed_tasklist['tf.exe']

    # makes sure a process's path is a TF2 install, not some other game
    @functools.cache
    def hl2_exe_is_tf2(self, hl2_exe_pid: int) -> bool:
        hl2_exe_dir: str = self.get_process_info(hl2_exe_pid, ('path',))['path']
        return configs.is_tf2_install(self.log, os.path.join(hl2_exe_dir, 'tf_win64.exe'))


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
