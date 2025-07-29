# Copyright (C) 2018-2025 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import dataclasses
import functools
import os
import re
from typing import Dict, List, Optional, Set, Tuple, Pattern

import logger
import settings


@dataclasses.dataclass
class ConsoleLogParsed:
    in_menus: bool = True
    tf2_map: str = ''
    tf2_class: str = ''
    queued_state: str = "Not queued"
    hosting: bool = False
    server_name: str = ''
    server_players: int = 0
    server_players_max: int = 0


@dataclasses.dataclass
class ConsoleLogPersistence:
    file_position: int = 0
    just_started_server: bool = False
    server_still_running: bool = False
    connecting_to_matchmaking: bool = False
    using_wav_cache: bool = False
    found_first_wav_cache: bool = False
    kataiser_seen_on: str = ''
    server_name_full: str = ''


# reads a console.log and returns as much game state as possible, alternatively None if whether an old scan was reused
def interpret(self, console_log_path: str, user_usernames: Set[str], force: bool = False, from_game_state: Optional = None, tf2_start_time: int = 0) -> Optional[ConsoleLogParsed]:
    TF2_LOAD_TIME_ASSUMPTION: int = 10

    # defaults
    parse_results = ConsoleLogParsed()
    in_menus: bool = parse_results.in_menus
    tf2_map: str = parse_results.tf2_map
    tf2_class: str = parse_results.tf2_class
    queued_state: str = parse_results.queued_state
    hosting: bool = parse_results.hosting
    server_players: int = parse_results.server_players
    server_players_max: int = parse_results.server_players_max

    # if we already have a game state and file position, just update the state from the new lines since then
    if from_game_state:
        in_menus = from_game_state.in_menus
        tf2_map = from_game_state.tf2_map
        tf2_class = from_game_state.tf2_class
        queued_state = from_game_state.queued_state
        hosting = from_game_state.hosting
        server_players = from_game_state.server_players[0]
        server_players_max = from_game_state.server_players[1]
        persistence: ConsoleLogPersistence = from_game_state.console_log_persistence
    else:
        persistence = ConsoleLogPersistence()

    def store_parsing_persistence(default: bool):
        if default:
            self.game_state.console_log_persistence = ConsoleLogPersistence()
        else:
            self.game_state.console_log_persistence = ConsoleLogPersistence(file_position, just_started_server, server_still_running, connecting_to_matchmaking,
                                                                            using_wav_cache, found_first_wav_cache, kataiser_seen_on, server_name_full)

    # console.log is a log of tf2's console (duh), only exists if tf2 has -condebug (see no_condebug_warning() in GUI)
    self.log.debug(f"Looking for console.log at {console_log_path}")

    if not os.path.isfile(console_log_path):
        self.log.error(f"console.log doesn't exist, issuing warning (files/dirs in /tf/: {os.listdir(os.path.dirname(console_log_path))})", reportable=False)
        self.no_condebug = False
        store_parsing_persistence(True)
        return parse_results  # might as well

    # only interpret console.log again if it's been modified
    self.console_log_mtime = int(os.stat(console_log_path).st_mtime)
    if not force and self.console_log_mtime == self.old_console_log_mtime:
        self.log.debug("Not rescanning console.log")
        return None

    # TF2 takes some time to load the console when starting up, so wait until it's been modified to avoid getting outdated information
    console_log_mtime_relative: int = self.console_log_mtime - tf2_start_time
    if console_log_mtime_relative <= TF2_LOAD_TIME_ASSUMPTION:
        self.log.debug(f"console.log's mtime relative to TF2's start time is {console_log_mtime_relative} (<= {TF2_LOAD_TIME_ASSUMPTION}), assuming default state")
        store_parsing_persistence(True)
        return parse_results

    # resume parsing from persistence
    file_position: int = persistence.file_position
    just_started_server: bool = persistence.just_started_server
    server_still_running: bool = persistence.server_still_running
    connecting_to_matchmaking: bool = persistence.connecting_to_matchmaking
    using_wav_cache: bool = persistence.using_wav_cache
    found_first_wav_cache: bool = persistence.found_first_wav_cache
    kataiser_seen_on: str = persistence.kataiser_seen_on
    server_name_full: str = persistence.server_name_full

    consolelog_file_size: int = os.stat(console_log_path).st_size

    if self.last_console_log_size is not None:
        if consolelog_file_size < self.last_console_log_size:
            self.log.error("console.log seems to have been externally shortened (possibly TF2BD)")
            # TODO: try to account for this somehow, if need be

        self.last_console_log_size = consolelog_file_size

    # actually open the file finally
    with open(console_log_path, 'r', errors='replace', encoding='UTF8') as consolelog_file:
        consolelog_file.seek(file_position)  # skip to last saved position
        consolelog_read = consolelog_file.read()
        lines: List[str] = consolelog_read.splitlines(keepends=True)
        self.log.debug(f"console.log: {consolelog_file_size} bytes, skipped to {file_position}, read {len(consolelog_read)} bytes and {len(lines)} lines")
        file_position = consolelog_file.tell()

    # update this again late, fixes wrong detections but may cause a duplicate scan
    self.console_log_mtime = int(os.stat(console_log_path).st_mtime)

    # setup
    now_in_menus: bool = False
    with_optimization: bool = True  # "with" optimization, not "with optimization"
    chat_safety: bool = True
    user_is_kataiser: bool = 'Kataiser' in user_usernames
    # TODO: detection for canceling loading into community servers (if possible)
    match_types: Dict[str, str] = {'12v12 Casual Match': 'Casual', 'MvM Practice': 'MvM (Boot Camp)', 'MvM MannUp': 'MvM (Mann Up)', '6v6 Ladder Match': 'Competitive'}
    menus_messages: Tuple[str, ...] = ('For FCVAR_REPLICATED', '[TF Workshop]', 'request to abandon', 'Server shutting down', 'Lobby destroyed', 'Disconnect:', 'destroyed CAsyncWavDataCache',
                                       'ShutdownGC', 'Connection failed after', 'Host_Error')
    menus_message_used: Optional[str] = None
    menus_message: str
    gui_update: int = 0
    gui_updates: int = 0
    is_initial_parse = file_position == 0

    for username in user_usernames:
        if 'with' in username:
            with_optimization = False
        if ' :  ' in username:
            chat_safety = False

    # iterates though 0 (initially) to roughly 16000 lines from console.log and learns (almost) everything from them
    line: str
    for line in lines:
        gui_update += 1

        if gui_update == 1500:
            # update the GUI occasionally during big parses, to prevent UI lag
            self.gui.safe_update()
            gui_update = 0
            gui_updates += 1

        # lines that have "with" in them are basically always kill logs and can be safely ignored
        # this (probably) improves performance
        # same goes for chat logs, this one's actually to reduce false detections
        if (with_optimization and 'with' in line) or (chat_safety and ' :  ' in line):
            continue

        if not in_menus:
            for menus_message in menus_messages:
                if menus_message in line:
                    now_in_menus = True
                    break

            if line.startswith('hostname: '):
                server_name_full = line[10:-1]

            elif line.startswith('players : '):
                line_split = line.split()
                server_players = int(line_split[2]) + int(line_split[4])  # humans + bots
                server_players_max = int(line_split[6][1:])

            elif line.endswith(' selected \n'):
                class_line_possibly: List[str] = line[:-11].split()

                if class_line_possibly and class_line_possibly[-1] in tf2_classes:
                    tf2_class = class_line_possibly[-1]

            elif 'Disconnect by user' in line:
                for user_username in user_usernames:
                    if user_username in line:
                        now_in_menus = True
                        break

            elif 'Missing map' in line and 'Missing map material' not in line:
                now_in_menus = True

            if not user_is_kataiser and '[U:1:160315024]' in line:
                kataiser_seen_on = tf2_map

        elif 'SV_ActivateServer' in line:  # full line: "SV_ActivateServer: setting tickrate to 66.7"
            just_started_server = True

        if line.startswith('Map:'):
            in_menus = False
            connecting_to_matchmaking = False
            tf2_map = line[5:-1]
            tf2_class = ''

            if just_started_server:
                server_still_running = True
                just_started_server = False
            else:
                just_started_server = False
                server_still_running = False

        elif not connecting_to_matchmaking and 'Connected to' in line:
            # joined a community server, so must use CAsyncWavDataCache method to detect disconnects
            using_wav_cache = True
            found_first_wav_cache = False
            connecting_to_matchmaking = False

        elif 'matchmaking server' in line:
            connecting_to_matchmaking = True

        elif using_wav_cache and 'CAsyncWavDataCache' in line:
            if found_first_wav_cache:
                # it's the one after disconnecting

                if in_menus:
                    # ...unless it isn't?
                    self.log.error("Found CAsyncWavDataCache despite being in menus already")
                else:
                    now_in_menus = True
            else:
                # it's the one after loading in
                found_first_wav_cache = True

        elif '[P' in line:
            if '[PartyClient] L' in line:  # full line: "[PartyClient] Leaving queue"
                # queueing is not necessarily only in menus
                queued_state = "Not queued"

            elif '[PartyClient] Entering q' in line:  # full line: "[PartyClient] Entering queue for match group " + whatever mode
                match_type: str = line.split('match group ')[-1][:-1]
                queued_state = f"Queued for {match_types[match_type]}"

            elif '[PartyClient] Entering s' in line:  # full line: "[PartyClient] Entering standby queue"
                queued_state = 'Queued for a party\'s match'

        if now_in_menus:
            now_in_menus = False
            in_menus = True
            menus_message_used = line
            kataiser_seen_on = ''
            connecting_to_matchmaking = False
            using_wav_cache = False
            found_first_wav_cache = False
            just_started_server = False
            server_still_running = False

    if not user_is_kataiser and not in_menus and kataiser_seen_on == tf2_map:
        self.log.debug(f"Kataiser located, telling user :D (on {tf2_map})")
        self.gui.set_bottom_text('kataiser', True)

    if in_menus:
        tf2_map = ''
        tf2_class = ''
        hosting = False
        server_name = ''
        server_name_full = ''
        server_players = 0
        server_players_max = 0
        self.gui.set_bottom_text('kataiser', False)

        if menus_message_used:
            self.log.debug(f"Menus message used: \"{menus_message_used.strip()}\"")
    else:
        server_name, is_valve_server = cleanup_server_name(server_name_full)

        if is_valve_server and server_players_max == 32:
            server_players_max = 24  # cool

        if tf2_class != '' and tf2_map == '':
            self.log.error("Have class without map")

        if server_still_running:
            hosting = True

    if settings.get('hide_queued_gamemode') and "Queued" in queued_state:
        self.log.debug(f"Hiding queued state (\"{queued_state}\" to \"Queued\")")
        queued_state = "Queued"

    parse_results = ConsoleLogParsed(in_menus, tf2_map, tf2_class, queued_state, hosting, server_name, server_players, server_players_max)
    self.log.debug(f"console.log parse results (initial = {is_initial_parse}): {parse_results}")

    if gui_updates != 0:
        self.log.debug(f"Mid-parse GUI updates: {gui_updates}")

    store_parsing_persistence(False)
    return parse_results


# check if any characters outside of ASCII exist in any usernames
def non_ascii_in_usernames(usernames: Set[str]) -> bool:
    for username in usernames:
        if non_ascii_regex.search(username) is not None:
            return True

    return False


# make server names look a bit nicer
@functools.cache
def cleanup_server_name(name: str, log: Optional[logger.Log] = None) -> tuple[str, bool]:
    cleaned: tuple[str, bool]

    if re_valve_server.match(name):
        cleaned = re_valve_server_remove.sub("", name), True
    else:
        name = ''.join(c for c in name if c.isprintable() and c not in ('█', '▟', '▙')).strip()  # removes unprintable/ugly characters
        name = re_double_space.sub(' ', name)  # removes double space

        if len(name) > 32:
            # TODO: would prefer to use actual text width here
            cleaned = f'{name[:30]}…', False
        else:
            cleaned = name, False

    if log and name != cleaned[0]:
        log.debug(f"Cleaned up server name from \"{name}\" to \"{cleaned[0]}\"")

    return cleaned


re_valve_server: Pattern[str] = re.compile(r'Valve Matchmaking Server \(.*srcds.*\)')
re_valve_server_remove: Pattern[str] = re.compile(r'( srcds[^)]+)|( \(srcds.*\))')
re_double_space: Pattern[str] = re.compile(r' {2,}')
tf2_classes: Tuple[str, ...] = ('Scout', 'Soldier', 'Pyro', 'Demoman', 'Heavy', 'Engineer', 'Medic', 'Sniper', 'Spy')
non_ascii_regex = re.compile('[^\x00-\x7F]')
