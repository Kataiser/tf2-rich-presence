# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import datetime
import traceback
from typing import Union

from colorama import Fore

import detect_system_language
import launcher
import logger
import settings
import updater
import welcomer


def launch(welcome_version):
    try:
        log_init = logger.Log()
        log_init.info(f"Initializing TF2 Rich Presence {launcher.VERSION}")
        log_init.debug(f"Current log: {log_init.filename}")
        log_init.info(f"Log level: {log_init.log_level}")

        welcomer.welcome(log_init, welcome_version)

        default_settings: dict = settings.get_setting_default(return_all=True)
        current_settings: dict = settings.access_registry()
        missing_settings: dict = settings.fix_missing_settings(default_settings, current_settings)
        if missing_settings:
            log_init.error(f"Missing setting(s), defaults reverted: {missing_settings}")

        detect_system_language.detect(log_init)
        updater.check_for_update(log_init, launcher.VERSION, float(settings.get('request_timeout')))
        holidays(log_init)
    except (KeyboardInterrupt, SystemExit):
        raise SystemExit
    except Exception:
        try:
            log_init.critical(traceback.format_exc())
        except NameError:
            pass

        raise


# cause why not
def holidays(log: logger.Log):
    now: datetime.datetime = datetime.datetime.now()
    holiday_text: Union[str, None] = None

    if now.month == 1 and now.day == 1:
        holiday_text = "Happy New Years!"
    elif now.month == 4 and now.day == 1:
        age = now.year - 2018
        ordinal = 'tsnrhtdd'[age % 5 * (age % 100 ^ 15 > 4 > age % 10)::4]  # oh
        holiday_text = f"It's TF2 Rich Presence's {age}{ordinal} birthday today! (Yes, April 1st, seriously)"
    elif now.month == 12 and now.day == 25:
        holiday_text = "Merry Christmas!"

    if holiday_text:
        log.info(f"Today is {now.year}/{now.month}/{now.day}: so the holiday text is \"{holiday_text}\"")
        print(f"{Fore.LIGHTGREEN_EX}{holiday_text}{Fore.RESET}\n")


if __name__ == '__main__':
    launch(0)
