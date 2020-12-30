# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import os
from typing import List, Set, Union

import vdf

import console_log


# allows the console to output 'class selected' on class choose
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


# reads steam's launch options save file to find usernames with -condebug
def steam_config_file(self, exe_location: str, tf2_is_running: bool = False) -> Set[str]:
    self.log.debug("Scanning Steam config files for -condebug")
    found_condebug: bool = False
    found_usernames: Set[str] = set()

    user_id_folders: List[str] = next(os.walk(os.path.join(exe_location, 'userdata')))[1]
    self.log.debug(f"User id folders: {user_id_folders}")
    for user_id_folder in user_id_folders:  # possibly multiple users for the same steam install
        try:
            # 'C:\Program Files (x86)\Steam\userdata\*user id number*\config\localconfig.vdf'
            global_config_file_path: str = os.path.join(exe_location, 'userdata', user_id_folder, 'config', 'localconfig.vdf')
            self.log.debug(f"Reading {global_config_file_path}")

            with open(global_config_file_path, 'r', errors='replace') as global_config_file:
                global_config_file_read: str = global_config_file.read()
                global_config_file_size: int = os.stat(global_config_file_path).st_size

            if '-condebug' not in global_config_file_read or '"440"' not in global_config_file_read:
                continue

            self.log.debug(f"-condebug and \"440\" found, parsing file ({global_config_file_size} bytes)")
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
                tf2_launch_options = parsed_lowercase['userlocalconfigstore']['software']['valve']['steam']['apps']['440']['launchoptions']
            except KeyError:
                pass  # (hopefully) -condebug was in some other game
            else:
                if '-condebug' in tf2_launch_options:
                    found_condebug = True
                    self.log.debug(f"Found -condebug in launch options ({tf2_launch_options})")
                    config_mtime: int = int(os.stat(global_config_file_path).st_mtime)
                    self.steam_config_mtimes[global_config_file_path] = config_mtime
                    self.log.debug(f"Added mtime ({config_mtime})")

                    if possible_username:
                        found_usernames.add(possible_username)
        except FileNotFoundError:
            pass
        except PermissionError as error:
            self.log.error(str(error))

    if not found_condebug:
        self.log.error("-condebug not found, telling user", reportable=False)
        del self.log
        # yell at the user to fix their settings
        console_log.no_condebug_warning(self.loc, tf2_is_running)
    else:
        return found_usernames


# adapted from https://www.popmartian.com/tipsntricks/2014/11/20/how-to-lower-case-all-dictionary-keys-in-a-complex-python-dictionary/
def lowercase_keys(mixed_case: Union[dict, list]) -> Union[dict, list]:
    allowed_keys: tuple = ('userlocalconfigstore', 'friends', 'personaname', 'userlocalconfigstore', 'software', 'valve', 'steam', 'apps', '440', 'launchoptions')
    key: str

    for key in list(mixed_case):
        key_lower: str = key.lower()

        if key_lower in allowed_keys:
            mixed_case[key_lower]: Union[dict, list] = mixed_case.pop(key)

            if isinstance(mixed_case[key_lower], dict) or isinstance(mixed_case[key_lower], list):
                mixed_case[key_lower]: Union[dict, list] = lowercase_keys(mixed_case[key_lower])
        else:
            del mixed_case[key]

    return mixed_case
