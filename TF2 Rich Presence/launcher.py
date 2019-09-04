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
from typing import Union

try:
    sys.path.append(os.path.abspath(os.path.join('resources', 'python', 'packages')))
    sys.path.append(os.path.abspath(os.path.join('resources')))
    import raven
    from raven import Client
except Exception:
    raven = None
    Client = None


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
        if sentry_enabled and raven:
            handle_crash_without_log(client=sentry_client_launcher)
        else:
            handle_crash_without_log()


# displays and reports current traceback
def handle_crash_without_log(client: Union[Client, None] = None):
    formatted_exception = traceback.format_exc()

    if client:
        print(f"\n{formatted_exception}\nTF2 Rich Presence has crashed, and the error has been reported to the developer."
              f"\n(Consider opening an issue at https://github.com/Kataiser/tf2-rich-presence/issues)"
              f"\nRestarting in 2 seconds...\n")

        if not exc_already_reported(formatted_exception):
            client.captureMessage(formatted_exception)
    else:
        print(f"\n{formatted_exception}\nTF2 Rich Presence has crashed, and the error can't be reported to the developer."
              f"\n(Consider opening an issue at https://github.com/Kataiser/tf2-rich-presence/issues)"
              f"\nRestarting in 2 seconds...\n")

    time.sleep(2)


# get API key from the 'APIs' file
def get_api_key(service):
    if os.path.isdir('resources'):
        apis_path = os.path.join('resources', 'APIs')
    else:
        apis_path = 'APIs'

    with gzip.open(apis_path, 'r') as api_keys_file:
        return json.load(api_keys_file)[service]


# don't report the same error twice
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


sentry_enabled: bool = True

if __name__ == '__main__':
    if sentry_enabled:
        # the raven client for Sentry (https://sentry.io/)
        sentry_client_launcher = raven.Client(dsn=get_api_key('sentry'),
                                              release='{tf2rpvnum}',
                                              string_max_length=512,
                                              processors=('raven.processors.SanitizePasswordsProcessor',))

    launch()
