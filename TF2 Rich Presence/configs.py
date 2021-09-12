# Copyright (C) 2018-2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import os
import winreg
from typing import Callable, List, Optional, Tuple, Union

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


# reads steam's launch options save file to find TF2 launch options
def steam_config_file(self, exe_location: str, require_condebug: bool) -> Optional[str]:
    self.log.debug(f"Scanning Steam config files{' for -condebug' if require_condebug else ''}")
    found_condebug: bool = False
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

        try:
            with open(global_config_file_path, 'r', errors='replace') as global_config_file:
                global_config_file_read: str = global_config_file.read()
                global_config_file_size: int = os.stat(global_config_file_path).st_size
        except FileNotFoundError:
            self.log.debug(f"Couldn't find {global_config_file_path}")
            continue
        except PermissionError as error:
            self.log.error(f"Couldn't read {global_config_file_path}: {str(error)}")
            continue

        self.log.debug(f"Reading {global_config_file_path}")

        if require_condebug:
            if '"440"' not in global_config_file_read or '-condebug' not in global_config_file_read:
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
            username: Optional[str] = parsed_lowercase['userlocalconfigstore']['friends']['personaname']
        except KeyError:
            username = None

        try:
            tf2_savedata: dict = parsed_lowercase['userlocalconfigstore']['software']['valve']['steam']['apps']['440']
        except KeyError:
            pass  # (hopefully) -condebug was in some other game
        else:
            last_played_time: int = int(tf2_savedata['lastplayed'])
            launch_options: str = tf2_savedata['launchoptions'] if 'launchoptions' in tf2_savedata else ''

            if username in self.usernames or last_played_time > most_likely_args[0]:
                most_likely_args = (last_played_time, launch_options)

            if require_condebug and '-condebug' in tf2_savedata['launchoptions']:
                found_condebug = True
                self.log.debug(f"Found -condebug in launch options ({launch_options})")

        config_mtime: int = int(os.stat(global_config_file_path).st_mtime)
        self.steam_config_mtimes[global_config_file_path] = config_mtime
        self.log.debug(f"Added mtime ({config_mtime})")

    if not found_condebug and require_condebug:
        self.log.error("-condebug not found, telling user", reportable=False)
        # yell at the user to fix their settings
        self.no_condebug = False
        return None
    else:
        return most_likely_args[1]


# given Steam's install, find a TF2 install
def find_tf2_exe(self, steam_location: str) -> Optional[str]:
    extend_path: Callable[[str], str] = lambda path: os.path.join(path, 'steamapps', 'common', 'Team Fortress 2', 'hl2.exe')
    default_path: str = extend_path(steam_location)

    if is_tf2_install(self.log, default_path):
        return default_path

    self.log.debug("Reading libraryfolders.vdf for TF2 installation")

    with open(os.path.join(steam_location, 'steamapps', 'libraryfolders.vdf'), 'r', encoding='UTF8', errors='replace') as libraryfolders_vdf:
        libraryfolders_vdf_read: dict = vdf.load(libraryfolders_vdf)

    if 'LibraryFolders' in libraryfolders_vdf_read:
        libraryfolders_data: dict = libraryfolders_vdf_read['LibraryFolders']
    elif 'libraryfolders' in libraryfolders_vdf_read:
        libraryfolders_data = libraryfolders_vdf_read['libraryfolders']
    else:
        self.log.error(f"libraryfolders.vdf seems broken, contains: {libraryfolders_vdf_read}")
        return

    for library_folder_key in libraryfolders_data:
        if len(library_folder_key) < 4:
            library_folder_entry: Union[dict, str] = libraryfolders_data[library_folder_key]
            library_folder_path: str = library_folder_entry['path'] if 'path' in library_folder_entry else library_folder_entry
            potentional_install: str = extend_path(library_folder_path)

            if is_tf2_install(self.log, potentional_install):
                return potentional_install

    self.log.error(f"Couldn't find a TF2 installation in any Steam library folders, will continually scan for it (libraryfolders.vdf: {libraryfolders_vdf_read})")


# makes sure a path to hl2.exe exists and is TF2 and not some other game
def is_tf2_install(log: logger.Log, exe_location: str) -> bool:
    if not os.path.isfile(exe_location):
        log.debug(f"No TF2 installation found at {exe_location}")
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


# Steam seems to update this often enough
def get_steam_username() -> str:
    key: winreg.HKEYType = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Valve\\Steam\\")
    username: str = winreg.QueryValueEx(key, 'LastGameNameUsed')[0]
    key.Close()
    return username


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
