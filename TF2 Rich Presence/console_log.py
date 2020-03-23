# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import os
from typing import Dict, List, Tuple, Union

import colorama

import launcher
import localization
import settings


# reads a console.log and returns current map and class
def interpret(self, console_log_path: str, user_usernames: list, kb_limit: float = float(settings.get('console_scan_kb')), force: bool = False, tf2_start_time: int = 0) -> Tuple[str, str]:
    # defaults
    current_map: str = 'In menus'
    current_class: str = 'Not queued'
    kataiser_seen_on: Union[str, None] = None

    match_types: Dict[str, str] = {'match group 12v12 Casual Match': 'Casual', 'match group MvM Practice': 'MvM (Boot Camp)', 'match group MvM MannUp': 'MvM (Mann Up)',
                                   'match group 6v6 Ladder Match': 'Competitive'}
    menus_messages: tuple = ('Server shutting down', 'For FCVAR_REPLICATED', '[TF Workshop]', 'Lobby destroyed', 'Disconnect:', 'Missing map')
    menus_message: str
    tf2_classes: tuple = ('Scout', 'Soldier', 'Pyro', 'Demoman', 'Heavy', 'Engineer', 'Medic', 'Sniper', 'Spy')

    hide_queued_gamemode: bool = settings.get('hide_queued_gamemode')
    user_is_kataiser: bool = 'Kataiser' in user_usernames

    # console.log is a log of tf2's console (duh), only exists if tf2 has -condebug (see no_condebug_warning())
    self.log.debug(f"Looking for console.log at {console_log_path}")
    self.log.console_log_path = console_log_path

    if not os.path.isfile(console_log_path):
        self.log.error(f"console.log doesn't exist, issuing warning (files/dirs in /tf/: {os.listdir(os.path.dirname(console_log_path))})", reportable=False)
        del self.log
        no_condebug_warning(tf2_is_running=True)

    # only interpret console.log again if it's been modified
    console_log_mtime: int = int(os.stat(console_log_path).st_mtime)
    if not force and console_log_mtime == self.old_console_log_mtime:
        self.log.debug(f"Not rescanning console.log, remaining on {self.old_console_log_interpretation}")
        return self.old_console_log_interpretation

    # TF2 takes some time to load the console when starting up, so until it's been modified to avoid getting outdated information
    console_log_mtime_relative = console_log_mtime - tf2_start_time
    if console_log_mtime_relative < 0:
        self.log.debug(f"console.log's mtime relative to TF2's start time is {console_log_mtime_relative}, assuming default state")
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

    # limit the file size, for readlines perf
    if consolelog_file_size > byte_limit * 4 and settings.get('trim_console_log') and not force and not launcher.DEBUG:
        trim_size = int(byte_limit * 2)
        self.log.debug(f"Limiting console.log to {trim_size} bytes")

        try:
            with open(console_log_path, 'rb+') as consolelog_file_b:
                # this can probably be done faster and/or cleaner
                consolelog_file_b.seek(trim_size, 2)
                consolelog_file_trimmed = consolelog_file_b.read()
                consolelog_file_b.seek(0)
                consolelog_file_b.truncate()
                consolelog_file_b.write(consolelog_file_trimmed)
        except PermissionError as error:
            self.log.error(f"Failed to trim console.log: {error}")

    # iterates though roughly 16000 lines from console.log and learns everything from them
    line_used: str = ''
    just_started_server: bool = False
    server_still_running: bool = False

    line: str
    for line in lines:
        for menus_message in menus_messages:
            if menus_message in line:
                current_map = 'In menus'
                current_class = 'Not queued'
                line_used = line
                break

        if ' selected' in line:
            current_class_possibly: str = line[:-11]

            if current_class_possibly in tf2_classes:
                current_class = current_class_possibly
                line_used = line

        elif 'Map:' in line:
            current_map = line[5:-1]  # this variable is poorly named
            current_class = 'unselected'  # so is this one
            line_used = line

            if just_started_server:
                server_still_running = True
                just_started_server = False
            else:
                just_started_server = False
                server_still_running = False

        elif '[PartyClient] L' in line:  # full line: [PartyClient] Leaving queue
            current_class = 'Not queued'
            line_used = line

        elif '[PartyClient] Entering queue ' in line:
            current_map = 'In menus'
            line_used = line

            if hide_queued_gamemode:
                current_class = "Queued"
            else:
                current_class = f"Queued for {match_types[line[33:-1]]}"

        elif 'Disconnect by user' in line and [i for i in user_usernames if i in line]:
            current_map = 'In menus'
            current_class = 'Not queued'
            line_used = line

        elif '[PartyClient] Entering s' in line:  # full line: [PartyClient] Entering standby queue
            current_map = 'In menus'
            current_class = 'Queued for a party\'s match'
            line_used = line

        elif 'SV_ActivateServer' in line:
            just_started_server = True

        if not user_is_kataiser and 'Kataiser' in line and not self.has_seen_kataiser:
            kataiser_seen_on = current_map

    if server_still_running and current_map != 'In menus':
        current_map = f'{current_map} (hosting)'

    if not user_is_kataiser and not self.has_seen_kataiser and kataiser_seen_on == current_map and current_map not in ('', 'In menus'):
        self.has_seen_kataiser = True
        self.log.debug(f"Kataiser located, telling user :D (on {current_map})")
        print(f"{colorama.Fore.LIGHTCYAN_EX}Hey, it seems that Kataiser, the developer of TF2 Rich Presence, is in your game! Say hi to me if you'd like :){colorama.Style.RESET_ALL}\n")

    self.log.debug(f"Got '{current_map}' and '{current_class}' from this line: '{line_used[:-1]}'")
    self.old_console_log_interpretation = (current_map, current_class)
    self.old_console_log_mtime = console_log_mtime

    return current_map, current_class


# alerts the user that they don't seem to have -condebug
def no_condebug_warning(tf2_is_running: bool = True):
    loc = localization.Localizer(language=settings.get('language'))

    print(colorama.Style.BRIGHT, end='')
    print('\n{0}'.format(loc.text("Your TF2 installation doesn't yet seem to be set up properly. To fix:")))
    print(colorama.Style.RESET_ALL, end='')
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
