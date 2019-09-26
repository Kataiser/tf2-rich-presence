# Copyright (C) 2019  Kataiser
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import argparse
import gzip
import importlib
import json
import os
import sys
import time
import traceback
import zlib

sys.path.append(os.path.abspath(os.path.join('resources', 'python', 'packages')))
sys.path.append(os.path.abspath(os.path.join('resources')))
import sentry_sdk


def launch():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--m', default='main', help="The module to launch (main, settings, or updater)")
        args = parser.parse_args()

        old_dir = os.getcwd()
        if os.path.exists('resources\\'):
            os.chdir('resources')
        loaded_module = importlib.import_module(args.m)
        os.chdir(old_dir)

        loaded_module.launch()
    except (KeyboardInterrupt, SystemExit):
        raise SystemExit
    except Exception:
        handle_crash()


# displays and reports current traceback
def handle_crash():
    formatted_exception = traceback.format_exc()

    try:
        print(f"\n{formatted_exception}\nTF2 Rich Presence has crashed, and the error has been reported to the developer."
              f"\n(Consider opening an issue at https://github.com/Kataiser/tf2-rich-presence/issues)"
              f"\nRestarting in 2 seconds...\n")

        if not exc_already_reported(formatted_exception):
            sentry_sdk.capture_exception()
    except Exception:
        # Sentry has failed us :(
        print(f"\n{formatted_exception}\nTF2 Rich Presence has crashed, and the error can't be reported to the developer."
              f"\n(Consider opening an issue at https://github.com/Kataiser/tf2-rich-presence/issues)"
              f"\nRestarting in 2 seconds...\n")

    time.sleep(2)
    # should restart via the bat/exe now


# get API key from the 'APIs' file
def get_api_key(service):
    if os.path.isdir('resources'):
        apis_path = os.path.join('resources', 'APIs')
    else:
        apis_path = 'APIs'

    with gzip.open(apis_path, 'r') as api_keys_file:
        return json.load(api_keys_file)[service]


# don't report the same traceback twice
def exc_already_reported(tb: str):
    try:
        tb_hash = str(zlib.crc32(tb.encode('utf-8', errors='replace')))  # technically not a hash but w/e

        db_path = os.path.join('resources', 'DB.json') if os.path.isdir('resources') else 'DB.json'
        with open(db_path, 'r+') as db_json:
            db_data = json.load(db_json)

            if tb_hash in db_data['tb_hashes']:
                return True
            else:
                db_data['tb_hashes'].append(tb_hash)
                db_json.seek(0)
                db_json.truncate(0)
                json.dump(db_data, db_json, indent=4)
                return False
    except Exception:
        return False


if __name__ == '__main__':
    # set up Sentry (https://sentry.io/)
    sentry_sdk.init(dsn=get_api_key('sentry'), release='{tf2rpvnum}', attach_stacktrace=True)

    launch()
