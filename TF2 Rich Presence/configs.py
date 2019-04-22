import os
from typing import List, TextIO, Union

import vdf

import main


# allows the console to output 'class selected' on class choose
def class_config_files(log, exe_location: str):
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

            with open(global_config_file_path, 'r+', errors='replace') as global_config_file:
                parsed = vdf.parse(global_config_file)
                log.debug(f"Parsing {global_config_file_path} for -condebug")

            try:
                possible_username = parsed['UserLocalConfigStore']['friends']['PersonaName']
                log.debug(f"Possible username: {possible_username}")
            except KeyError:
                log.error("Couldn't find PersonaName in config")
                possible_username = None

            try:
                tf2_launch_options = parsed['UserLocalConfigStore']['Software']['Valve']['Steam']['Apps']['440']['LaunchOptions']

                if '-condebug' in tf2_launch_options:  # runs if no KeyError in above line
                    found_condebug = True
                    log.debug(f"Found -condebug in launch options ({tf2_launch_options})")

                    if possible_username:
                        found_usernames.append(possible_username)
            except KeyError:
                pass
        except FileNotFoundError:
            pass

    if not found_condebug:
        log.debug("-condebug not found, telling user")
        # yell at the user to fix their settings
        main.no_condebug_warning()
    else:
        log.debug(f"Usernames with -condebug: {found_usernames}")
        return found_usernames
