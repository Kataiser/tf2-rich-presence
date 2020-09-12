# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import os
from typing import Dict, List, Set, Tuple, Union

from colorama import Fore, Style

import localization
import settings


# reads a console.log and returns current map and class
def interpret(self, console_log_path: str, user_usernames: Set[str], kb_limit: float = float(settings.get('console_scan_kb')), force: bool = False,
              tf2_start_time: int = 0) -> Tuple[str, str]:
    TF2_LOAD_TIME_ASSUMPTION: int = 10
    SIZE_LIMIT_MULTIPLE_TRIGGER: int = 4
    SIZE_LIMIT_MULTIPLE_TARGET: int = 2
    SIZE_LIMIT_MIN_LINES: int = 15000

    # defaults
    current_map: str = 'In menus'
    current_class: str = 'Not queued'
    kataiser_seen_on: Union[str, None] = None

    match_types: Dict[str, str] = {'12v12 Casual Match': 'Casual', 'MvM Practice': 'MvM (Boot Camp)', 'MvM MannUp': 'MvM (Mann Up)', '6v6 Ladder Match': 'Competitive'}
    menus_messages: tuple = ('Lobby destroyed', 'For FCVAR_REPLICATED', '[TF Workshop]', 'Disconnecting from abandoned', 'Server shutting down', 'destroyed Lobby', 'Disconnect:',
                             'destroyed CAsyncWavDataCache', 'Connection failed after', 'Missing map', 'Host_Error')
    menus_message: str

    hide_queued_gamemode: bool = settings.get('hide_queued_gamemode')
    user_is_kataiser: bool = 'Kataiser' in user_usernames

    # console.log is a log of tf2's console (duh), only exists if tf2 has -condebug (see no_condebug_warning())
    self.log.debug(f"Looking for console.log at {console_log_path}")
    self.log.console_log_path = console_log_path

    if not os.path.isfile(console_log_path):
        self.log.error(f"console.log doesn't exist, issuing warning (files/dirs in /tf/: {os.listdir(os.path.dirname(console_log_path))})", reportable=False)
        del self.log
        no_condebug_warning(self.loc, tf2_is_running=True)

    # only interpret console.log again if it's been modified
    self.console_log_mtime = int(os.stat(console_log_path).st_mtime)
    if not force and self.console_log_mtime == self.old_console_log_mtime:
        self.log.debug(f"Not rescanning console.log, remaining on {self.old_console_log_interpretation}")
        return self.old_console_log_interpretation

    # TF2 takes some time to load the console when starting up, so wait until it's been modified to avoid getting outdated information
    console_log_mtime_relative: int = self.console_log_mtime - tf2_start_time
    if console_log_mtime_relative <= TF2_LOAD_TIME_ASSUMPTION:
        self.log.debug(f"console.log's mtime relative to TF2's start time is {console_log_mtime_relative} (<= {TF2_LOAD_TIME_ASSUMPTION}), assuming default state")
        return current_map, current_class

    consolelog_file_size: int = os.stat(console_log_path).st_size
    byte_limit: float = kb_limit * 1024.0

    with open(console_log_path, 'r', errors='replace') as consolelog_file:
        if consolelog_file_size > byte_limit:
            skip_to_byte: int = consolelog_file_size - int(byte_limit)
            consolelog_file.seek(skip_to_byte, 0)  # skip to last few KBs

            lines: List[str] = consolelog_file.readlines()
            self.log.debug(f"console.log: {consolelog_file_size} bytes, skipped to {skip_to_byte}, read {int(byte_limit)} bytes and {len(lines)} lines")
        else:
            lines = consolelog_file.readlines()
            self.log.debug(f"console.log: {consolelog_file_size} bytes, {len(lines)} lines (didn't skip lines)")

    # limit the file size, for better readlines performance
    if consolelog_file_size > byte_limit * SIZE_LIMIT_MULTIPLE_TRIGGER and len(lines) > SIZE_LIMIT_MIN_LINES and settings.get('trim_console_log') and not force:
        trim_size = int(byte_limit * SIZE_LIMIT_MULTIPLE_TARGET)
        self.log.debug(f"Limiting console.log to {trim_size} bytes")

        try:
            with open(console_log_path, 'rb+') as consolelog_file_b:
                # this can probably be done faster and/or cleaner
                consolelog_file_b.seek(-trim_size, 2)
                consolelog_file_trimmed: bytes = consolelog_file_b.read()
                trimmed_line_count: int = consolelog_file_trimmed.count(b'\n')

                if trimmed_line_count > SIZE_LIMIT_MIN_LINES:
                    consolelog_file_b.seek(0)
                    consolelog_file_b.truncate()
                    consolelog_file_b.write(consolelog_file_trimmed)
                else:
                    self.log.error(f"Trimmed line count will be {trimmed_line_count} (< {SIZE_LIMIT_MIN_LINES}), aborting (trim len = {len(consolelog_file_trimmed)})")
        except PermissionError as error:
            self.log.error(f"Failed to trim console.log: {error}")

    just_started_server: bool = False
    server_still_running: bool = False
    with_optimization: bool = True  # "with" optimization, not "with optimization"

    for username in user_usernames:
        if 'with' in username:
            with_optimization = False

    map_line_used: str = ''
    class_line_used: str = ''
    last_class: str = ''
    line: str

    # iterates though roughly 16000 lines from console.log and learns everything from them
    for line in lines:
        # lines that have "with" in them are basically always kill logs and can be safely ignored
        # this (probably) improves performance
        if with_optimization and 'with' in line:
            if user_is_kataiser or 'Kataiser' not in line or self.has_seen_kataiser:
                continue

        if current_map != 'In menus':
            found_in_menus: bool = False

            for menus_message in menus_messages:
                if menus_message in line:
                    found_in_menus = True
                    current_map = 'In menus'
                    current_class = 'Not queued'
                    map_line_used = class_line_used = line
                    break

            # ok this is jank but it's to only trigger on actually closing the map and not just (I think) ending a demo recording
            if not found_in_menus and 'SoundEmitter:' in line:
                if int(line.split('[')[1].split()[0]) > 1000:
                    current_map = 'In menus'
                    current_class = 'Not queued'
                    map_line_used = class_line_used = line

        if line.endswith(' selected \n'):
            current_class_possibly: str = line[:-11]

            if current_class_possibly in tf2_classes:
                current_class = current_class_possibly
                last_class = current_class
                class_line_used = line

        elif line.startswith('Map:'):
            current_map = line[5:-1]  # this variable is poorly named
            current_class = 'unselected'  # so is this one
            map_line_used = class_line_used = line

            if just_started_server:
                server_still_running = True
                just_started_server = False
            else:
                just_started_server = False
                server_still_running = False

        elif '[PartyClient] L' in line:  # full line: "[PartyClient] Leaving queue"
            # queueing is not necessarily only in menus
            class_line_used = line
            current_class = 'Not queued' if current_map == 'In menus' else last_class

        elif '[PartyClient] Entering q' in line:  # full line: "[PartyClient] Entering queue for match group " + whatever mode
            class_line_used = line

            if hide_queued_gamemode:
                current_class = "Queued"
            else:
                match_type: str = line.split('match group ')[-1][:-1]
                current_class = f"Queued for {match_types[match_type]}"

        elif '[PartyClient] Entering s' in line:  # full line: "[PartyClient] Entering standby queue"
            current_class = 'Queued for a party\'s match'
            class_line_used = line

        elif 'Disconnect by user' in line:
            for user_username in user_usernames:
                if user_username in line:
                    current_map = 'In menus'
                    current_class = 'Not queued'
                    map_line_used = class_line_used = line
                    break

        elif 'SV_ActivateServer' in line:  # full line: "SV_ActivateServer: setting tickrate to 66.7"
            just_started_server = True

        if not user_is_kataiser and 'Kataiser' in line and not self.has_seen_kataiser:
            kataiser_seen_on = current_map

    if not user_is_kataiser and not self.has_seen_kataiser and kataiser_seen_on == current_map and current_map != 'In menus':
        self.has_seen_kataiser = True
        self.log.debug(f"Kataiser located, telling user :D (on {current_map})")
        print(f"{Fore.LIGHTCYAN_EX}Hey, it seems that Kataiser, the developer of TF2 Rich Presence, is in your game! Say hi to me if you'd like :){Style.RESET_ALL}\n")

    if server_still_running and current_map != 'In menus':
        current_map = f'{current_map} (hosting)'

    if map_line_used == class_line_used:
        self.log.debug(f"Got '{current_map}' and '{current_class}' from line '{map_line_used[:-1]}'")
    else:
        self.log.debug(f"Got '{current_map}' from line '{map_line_used[:-1]}' and '{current_class}' from line '{class_line_used[:-1]}'")

    if map_line_used == '' and class_line_used != '' and 'Queued' not in class_line_used:
        self.log.error("Have class_line_used without map_line_used")

    # remove empty lines (bot spam)
    if 'In menus' in current_map and settings.get('trim_console_log') and not force:
        if self.cleanup_primed:
            self.log.debug("Potentially cleaning up console.log")
            console_log_lines_out: List[str] = []
            empty_line_count: int = 0

            with open(console_log_path, 'r', encoding='UTF8', errors='replace') as console_log_read:
                console_log_lines_in: List[str] = console_log_read.readlines()

            for line in console_log_lines_in:
                if line.strip(' \t') == '\n':
                    empty_line_count += 1
                else:
                    console_log_lines_out.append(line)

            if empty_line_count >= 20 and len(console_log_lines_out) > SIZE_LIMIT_MIN_LINES:
                with open(console_log_path, 'w', encoding='UTF8') as console_log_write:
                    for line in console_log_lines_out:
                        console_log_write.write(line)

                self.log.debug(f"Removed {empty_line_count} empty lines from console.log")
            else:
                self.log.debug(f"Didn't remove {empty_line_count} empty lines from console.log")

            self.cleanup_primed = False
    else:
        self.cleanup_primed = True

    return current_map, current_class


# alerts the user that they don't seem to have -condebug
def no_condebug_warning(loc: localization.Localizer, tf2_is_running: bool = True):
    print(Style.BRIGHT, end='')
    print('\n{0}'.format(loc.text("Your TF2 installation doesn't yet seem to be set up properly. To fix:")))
    print(Style.RESET_ALL, end='')
    print(loc.text("1. Right click on Team Fortress 2 in your Steam library"))
    print(loc.text("2. Open properties (very bottom)"))
    print(loc.text("3. Click \"Set launch options...\""))
    print(loc.text("4. Add {0}").format("-condebug"))
    print(loc.text("5. OK and Close"))
    if tf2_is_running:
        print(loc.text("6. Restart TF2"))
    print()

    # -condebug is kinda necessary so just wait to restart if it's not there
    input('{0}\n'.format(loc.text("Press enter in this window when done")))
    raise SystemExit


tf2_classes: tuple = ('Scout', 'Soldier', 'Pyro', 'Demoman', 'Heavy', 'Engineer', 'Medic', 'Sniper', 'Spy')
