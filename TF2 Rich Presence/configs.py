# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import functools
import os
from typing import List, TextIO, Union

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

        # config files are at 'Steam\steamapps\common\Team Fortress 2\tf\cfg'
        try:
            # reads each existing class.cfg
            class_config_file: TextIO = open(os.path.join(exe_location, 'tf', 'cfg', f'{config_filename}.cfg'), 'r+', errors='replace')
            if selected_line not in class_config_file.read():
                # if it doesn't already have the echo line, add it
                class_config_file.write('\n\n' + selected_line)
                classes_not_found.append((f'{config_filename}.cfg', selected_line))
            else:
                classes_found.append((f'{config_filename}.cfg', selected_line))
        except FileNotFoundError:
            # the config file doesn't exist, so create it and add the echo line
            class_config_file = open(os.path.join(exe_location, 'tf', 'cfg', f'{config_filename}.cfg'), 'w')
            log.debug(f"Created {class_config_file.name}")
            class_config_file.write(selected_line)

        # I know a 'with open()' is better but eh
        class_config_file.close()

    log.debug(f"Classes with echo found: {classes_found}")
    log.debug(f"Classes with echo not found: {classes_not_found}")


# reads steams launch options save file to find -condebug
@functools.lru_cache(maxsize=1)
def steam_config_file(log, exe_location: str) -> list:
    log.debug("Looking for -condebug")
    found_condebug: bool = False
    found_usernames: List[str] = []

    user_id_folders: List[str] = next(os.walk(os.path.join(exe_location, 'userdata')))[1]
    log.debug(f"User id folders: {user_id_folders}")
    for user_id_folder in user_id_folders:  # possibly multiple users for the same steam install
        try:
            # 'C:\Program Files (x86)\Steam\userdata\*user id number*\config\localconfig.vdf'
            global_config_file_path: Union[bytes, str] = os.path.join(exe_location, 'userdata', user_id_folder, 'config', 'localconfig.vdf')
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
                possible_username = parsed_lowercase['userlocalconfigstore']['friends']['personaname']
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
        # yell at the user to fix their settings
        del log
        console_log.no_condebug_warning()
    else:
        log.debug(f"Usernames with -condebug: {found_usernames}")
        return found_usernames


# adapted from https://www.popmartian.com/tipsntricks/2014/11/20/how-to-lower-case-all-dictionary-keys-in-a-complex-python-dictionary/
def lowercase_keys(dictionary):
    allowed_keys = ('userlocalconfigstore', 'friends', 'personaname', 'userlocalconfigstore', 'software', 'valve', 'steam', 'apps', '440', 'launchoptions')
    keys_to_remove = []

    for key in dictionary.keys():
        key_lower = key.lower()

        if key_lower in allowed_keys:
            dictionary[key_lower] = dictionary.pop(key)

            if isinstance(dictionary[key_lower], dict) or isinstance(dictionary[key_lower], list):
                dictionary[key_lower] = lowercase_keys(dictionary[key_lower])
        else:
            keys_to_remove.append(key)

    for key in keys_to_remove:
        del dictionary[key]

    return dictionary
