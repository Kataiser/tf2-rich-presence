import gzip
import inspect
import json
import os
import zlib
from typing import BinaryIO, List
# note: don't import anything outside of the standard library, in order to avoid unreportable crashes when running the launcher


# generates a short hash string from several source files
def generate_hash() -> str:
    files_to_hash: List[str] = ['main.py', 'console_log.py', 'configs.py', 'custom_maps.py', 'logger.py', 'updater.py', 'launcher.py', 'settings.py', 'detect_system_language.py', 'utils.py',
                                'maps.json', 'localization.json', 'APIs']
    files_to_hash_data = []

    for file_to_hash in files_to_hash:
        file_to_hash_path = os.path.join('resources', file_to_hash) if os.path.isdir('resources') else file_to_hash

        with open(file_to_hash_path, 'rb') as file:
            file_read = file.read()

        if 'launcher' in file_to_hash:
            file_read = file_read.replace(b'{tf2rpvnum}-dev', b'{tf2rpvnum}')

        files_to_hash_data.append(file_read)

    hash_int = zlib.adler32(b'\n'.join(files_to_hash_data))
    hash_hex = hex(hash_int)[2:10].ljust(8, '0')
    return hash_hex


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


def get_caller_filename() -> str:
    frame = inspect.stack()[2]
    module = inspect.getmodule(frame[0])
    caller_filename = os.path.basename(module.__file__)
    return caller_filename


# get API key from the 'APIs' file
def get_api_key(service):
    if os.path.isdir('resources'):
        apis_path = os.path.join('resources', 'APIs')
    else:
        apis_path = 'APIs'

    with gzip.open(apis_path, 'r') as api_keys_file:
        return json.load(api_keys_file)[service]
