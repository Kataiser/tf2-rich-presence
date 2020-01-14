# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import ctypes

import colorama

import localization
import settings
import logger


def welcome(log: logger.Log, message_version):
    # localize the window title
    loc = localization.Localizer(language=settings.get('language'))
    ctypes.windll.kernel32.SetConsoleTitleW(loc.text("TF2 Rich Presence ({0})").format('{tf2rpvnum}'))
    log.debug(f"Welcoming with message version {message_version}")

    print(colorama.Style.BRIGHT, end='')
    print(loc.text("TF2 Rich Presence ({0}) by Kataiser").format('{tf2rpvnum}'))
    print(colorama.Style.RESET_ALL, end='')
    print("https://github.com/Kataiser/tf2-rich-presence\n")
    print(colorama.Style.BRIGHT, end='')

    if message_version == '0':
        print("{}\n".format(loc.text("Launching Team Fortress 2 with Rich Presence enabled...")))
    elif message_version == '1':
        print("{}\n".format(loc.text("Launching TF2 with Rich Presence alongside Team Fortress 2...")))
    print(colorama.Style.RESET_ALL, end='')


if __name__ == '__main__':
    log = logger.Log()
    welcome(log, 0)
