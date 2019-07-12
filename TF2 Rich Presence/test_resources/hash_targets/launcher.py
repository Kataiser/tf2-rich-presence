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


def launch():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('module')
        args = parser.parse_args()

        old_dir = os.getcwd()
        os.chdir('resources')
        loaded_module = importlib.import_module(args.module)
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

        if os.path.exists('tb_hashes.txt'):
            tb_hashes_path = 'tb_hashes.txt'
        else:
            tb_hashes_path = os.path.join('resources', 'tb_hashes.txt')

        with open(tb_hashes_path, 'r') as tb_hashes_txt:
            reported_hashes = tb_hashes_txt.readlines()

        if tb_hash in reported_hashes:
            return True
        else:
            with open(tb_hashes_path, 'a') as tb_hashes_txt_a:
                tb_hashes_txt_a.write(f'{tb_hash}\n')
            return False
    except Exception:
        return False


sentry_enabled: bool = True

if sentry_enabled:
    # the raven client for Sentry (https://sentry.io/)
    sentry_client_launcher = raven.Client(dsn=get_api_key('sentry'),
                                          release='v1.8',
                                          string_max_length=512,
                                          processors=('raven.processors.SanitizePasswordsProcessor',))

if __name__ == '__main__':
    launch()
