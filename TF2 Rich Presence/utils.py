# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

# note: don't import anything outside of the standard library, in order to avoid unreportable crashes when running the launcher
import functools
import gzip
import json
import os
import time
from typing import Dict, List, Union


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
        with open(db_path, 'w', encoding='UTF8') as db_json:
            db_data: dict = write
            db_json.truncate(0)
            json.dump(db_data, db_json, indent=4, ensure_ascii=False)
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
    if os.path.isdir('resources'):
        apis_path = os.path.join('resources', 'APIs')
    else:
        apis_path = 'APIs'

    with gzip.open(apis_path, 'r') as api_keys_file:
        return json.load(api_keys_file)[service]


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


# load maps database from maps.json
@functools.lru_cache(maxsize=None)
def load_maps_db() -> Dict[str, Dict[str, List[str]]]:
    maps_db_path = os.path.join('resources', 'maps.json') if os.path.isdir('resources') else 'maps.json'

    if os.path.isfile(maps_db_path):
        with open(maps_db_path, 'r') as maps_db:
            return json.load(maps_db)
    else:
        return {'official': {}, 'common_custom': {}, 'creators_tf': {}}
