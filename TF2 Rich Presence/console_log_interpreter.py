import os
from typing import Dict, List, Union

import colorama

import settings
import main


# reads a console.log and returns current map and class
def interpret(self, console_log_path: str, user_usernames: list, kb_limit=settings.get('console_scan_kb'), force=False) -> tuple:
    # defaults
    current_map: str = ''
    current_class: str = ''
    kataiser_seen_on: str = ''

    match_types: Dict[str, str] = {'match group 12v12 Casual Match': 'Casual', 'match group MvM Practice': 'MvM (Boot Camp)', 'match group MvM MannUp': 'MvM (Mann Up)',
                                   'match group 6v6 Ladder Match': 'Competitive'}
    disconnect_messages = ('Server shutting down', 'Steam config directory', 'Lobby destroyed', 'Disconnect:', 'Missing map')
    tf2_classes = ('Scout', 'Soldier', 'Pyro', 'Demoman', 'Heavy', 'Engineer', 'Medic', 'Sniper', 'Spy')

    hide_queued_gamemode = settings.get('hide_queued_gamemode')
    user_is_kataiser = 'Kataiser' in user_usernames

    # console.log is a log of tf2's console (duh), only exists if tf2 has -condebug (see the bottom of config_files)
    consolelog_filename: Union[bytes, str] = console_log_path
    self.log.debug(f"Looking for console.log at {consolelog_filename}")
    self.log.console_log_path = consolelog_filename

    if not os.path.exists(consolelog_filename):
        self.log.error(f"console.log doesn't exist, issuing warning (files/dirs in /tf/: {os.listdir(os.path.dirname(console_log_path))})")
        del self.log
        main.no_condebug_warning()

    # only interpret console.log again if it's been modified
    console_log_mtime = os.stat(console_log_path).st_mtime
    if not force and console_log_mtime == self.old_console_log_mtime:
        self.log.debug(f"Not rescanning console.log, remaining on {self.old_console_log_interpretation}")
        return self.old_console_log_interpretation

    with open(consolelog_filename, 'r', errors='replace') as consolelog_file:
        consolelog_file_size: int = os.stat(consolelog_filename).st_size
        byte_limit = kb_limit * 1024

        if consolelog_file_size > byte_limit:
            skip_to_byte = consolelog_file_size - byte_limit
            consolelog_file.seek(skip_to_byte, 0)  # skip to last few KBs

            lines: List[str] = consolelog_file.readlines()
            self.log.debug(f"console.log: {consolelog_file_size} bytes, skipped to {skip_to_byte}, read {byte_limit} bytes and {len(lines)} lines")
        else:
            lines: List[str] = consolelog_file.readlines()
            self.log.debug(f"console.log: {consolelog_file_size} bytes, {len(lines)} lines (didn't skip lines)")

    # limit the file size, for readlines perf
    if consolelog_file_size > byte_limit * 4 and settings.get('trim_console_log'):
        trim_size = byte_limit * 2
        self.log.debug(f"Limiting console.log to {trim_size} bytes")

        try:
            with open(consolelog_filename, 'rb+') as consolelog_file:
                # this can probably be done faster and/or cleaner
                consolelog_file_trim = consolelog_file.read()[-trim_size:]
                consolelog_file.seek(0)
                consolelog_file.truncate()
                consolelog_file.write(consolelog_file_trim)
        except PermissionError as error:
            self.log.error(f"Failed to trim console.log: {error}")

    # iterates though roughly 16000 lines from console.log and learns everything from them
    line_used: str = ''
    for line in lines:
        if 'Map:' in line:
            current_map = line[5:-1]
            current_class = 'unselected'  # this variable is poorly named
            line_used = line

        if 'selected' in line:
            current_class_possibly = line[:-11]

            if current_class_possibly in tf2_classes:
                current_class = current_class_possibly
                line_used = line

        if 'Disconnect by user' in line and [i for i in user_usernames if i in line]:
            current_map = 'In menus'  # so is this one
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

        if not user_is_kataiser and not self.has_seen_kataiser and 'Kataiser' in line:
            kataiser_seen_on = current_map

    if not user_is_kataiser and not self.has_seen_kataiser and kataiser_seen_on == current_map and current_map not in ('', 'In menus'):
        self.has_seen_kataiser = True
        self.log.debug(f"Kataiser located, telling user :) (on {current_map})")
        print(f"{colorama.Fore.LIGHTCYAN_EX}Hey, it seems that Kataiser, the developer of TF2 Rich Presence, is in your game! Say hi to me if you'd like :){colorama.Style.RESET_ALL}\n")

    self.log.debug(f"Got '{current_map}' and '{current_class}' from this line: '{line_used[:-1]}'")
    self.old_console_log_interpretation = (current_map, current_class)
    self.old_console_log_mtime = console_log_mtime

    return current_map, current_class
