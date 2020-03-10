# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import functools
import os
from typing import List, Union

import vdf

import console_log


# allows the console to output 'class selected' on class choose
def class_config_files(log, exe_location: str):
    log.debug(f"Reading (and possibly modifying) class configs at {exe_location}")
    tf2_classes: List[str] = ['Scout', 'Soldier', 'Pyro', 'Demoman', 'Heavy', 'Engineer', 'Medic', 'Sniper', 'Spy']
    classes_found = []
    classes_not_found = []

    for tf2_class in tf2_classes:
        # 'echo' means 'output to console' in source-speak
        selected_line: str = f'echo "{tf2_class} selected"'

        config_filename: str = tf2_class.lower().replace('heavy', 'heavyweapons')  # valve why
        config_path = os.path.join(exe_location, 'tf', 'cfg', f'{config_filename}.cfg')
        # config files are at 'Steam\steamapps\common\Team Fortress 2\tf\cfg'

        if os.path.isfile(config_path):
            # reads each existing class.cfg
            with open(config_path, 'r+', errors='ignore') as class_config_file:
                if selected_line not in class_config_file.read():
                    # if it doesn't already have the echo line, add it
                    class_config_file.write('\n\n' + selected_line)
                    classes_not_found.append((f'{config_filename}.cfg', selected_line))
                else:
                    classes_found.append((f'{config_filename}.cfg', selected_line))
        else:
            # the config file doesn't exist, so create it and add the echo line
            with open(config_path, 'w') as class_config_file:
                class_config_file.write(selected_line)

            log.debug(f"Created {class_config_file.name}")

    log.debug(f"Classes with echo found: {classes_found}")
    log.debug(f"Classes with echo not found: {classes_not_found}")


# reads steams launch options save file to find -condebug
@functools.lru_cache(maxsize=1)
def steam_config_file(log, exe_location: str, tf2_is_running: bool = False) -> list:
    log.debug("Looking for -condebug")
    found_condebug: bool = False
    found_usernames: List[str] = []

    user_id_folders: List[str] = next(os.walk(os.path.join(exe_location, 'userdata')))[1]
    log.debug(f"User id folders: {user_id_folders}")
    for user_id_folder in user_id_folders:  # possibly multiple users for the same steam install
        try:
            # 'C:\Program Files (x86)\Steam\userdata\*user id number*\config\localconfig.vdf'
            global_config_file_path: str = os.path.join(exe_location, 'userdata', user_id_folder, 'config', 'localconfig.vdf')
            log.debug(f"Reading {global_config_file_path}")

            with open(global_config_file_path, 'r+', errors='replace') as global_config_file:
                global_config_file_read = global_config_file.read()

                if '-condebug' in global_config_file_read and '"440"' in global_config_file_read:
                    log.debug(f"-condebug and \"440\" found, parsing file ({len(global_config_file_read)} bytes)")

                    parsed = vdf.loads(global_config_file_read)
                    log.debug(f"VDF parse complete ({len(parsed['UserLocalConfigStore'])} keys)")
                    parsed_lowercase = lowercase_keys(parsed)
                    log.debug(f"Lowercase complete ({len(parsed['userlocalconfigstore'])} keys)")
                else:
                    continue

            try:
                possible_username: Union[str, None] = parsed_lowercase['userlocalconfigstore']['friends']['personaname']
                log.debug(f"Possible username: {possible_username}")
            except KeyError:
                log.error("Couldn't find PersonaName in config")
                possible_username = None

            try:
                tf2_launch_options = parsed_lowercase['userlocalconfigstore']['software']['valve']['steam']['apps']['440']['launchoptions']

                if '-condebug' in tf2_launch_options:  # runs if no KeyError in above line
                    found_condebug = True
                    log.debug(f"Found -condebug in launch options ({tf2_launch_options})")

                    if possible_username:
                        found_usernames.append(possible_username)
            except KeyError:
                pass  # looks like -condebug was in some other game
        except FileNotFoundError:
            pass
        except PermissionError as error:
            log.error(error)

    if not found_condebug:
        log.debug("-condebug not found, telling user")
        del log
        # yell at the user to fix their settings
        console_log.no_condebug_warning(tf2_is_running)
    else:
        log.debug(f"Usernames with -condebug: {found_usernames}")
        return found_usernames


# adapted from https://www.popmartian.com/tipsntricks/2014/11/20/how-to-lower-case-all-dictionary-keys-in-a-complex-python-dictionary/
def lowercase_keys(mixed_case: Union[dict, list]) -> Union[dict, list]:
    allowed_keys: tuple = ('userlocalconfigstore', 'friends', 'personaname', 'userlocalconfigstore', 'software', 'valve', 'steam', 'apps', '440', 'launchoptions')
    keys_to_remove: list = []
    key: str

    for key in mixed_case.keys():
        key_lower: str = key.lower()

        if key_lower in allowed_keys:
            mixed_case[key_lower]: Union[dict, list] = mixed_case.pop(key)

            if isinstance(mixed_case[key_lower], dict) or isinstance(mixed_case[key_lower], list):
                mixed_case[key_lower]: Union[dict, list] = lowercase_keys(mixed_case[key_lower])
        else:
            keys_to_remove.append(key)

    for key in keys_to_remove:
        del mixed_case[key]

    return mixed_case
