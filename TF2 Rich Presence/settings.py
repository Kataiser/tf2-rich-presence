# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import functools
import json
import winreg
from typing import Union


# access a setting from any file, with a string that is the same as the variable name (cached, so settings changes won't be rechecked right away)
# TODO: access settings as a class with type hinted public members
@functools.lru_cache(maxsize=None)
def get(setting: str) -> Union[str, int, bool]:
    try:
        return access_registry()[setting]
    except KeyError:
        return get_setting_default(setting)


# either reads the settings key and returns it as a dict, or if a dict is provided, saves it
# note that settings are saved as JSON in a single string key
def access_registry(save: Union[dict, None] = None) -> dict:
    reg_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\TF2 Rich Presence')

    try:
        reg_key_data = json.loads(winreg.QueryValue(reg_key, 'Settings'))
    except FileNotFoundError:  # means that the key hasn't been initialized
        # assume no key means default settings. might not be true but whatever
        default_settings = defaults()
        winreg.SetValue(reg_key, 'Settings', winreg.REG_SZ, json.dumps(default_settings, separators=(',', ':')))
        reg_key_data = default_settings

    if save:
        winreg.SetValue(reg_key, 'Settings', winreg.REG_SZ, json.dumps(save, separators=(',', ':')))
    else:
        return reg_key_data


# either gets a settings default, or if return_dict, returns all defaults as a dict
def get_setting_default(setting: str = '', return_all: bool = False) -> Union[str, int, bool, dict]:
    defaults = {'sentry_level': 'All errors',
                'wait_time': 2,
                'wait_time_slow': 5,
                'map_invalidation_hours': 24,
                'check_updates': True,
                'request_timeout': 5,
                'hide_queued_gamemode': False,
                'log_level': 'Debug',
                'console_scan_kb': 1024,
                'class_pic_type': 'Icon',
                'language': 'English',
                'second_line': 'Player count',
                'trim_console_log': True}

    if return_all:
        return defaults
    else:
        return defaults[setting]


# slightly less ugly
def defaults() -> dict:
    return get_setting_default(return_all=True)


# find settings that are different between two settings dicts
def compare_settings(before: dict, after: dict) -> dict:
    return {k: after[k] for k in before if before[k] != after[k]}


# fixes settings that aren't in "current" from "default"
def fix_missing_settings(log):
    default: dict = defaults()
    current: dict = access_registry()
    missing: dict = {}

    if len(default) != len(current):
        for default_setting in default:
            if default_setting not in current:
                missing[default_setting] = default[default_setting]
                current[default_setting] = default[default_setting]

        access_registry(save=current)

    if missing:
        log.error(f"Missing setting(s), defaults added to current: {missing}")


if __name__ == '__main__':
    for setting in defaults():
        print(f"{setting}: {get(setting)}")
