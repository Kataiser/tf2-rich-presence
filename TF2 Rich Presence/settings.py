# Copyright (C) 2018-2022 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import functools
import json
import winreg
from typing import Optional, Union

import ujson

import logger


# access a setting from any file, with a string that is the same as the variable name (cached, so settings changes won't be rechecked right away)
# TODO: access settings as a class with type hinted members
@functools.cache
def get(setting: str) -> Union[str, int, bool]:
    try:
        return access_registry()[setting]
    except KeyError:
        return get_setting_default(setting)


# either reads the settings key and returns it as a dict, or if a dict is provided, saves it
# note that settings are saved as JSON in a single string key
# could do this as a file in AppData\Roaming\TF2 Rich Presence, but it would likely be slower for no benefit AFAIK
def access_registry(save: Optional[dict] = None) -> Optional[dict]:
    reg_key: winreg.HKEYType = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\TF2 Rich Presence')

    try:
        reg_key_data: dict = ujson.loads(winreg.QueryValue(reg_key, 'Settings'))
    except FileNotFoundError:  # means that the key hasn't been initialized
        # assume no key means default settings. might not be true but whatever
        default_settings: dict = defaults()
        winreg.SetValue(reg_key, 'Settings', winreg.REG_SZ, json.dumps(default_settings, separators=(',', ':')))
        reg_key_data: dict = default_settings

    if save:
        winreg.SetValue(reg_key, 'Settings', winreg.REG_SZ, json.dumps(save, separators=(',', ':')))
        reg_key.Close()
        get.cache_clear()
        logger.Log.log_level_allowed.cache_clear()
    else:
        reg_key.Close()
        return reg_key_data


# changes a single setting
def change(setting: str, value: Union[str, int, bool, float]):
    current_settings = access_registry()
    current_settings[setting] = value
    access_registry(save=current_settings)


# either gets a settings default, or if return_dict, returns all defaults as a dict
def get_setting_default(setting: str = '', return_all: bool = False) -> Union[str, int, bool, dict]:
    default_settings = {'sentry_level': 'All errors',
                        'wait_time': 1,
                        'wait_time_slow': 5,
                        'check_updates': True,
                        'request_timeout': 10,
                        'hide_queued_gamemode': False,
                        'log_level': 'Debug',
                        'language': 'English',
                        'top_line': 'Player count',
                        'bottom_line': 'Time on map',
                        'gui_scale': 100,
                        'drawing_gamemodes': False,
                        'preserve_window_pos': True}

    if return_all:
        return default_settings
    else:
        return default_settings[setting]


# slightly less ugly
def defaults() -> dict:
    return get_setting_default(return_all=True)


# find settings that are different between two settings dicts
def compare_settings(before: dict, after: dict) -> dict:
    return {k: after[k] for k in before if before[k] != after[k]}


# fixes settings that are missing or deprecated
def fix_settings(log):
    default: dict = defaults()
    current: dict = access_registry()
    added: dict = {}
    removed: dict = {}
    made_fixes: bool = False

    for default_setting in default:
        if default_setting not in current:
            current[default_setting] = default[default_setting]
            added[default_setting] = default[default_setting]
            made_fixes = True

    for current_setting in list(current):
        if current_setting not in default:
            removed[current_setting] = current[current_setting]
            del current[current_setting]
            made_fixes = True

        access_registry(save=current)

    if made_fixes:
        log.error(f"Fixed settings: added {added}, removed {removed}")


if __name__ == '__main__':
    for setting in defaults():
        print(f"{setting}: {get(setting)}")
