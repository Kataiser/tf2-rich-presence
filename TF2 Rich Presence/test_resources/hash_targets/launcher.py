import time
import traceback
from typing import Union

import raven
from raven import Client


def launch():
    try:
        import main
        main.main()
    except Exception as error:
        if sentry_enabled:
            handle_crash_without_log(error, client=sentry_client)
        else:
            handle_crash_without_log(error)


# displays and reports current traceback
def handle_crash_without_log(exception: Exception, client: Union[Client, None] = None):
    if client:
        formatted_exception = traceback.format_exc()
        print(f"TF2 Rich Presence has crashed, the error should now be reported to the developer.\nHere's the full error message if you're interested.\n{formatted_exception}")
        client.captureMessage(str(exception))

    time.sleep(5)


sentry_enabled: bool = False

if sentry_enabled:
    # the raven client for Sentry (https://sentry.io/)
    sentry_client = raven.Client(dsn='https://de781ce2454f458eafab1992630bc100:ce637f5993b14663a0840cd9f98a714a@sentry.io/1245944',
                                 release='{tf2rpvnum}',
                                 string_max_length=512,
                                 processors=('raven.processors.SanitizePasswordsProcessor',))

if __name__ == '__main__':
    launch()
