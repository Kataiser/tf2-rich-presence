# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import traceback

import detect_system_language
import launcher
import logger
import settings
import updater
import welcomer


def launch(welcome_version):
    log_init = logger.Log()
    log_init.info(f"Initializing TF2 Rich Presence {launcher.VERSION}")
    log_init.debug(f"Current log: {log_init.filename}")
    log_init.info(f'Log level: {log_init.log_level}')

    try:
        welcomer.welcome(log_init, welcome_version)
        detect_system_language.detect(log_init)
        updater.check_for_update(log_init, launcher.VERSION, settings.get('request_timeout'))
    except (KeyboardInterrupt, SystemExit):
        raise SystemExit
    except Exception:
        try:
            log_init.critical(traceback.format_exc())
        except NameError:
            pass

        raise


if __name__ == '__main__':
    launch(0)
