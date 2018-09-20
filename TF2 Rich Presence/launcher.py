import gzip
import json
import os
import sys
import time
import traceback
from typing import Union

sys.path.append(os.path.abspath(os.path.join('resources', 'python', 'packages')))
sys.path.append(os.path.abspath(os.path.join('resources')))
import raven
from raven import Client


def launch():
    try:
        import main
        main.main()
    except (KeyboardInterrupt, SystemExit):
        raise SystemExit
    except Exception as error:
        if sentry_enabled:
            handle_crash_without_log(error, client=sentry_client)
        else:
            handle_crash_without_log(error)


# displays and reports current traceback
def handle_crash_without_log(exception: Exception, client: Union[Client, None] = None):
    if client:
        formatted_exception = traceback.format_exc()
        print(f"\n{formatted_exception}\nTF2 Rich Presence has crashed, and the error message cannot be reported to the developer."
              f"\nConsider opening an issue at https://github.com/Kataiser/tf2-rich-presence/issues."
              f"\nRestarting in 2 seconds...")
        client.captureMessage(str(exception))

    time.sleep(2)


def get_api_key(service):
    if os.path.isdir('resources'):
        apis_path = os.path.join('resources', 'APIs')
    else:
        apis_path = 'APIs'

    with gzip.open(apis_path, 'r') as api_keys_file:
        return json.load(api_keys_file)[service]


sentry_enabled: bool = False

if sentry_enabled:
    # the raven client for Sentry (https://sentry.io/)
    sentry_client = raven.Client(dsn=get_api_key('sentry'),
                                 release='{tf2rpvnum}',
                                 string_max_length=512,
                                 processors=('raven.processors.SanitizePasswordsProcessor',))

if __name__ == '__main__':
    launch()
