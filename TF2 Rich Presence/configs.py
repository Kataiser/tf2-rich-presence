import os
from typing import List, TextIO, Union

import logger as log
import main


# allows the console to output 'class selected' on class choose
def class_config_files(exe_location: str):
    log.debug(f"Reading (and possibly modifying) class configs at {exe_location}")
    tf2_classes: List[str] = ['Scout', 'Soldier', 'Pyro', 'Demoman', 'Heavy', 'Engineer', 'Medic', 'Sniper', 'Spy']

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
                log.debug(f"'{selected_line}' not found in {class_config_file.name}, adding it")
                class_config_file.write('\n\n' + selected_line)
            else:
                log.debug(f"{selected_line} found in {class_config_file.name}")
        except FileNotFoundError:
            # the config file doesn't exist, so create it and add the echo line
            class_config_file = open(os.path.join(exe_location, 'tf', 'cfg', f'{config_filename}.cfg'), 'w')
            log.debug(f"Created {class_config_file.name}")
            class_config_file.write(selected_line)

        # I know a 'with open()' is better but eh
        class_config_file.close()


# reads steams launch options save file to find -condebug
def steam_config_file(exe_location: str) -> list:
    log.debug("Looking for -condebug")
    found_condebug: bool = False
    found_usernames: List[str] = []

    user_id_folders: List[str] = next(os.walk(exe_location + 'userdata'))[1]
    log.debug(f"User id folders: {user_id_folders}")
    for user_id_folder in user_id_folders:  # possibly multiple users for the same steam install
        try:
            # 'C:\Program Files (x86)\Steam\userdata\*user id number*\config\localconfig.vdf'
            global_config_file_path: Union[bytes, str] = os.path.join(exe_location, 'userdata', user_id_folder, 'config', 'localconfig.vdf')
            with open(global_config_file_path, 'r+', errors='replace') as global_config_file:
                lines: List[str] = global_config_file.readlines()
                log.debug(f"Reading {global_config_file_path} ({len(lines)} lines) for -condebug")
                tf2_line_num: int = 0

                for line in enumerate(lines):
                    if line[1].startswith('\t\t"PersonaName"\t\t'):
                        possible_username: str = line[1].replace('\t', '')[14:-2]
                        log.debug(f"Possible username: {possible_username}")

                    if line[1] == '\t\t\t\t\t"440"\n':  # looks for tf2's ID and finds the line number
                        log.debug(f"Found TF2's ID at line {line[0]}")
                        tf2_line_num = line[0]

                for line_offset in range(1, 21):
                    launchoptions_line: str = lines[tf2_line_num + line_offset]
                    if 'LaunchOptions' in launchoptions_line and'-condebug' in launchoptions_line:
                        # oh also this might be slow to update
                        found_condebug = True
                        log.debug(f"Found -condebug with offset {line_offset} in line: {launchoptions_line[:-1]}")
                        found_usernames.append(possible_username)
        except FileNotFoundError:
            pass
        except IndexError:
            pass

    if not found_condebug:
        log.debug("-condebug not found, telling user")
        # yell at the user to fix their settings
        main.no_condebug_warning()
    else:
        log.debug(f"Usernames with -condebug: {found_usernames}")
        return found_usernames
