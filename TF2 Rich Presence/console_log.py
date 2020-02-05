# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import os
import time
from typing import Dict, List, Union

import colorama

import localization
import settings


# reads a console.log and returns current map and class
def interpret(self, console_log_path: str, user_usernames: list, tf2_start_time: int = 0, kb_limit=settings.get('console_scan_kb'), force=False) -> tuple:
    # defaults
    current_map: str = 'In menus'
    current_class: str = 'Not queued'
    kataiser_seen_on: Union[str, None] = None

    match_types: Dict[str, str] = {'match group 12v12 Casual Match': 'Casual', 'match group MvM Practice': 'MvM (Boot Camp)', 'match group MvM MannUp': 'MvM (Mann Up)',
                                   'match group 6v6 Ladder Match': 'Competitive'}
    disconnect_messages: tuple = ('Server shutting down', 'Steam config directory', 'Lobby destroyed', 'Disconnect:', 'Missing map')
    disconnect_message: str
    tf2_classes: tuple = ('Scout', 'Soldier', 'Pyro', 'Demoman', 'Heavy', 'Engineer', 'Medic', 'Sniper', 'Spy')

    hide_queued_gamemode: bool = settings.get('hide_queued_gamemode')
    user_is_kataiser: bool = 'Kataiser' in user_usernames

    # console.log is a log of tf2's console (duh), only exists if tf2 has -condebug (see the bottom of config_files)
    consolelog_filename: Union[bytes, str] = console_log_path
    self.log.debug(f"Looking for console.log at {consolelog_filename}")
    self.log.console_log_path = consolelog_filename

    if not os.path.exists(consolelog_filename):
        self.log.error(f"console.log doesn't exist, issuing warning (files/dirs in /tf/: {os.listdir(os.path.dirname(console_log_path))})")
        del self.log
        no_condebug_warning()

    # TF2 takes some time to load the console when starting up, so wait a few seconds to avoid getting outdated information
    tf2_uptime = round(time.time()) - tf2_start_time
    if tf2_uptime < 15:
        self.log.debug(f"TF2's uptime is {tf2_uptime} seconds, assuming default state")
        return current_map, current_class

    # only interpret console.log again if it's been modified
    console_log_mtime = os.stat(console_log_path).st_mtime
    if not force and console_log_mtime == self.old_console_log_mtime:
        self.log.debug(f"Not rescanning console.log, remaining on {self.old_console_log_interpretation}")
        return self.old_console_log_interpretation

    consolelog_file_size: int = os.stat(consolelog_filename).st_size
    byte_limit = kb_limit * 1024

    with open(consolelog_filename, 'r', errors='replace') as consolelog_file:
        if consolelog_file_size > byte_limit:
            skip_to_byte = consolelog_file_size - byte_limit
            consolelog_file.seek(skip_to_byte, 0)  # skip to last few KBs

            lines: List[str] = consolelog_file.readlines()
            self.log.debug(f"console.log: {consolelog_file_size} bytes, skipped to {skip_to_byte}, read {byte_limit} bytes and {len(lines)} lines")
        else:
            lines: List[str] = consolelog_file.readlines()
            self.log.debug(f"console.log: {consolelog_file_size} bytes, {len(lines)} lines (didn't skip lines)")

    # limit the file size, for readlines perf
    if consolelog_file_size > byte_limit * 4 and settings.get('trim_console_log') and not force:
        trim_size = byte_limit * 2
        self.log.debug(f"Limiting console.log to {trim_size} bytes")

        try:
            with open(consolelog_filename, 'rb+') as consolelog_file:
                # this can probably be done faster and/or cleaner
                consolelog_file.seek(trim_size, 2)
                consolelog_file_trimmed = consolelog_file.read()
                consolelog_file.seek(0)
                consolelog_file.truncate()
                consolelog_file.write(consolelog_file_trimmed)
        except PermissionError as error:
            self.log.error(f"Failed to trim console.log: {error}")

    # iterates though roughly 16000 lines from console.log and learns everything from them
    line_used: str = ''
    line: str
    for line in lines:
        if 'Map:' in line:
            current_map = line[5:-1]  # this variable is poorly named
            current_class = 'unselected'  # so is this one
            line_used = line

        if ' selected' in line:
            current_class_possibly: str = line[:-11]

            if current_class_possibly in tf2_classes:
                current_class = current_class_possibly
                line_used = line

        if 'Disconnect by user' in line and [i for i in user_usernames if i in line]:
            current_map = 'In menus'
            current_class = 'Not queued'
            line_used = line

        for disconnect_message in disconnect_messages:
            if disconnect_message in line:
                current_map = 'In menus'
                current_class = 'Not queued'
                line_used = line
                break

        if '[PartyClient] Entering queue ' in line:
            current_map = 'In menus'
            line_used = line

            if hide_queued_gamemode:
                current_class = "Queued"
            else:
                current_class = f"Queued for {match_types[line[33:-1]]}"

        if '[PartyClient] Entering s' in line:  # full line: [PartyClient] Entering standby queue
            current_map = 'In menus'
            current_class = 'Queued for a party\'s match'
            line_used = line

        if '[PartyClient] L' in line:  # full line: [PartyClient] Leaving queue
            current_class = 'Not queued'
            line_used = line

        if not user_is_kataiser and 'Kataiser' in line and not self.has_seen_kataiser:
            kataiser_seen_on = current_map

    if not user_is_kataiser and not self.has_seen_kataiser and kataiser_seen_on == current_map and current_map not in ('', 'In menus'):
        self.has_seen_kataiser = True
        self.log.debug(f"Kataiser located, telling user :D (on {current_map})")
        print(f"{colorama.Fore.LIGHTCYAN_EX}Hey, it seems that Kataiser, the developer of TF2 Rich Presence, is in your game! Say hi to me if you'd like :){colorama.Style.RESET_ALL}\n")

    self.log.debug(f"Got '{current_map}' and '{current_class}' from this line: '{line_used[:-1]}'")
    self.old_console_log_interpretation = (current_map, current_class)
    self.old_console_log_mtime = console_log_mtime

    return current_map, current_class


# alerts the user that they don't seem to have -condebug
def no_condebug_warning():
    loc = localization.Localizer(language=settings.get('language'))

    print(colorama.Style.BRIGHT, end='')
    print('\n{0}'.format(loc.text("Your TF2 installation doesn't yet seem to be set up properly. To fix:")))
    print(colorama.Style.RESET_ALL, end='')
    print(loc.text("1. Right click on Team Fortress 2 in your Steam library"))
    print(loc.text("2. Open properties (very bottom)"))
    print(loc.text("3. Click \"Set launch options...\""))
    print(loc.text("4. Add {0}").format("-condebug"))
    print(loc.text("5. OK and Close"))
    print('{0}\n'.format(loc.text("6. Restart TF2")))

    # -condebug is kinda necessary so just wait to restart if it's not there
    input('{0}\n'.format(loc.text("Press enter in this window when done")))
    raise SystemExit
