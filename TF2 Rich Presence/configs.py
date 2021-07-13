# Copyright (C) 2018-2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import os
from typing import Callable, List, Optional, Set, Tuple, Union

import vdf

import logger


# allows for detecting which class the user is playing as
def class_config_files(log, exe_location: str):
    log.debug(f"Reading (and possibly modifying) class configs at {exe_location}")
    tf2_classes: List[str] = ['Scout', 'Soldier', 'Pyro', 'Demoman', 'Heavy', 'Engineer', 'Medic', 'Sniper', 'Spy']
    classes_found: List[str] = []
    classes_not_found: List[str] = []
    cfg_path: str = os.path.join(exe_location, 'tf', 'cfg')
    # tf2 config files are at 'Steam\steamapps\common\Team Fortress 2\tf\cfg'

    if not os.path.isdir(cfg_path):
        if os.path.isdir(exe_location):
            log.error(f"{exe_location} exists but {cfg_path} doesn't. WTF?")
        else:
            log.error(f"{exe_location} doesn't exist, can't read/modify class config files")

    for tf2_class in tf2_classes:
        # 'echo' means 'output to console' in source-speak
        selected_line: str = f'\n// Added by TF2 Rich Presence, please don\'t remove\necho "{tf2_class} selected"\n'

        config_filename: str = tf2_class.lower().replace('heavy', 'heavyweapons')  # valve why
        config_path: str = os.path.join(cfg_path, f'{config_filename}.cfg')

        if os.path.isfile(config_path):
            # reads each existing class.cfg
            with open(config_path, 'r+', errors='ignore') as class_config_file:
                if selected_line not in class_config_file.read():
                    # if it doesn't already have the echo line, add it
                    class_config_file.write('\n' + selected_line)
                    classes_not_found.append(config_filename)
                else:
                    classes_found.append(config_filename)
        else:
            # the config file doesn't exist, so create it and add the echo line
            with open(config_path, 'w') as class_config_file:
                class_config_file.write(selected_line)

            log.debug(f"Created {class_config_file.name}")

    log.debug(f"Classes with echo found: {classes_found}")
    log.debug(f"Classes with echo added: {classes_not_found}")


# reads steam's launch options save file to find TF2 launch options and usernames with -condebug
def steam_config_file(self, exe_location: str, require_condebug: bool) -> Optional[Tuple[str, Set[str]]]:
    self.log.debug(f"Scanning Steam config files{' for -condebug' if require_condebug else ''}")
    found_condebug: bool = False
    found_usernames: Set[str] = set()
    user_id_folders: List[str] = os.listdir(os.path.join(exe_location, 'userdata'))
    most_likely_args: Tuple[int, str] = (-1, '')

    if user_id_folders:
        self.log.debug(f"User id folders: {user_id_folders}")
    else:
        self.log.error("Steam userdata folder is empty")
        return None

    for user_id_folder in user_id_folders:  # possibly multiple users for the same steam install
        # 'C:\Program Files (x86)\Steam\userdata\*user id number*\config\localconfig.vdf'
        global_config_file_path: str = os.path.join(exe_location, 'userdata', user_id_folder, 'config', 'localconfig.vdf')
        self.log.debug(f"Reading {global_config_file_path}")

        try:
            with open(global_config_file_path, 'r', errors='replace') as global_config_file:
                global_config_file_read: str = global_config_file.read()
                global_config_file_size: int = os.stat(global_config_file_path).st_size
        except FileNotFoundError:
            self.log.debug(f"Couldn't find {global_config_file_path}")
            continue
        except PermissionError as error:
            self.log.error(str(error))
            continue

        if require_condebug:
            if '"440"' not in global_config_file_read:
                continue
            else:
                self.log.debug(f"\"440\" found, parsing file ({global_config_file_size} bytes)")
        else:
            self.log.debug(f"Parsing file ({global_config_file_size} bytes)")

        parsed: dict = vdf.loads(global_config_file_read)
        self.log.debug(f"VDF parse complete ({len(parsed['UserLocalConfigStore'])} keys)")
        parsed_lowercase: dict = lowercase_keys(parsed)
        self.log.debug(f"Lowercase complete ({len(parsed['userlocalconfigstore'])} keys)")

        try:
            possible_username: str = parsed_lowercase['userlocalconfigstore']['friends']['personaname']
            self.log.debug(f"Possible username: {possible_username}")
        except KeyError:
            personaname_exists_in_file: bool = 'personaname' in global_config_file_read.lower()
            self.log.error(f"Couldn't find PersonaName in config (\"personaname\" in lowercase: {personaname_exists_in_file})")
            possible_username = ''

        try:
            tf2_savedata = parsed_lowercase['userlocalconfigstore']['software']['valve']['steam']['apps']['440']
        except KeyError:
            pass  # (hopefully) -condebug was in some other game
        else:
            last_played_time: int = int(tf2_savedata['lastplayed'])

            if last_played_time > most_likely_args[0]:
                most_likely_args = (last_played_time, tf2_savedata['launchoptions'])

            if require_condebug and 'launchoptions' in tf2_savedata and '-condebug' in tf2_savedata['launchoptions']:
                found_condebug = True
                self.log.debug(f"Found -condebug in launch options ({tf2_savedata['launchoptions']})")

        if possible_username or not require_condebug:
            found_usernames.add(possible_username)

        config_mtime: int = int(os.stat(global_config_file_path).st_mtime)
        self.steam_config_mtimes[global_config_file_path] = config_mtime
        self.log.debug(f"Added mtime ({config_mtime})")

    if not found_condebug and require_condebug:
        self.log.error("-condebug not found, telling user", reportable=False)
        # yell at the user to fix their settings
        self.no_condebug = False
        return None
    else:
        return most_likely_args[1], found_usernames


# given Steam's install, find a TF2 install
def find_tf2_exe(self, steam_location: str) -> str:
    extend_path: Callable[[str], str] = lambda path: os.path.join(path, 'steamapps', 'common', 'Team Fortress 2', 'hl2.exe')
    default_path: str = extend_path(steam_location)

    if is_tf2_install(self.log, default_path):
        return default_path

    self.log.debug("Reading libraryfolders.vdf for TF2 installation")

    with open(os.path.join(steam_location, 'steamapps', 'libraryfolders.vdf'), 'r', encoding='UTF8', errors='replace') as libraryfolders_vdf:
        libraryfolders_vdf_read: dict = vdf.load(libraryfolders_vdf)['LibraryFolders']

    for library_folder_key in libraryfolders_vdf_read:
        if len(library_folder_key) < 4:
            potentional_install: str = extend_path(libraryfolders_vdf_read[library_folder_key])

            if is_tf2_install(self.log, potentional_install):
                return potentional_install

    self.log.error(f"Couldn't find a TF2 installation in any Steam library folders (libraryfolders.vdf: {libraryfolders_vdf_read})")


# makes sure a path to hl2.exe exists and is TF2 and not some other game
def is_tf2_install(log: logger.Log, exe_location: str) -> bool:
    if not os.path.isfile(exe_location):
        return False

    is_tf2: bool = False
    appid_path: str = os.path.join(os.path.dirname(exe_location), 'steam_appid.txt')

    if os.path.isfile(appid_path):
        with open(appid_path, 'rb') as appid_file:
            appid_read: bytes = appid_file.read()

            if appid_read.startswith(b'440\n'):
                is_tf2 = True
            else:
                log.debug(f"steam_appid.txt contains \"{appid_read}\" ")
    else:
        log.debug(f"steam_appid.txt doesn't exist (install folder: {os.listdir(os.path.dirname(exe_location))})")

    if is_tf2:
        log.debug(f"Found TF2 hl2.exe at {exe_location}")
        return True
    else:
        log.error(f"Found non-TF2 hl2.exe at {exe_location}")
        return False


# adapted from https://www.popmartian.com/tipsntricks/2014/11/20/how-to-lower-case-all-dictionary-keys-in-a-complex-python-dictionary/
def lowercase_keys(mixed_case: Union[dict, list]) -> Union[dict, list]:
    allowed_keys: Tuple[str, ...] = ('userlocalconfigstore', 'friends', 'personaname', 'userlocalconfigstore', 'software', 'valve', 'steam', 'apps', '440', 'launchoptions', 'lastplayed')
    key: str

    for key in list(mixed_case):
        key_lower: str = key.lower()

        if key_lower in allowed_keys:
            mixed_case[key_lower] = mixed_case.pop(key)

            if isinstance(mixed_case[key_lower], dict) or isinstance(mixed_case[key_lower], list):
                mixed_case[key_lower] = lowercase_keys(mixed_case[key_lower])
        else:
            del mixed_case[key]

    return mixed_case
