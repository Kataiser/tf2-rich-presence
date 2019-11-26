# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import argparse
import ctypes
import os
import sys

sys.path.append(os.path.abspath(os.path.join('resources', 'python', 'packages')))
sys.path.append(os.path.abspath(os.path.join('resources')))
import colorama

import localization
import settings


def main():
    ctypes.windll.kernel32.SetConsoleTitleW("TF2 Rich Presence ({tf2rpvnum})")
    loc = localization.Localizer(language=settings.get('language'))
    ctypes.windll.kernel32.SetConsoleTitleW(loc.text("TF2 Rich Presence ({0})").format('{tf2rpvnum}'))  # again, but localized

    colorama.init()
    print(colorama.Style.BRIGHT, end='')
    print(loc.text("TF2 Rich Presence ({0}) by Kataiser").format('{tf2rpvnum}'))
    print(colorama.Style.RESET_ALL, end='')
    print("https://github.com/Kataiser/tf2-rich-presence\n")
    print(colorama.Style.BRIGHT, end='')

    parser = argparse.ArgumentParser()
    parser.add_argument('--v', default='1', help="Which version of the message to use (1 or 2)")
    message_version = parser.parse_args().v

    if message_version == '1':
        print("{}\n".format(loc.text("Launching Team Fortress 2 with Rich Presence enabled...")))
    elif message_version == '2':
        print("{}\n".format(loc.text("Launching TF2 with Rich Presence alongside Team Fortress 2...")))


if __name__ == '__main__':
    main()
