# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import functools
import gzip
import json
import os
# note: don't import anything outside of the standard library, in order to avoid unreportable crashes when running the launcher


# read from or write to DB.json (intentionally uncached)
# TODO: might be a good idea to make this a registry thing to avoid permissions problems
def access_db(write: dict = None) -> dict:
    db_path = os.path.join('resources', 'DB.json') if os.path.isdir('resources') else 'DB.json'

    if write:
        with open(db_path, 'w') as db_json:
            db_data = write
            db_json.truncate(0)
            json.dump(db_data, db_json, indent=4)
    else:
        with open(db_path, 'r') as db_json:
            return json.load(db_json)


# get API key from the 'APIs' file
@functools.lru_cache(maxsize=None)
def get_api_key(service):
    if os.path.isdir('resources'):
        apis_path = os.path.join('resources', 'APIs')
    else:
        apis_path = 'APIs'

    with gzip.open(apis_path, 'r') as api_keys_file:
        return json.load(api_keys_file)[service]


# load maps database from maps.json
@functools.lru_cache(maxsize=None)
def load_maps_db() -> dict:
    maps_db_path = os.path.join('resources', 'maps.json') if os.path.isdir('resources') else 'maps.json'
    with open(maps_db_path, 'r') as maps_db:
        return json.load(maps_db)

