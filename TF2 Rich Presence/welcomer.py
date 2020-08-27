# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import ctypes

from colorama import Style

import launcher
import localization
import logger
import settings


def welcome(log: logger.Log, loc: localization.Localizer, message_version: str):
    # set the window title
    ctypes.windll.kernel32.SetConsoleTitleW(loc.text("TF2 Rich Presence ({0})").format(launcher.VERSION))
    log.debug(f"Welcoming with message version {message_version}")

    print(Style.BRIGHT, end='')
    print(loc.text("TF2 Rich Presence ({0}) by Kataiser").format(launcher.VERSION))
    print(Style.RESET_ALL, end='')
    print("https://github.com/Kataiser/tf2-rich-presence\n")
    print(Style.BRIGHT, end='')

    if message_version == '0':
        print("{}\n".format(loc.text("Launching Team Fortress 2 with Rich Presence enabled...")))
    elif message_version == '1':
        print("{}\n".format(loc.text("Launching TF2 with Rich Presence alongside Team Fortress 2...")))
    print(Style.RESET_ALL, end='')


if __name__ == '__main__':
    welcome(logger.Log(), localization.Localizer(language=settings.get('language')), '0')
