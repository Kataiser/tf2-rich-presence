# Copyright (C) 2018-2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

# note: don't import anything outside of the standard library, in order to avoid unreportable crashes when running the launcher
import functools
import gzip
import json
import os
from typing import Dict, Optional, Union


# read from or write to DB.json (intentionally uncached)
# TODO: have this be placed in AppData\Roaming and include settings
def access_db(write: dict = None) -> Optional[Dict[str, Union[bool, list, str]]]:
    db_path: str = os.path.join('resources', 'DB.json') if os.path.isdir('resources') else 'DB.json'
    default_db: dict = {'tb_hashes': [],
                        'error_hashes': [],
                        'has_asked_language': False,
                        'missing_localization': [],
                        'available_version': '',
                        'gui_position': [0, 0]}

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
@functools.cache
def get_api_key(service: str) -> str:
    # just some very basic obfuscation
    data: bytes = b'\x1f\x8b\x08\x00bl\xfa_\x02\xff-\x8eK\x0e\xc20\x0c\x05\xef\x925\xa2q\xfc\x12\xdb]q\x954\x1f\xd1\rEm7\x08qw"\xc1\xfa\xe9\xcd\xcc\xdb\xd5\xf5(\xdb^\xdd\xec\x10\x8c\xd5' \
                  b'\x08,1\xb1\xc0\x93\xb8\x8b;\xda\xe3\xdc_c\xbd\x9f\xe7\xf3\x98\xa7\xa96Q*- \xa2#j\xcb=/d\x16\x12\xfb\xa5\x90\xf7si\xe3\xdd\xa3\x19/\x84\x948{\x85/\xd5\xbai\x16B\xbe\xfd' \
                  b'\x90\xd7u\x9bhP\x0c\x18\x9a\x7fE\x18"\x01\xe9\x08\x01\x07\x92\xa0\x91\x84\xdc\xe7\x0b)\x81\xb1\xd4\xa7\x00\x00\x00'
    return json.loads(gzip.decompress(data))[service]
