"""Launcher for TF2 Rich Presence"""

# TF2 Rich Presence
# https://github.com/Kataiser/tf2-rich-presence
#
# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import importlib
import os
import sys
import time
import traceback
import zlib

sys.path.append(os.path.abspath(os.path.join('resources', 'python', 'packages')))
sys.path.append(os.path.abspath(os.path.join('resources')))
import colorama
import sentry_sdk

import utils


def launch():
    try:
        colorama.init()

        allowed_modules = ('init', 'main', 'settings')
        parser = argparse.ArgumentParser()
        parser.add_argument('--m', default='main', help=f"The module to launch {allowed_modules}")
        parser.add_argument('--welcome_version', default='0', help="Which version of the welcome message to use (0 or 1)")
        args = parser.parse_args()

        if args.m not in allowed_modules:
            raise SystemError(f"--m must be in {allowed_modules}")

        old_dir = os.getcwd()
        if os.path.exists('resources\\'):
            os.chdir('resources')
        loaded_module = importlib.import_module(args.m)
        os.chdir(old_dir)

        if args.m == 'init':
            loaded_module.launch(args.welcome_version)
        else:
            loaded_module.launch()
    except (KeyboardInterrupt, SystemExit):
        raise SystemExit
    except Exception:
        handle_crash()


# displays and reports current traceback
def handle_crash():
    print(colorama.Fore.LIGHTRED_EX, end='')
    formatted_exception = traceback.format_exc()

    try:
        if not exc_already_reported(formatted_exception):
            sentry_sdk.capture_exception()
    except Exception:
        # Sentry has failed us :(
        print(f"\n{formatted_exception}{colorama.Style.RESET_ALL}{colorama.Style.BRIGHT}")
        print(f"TF2 Rich Presence has crashed, and the error can't be reported to the developer."
              f"\n{colorama.Style.RESET_ALL}(Consider opening an issue at https://github.com/Kataiser/tf2-rich-presence/issues)"
              f"\n{colorama.Style.BRIGHT}Restarting in 5 seconds...\n")
    else:
        print(f"\n{formatted_exception}{colorama.Style.RESET_ALL}{colorama.Style.BRIGHT}")
        print(f"TF2 Rich Presence has crashed, and the error has been reported to the developer."
              f"\n{colorama.Style.RESET_ALL}(Consider opening an issue at https://github.com/Kataiser/tf2-rich-presence/issues)"
              f"\n{colorama.Style.BRIGHT}Restarting in 5 seconds...\n")

    time.sleep(5)
    # should restart via the bat/exe now


# don't report the same exception twice
def exc_already_reported(tb: str):
    try:
        tb_hash: str = str(zlib.crc32(tb.encode('utf-8', errors='replace')))  # technically not a hash but w/e

        db = utils.access_db()
        if tb_hash in db['tb_hashes']:
            return True
        else:
            db['tb_hashes'].append(tb_hash)
            utils.access_db(db)
            return False
    except Exception:
        return False


DEBUG = True
VERSION = '{tf2rpvnum}'

if __name__ == '__main__':
    # set up Sentry (https://sentry.io/)
    sentry_sdk.init(dsn=utils.get_api_key('sentry'), release=VERSION)

    launch()
