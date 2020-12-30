# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

# note: don't import anything outside of the standard library, in order to avoid unreportable crashes when running the launcher
import functools
import gzip
import json
import os
import time
import tkinter as tk
import traceback
from typing import Dict, Union


# read from or write to DB.json (intentionally uncached)
# TODO: have this be placed in AppData\Roaming and include settings
def access_db(write: dict = None) -> Dict[str, Union[dict, bool, list]]:
    db_path: str = os.path.join('resources', 'DB.json') if os.path.isdir('resources') else 'DB.json'
    default_db: dict = {'custom_maps': {},
                        'tb_hashes': [],
                        'error_hashes': [],
                        'has_asked_language': False,
                        'available_version': {'exists': False, 'tag': '', 'url': ''},
                        'missing_localization': []}

    if not os.path.isfile(db_path):
        open(db_path, 'w').close()

    if write:
        try:
            with open(db_path, 'w', encoding='UTF8') as db_json:
                db_data: dict = write
                db_json.truncate(0)
                json.dump(db_data, db_json, indent=4, ensure_ascii=False)
        except (UnicodeEncodeError, PermissionError):
            pass
        except OSError as error:
            if str(error) == 'No space left on device':
                pass
            else:
                raise
    else:
        try:
            with open(db_path, 'r', encoding='UTF8') as db_json:
                return json.load(db_json)
        except json.JSONDecodeError:
            access_db(write=default_db)
            return default_db


# get API key from the 'APIs' file
@functools.lru_cache(maxsize=None)
def get_api_key(service: str) -> str:
    # just some very basic obfuscation
    data: bytes = b'\x1f\x8b\x08\x00K\xc5\xec_\x02\xff%\xccI\x0e\xc20\x0c@\xd1\xabT^#b\xc7\xce\xe0\xac\xb8JF\xd1\rEM7\x08qw\x8aX\x7f\xfd\xf7\x86\xb6\xce\xba\xed\r\xd2\x02b\x95\xa3\x92pp\x9e' \
                  b'\x83 \x05\xb8,0\xfb\xe3\xd8_\xbf~?\x8e\xe7L\xc6\xb4\x1e"\xd5n\xc5\xc9\x10\x17{\x1e\xb9\x90\xaa\xf5\x8c\xa5\x12b\xaa\xfd\xfc\x87S\xe5B\xe2=g\x8c\x82\xb5\xe9\xd0\x98\x03I' \
                  b'\xbe\xfd\xcd\xeb\xba\x19:\x15\x15\x81\xcf\x17Q\x16\x89\xda\x8a\x00\x00\x00'
    return json.loads(gzip.decompress(data))[service]


# generate text that displays the difference between now and old_time
def generate_delta(loc, old_time: Union[float, None]) -> str:
    if old_time:
        time_diff: int = round(time.time() - old_time)

        if time_diff > 86400:
            divided_diff: float = round(time_diff / 86400, 1)

            if divided_diff == 1:
                return f" (+{divided_diff} {loc.text('day')})"
            else:
                return f" (+{divided_diff} {loc.text('days')})"
        elif time_diff > 3600:
            divided_diff = round(time_diff / 3600, 1)

            if divided_diff == 1:
                return f" (+{divided_diff} {loc.text('hour')})"
            else:
                return f" (+{divided_diff} {loc.text('hours')})"
        elif time_diff > 60:
            divided_diff = round(time_diff / 60, 1)

            if divided_diff == 1:
                return f" (+{divided_diff} {loc.text('minute')})"
            else:
                return f" (+{divided_diff} {loc.text('minutes')})"
        else:
            if time_diff == 1:
                return f" (+{time_diff} {loc.text('second')})"
            else:
                return f" (+{time_diff} {loc.text('seconds')})"
    else:
        return ""


# doesn't work if launching from Pycharm for some reason
def set_window_icon(log, window: tk.Tk, wrench: bool):
    filename = 'tf2_logo_blurple_wrench.ico' if wrench else 'tf2_logo_blurple.ico'

    try:
        if os.path.isdir('resources'):
            window.iconbitmap(default=os.path.join('resources', filename))
        else:
            window.iconbitmap(default=filename)
    except tk.TclError:
        log.error(traceback.format_exc())
