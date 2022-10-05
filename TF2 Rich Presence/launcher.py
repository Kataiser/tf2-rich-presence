"""Launcher for TF2 Rich Presence"""

# TF2 Rich Presence
# https://github.com/Kataiser/tf2-rich-presence
#
# Copyright (C) 2018-2022 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
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

import getpass
import os
import socket
import sys
import traceback
import zlib
from tkinter import messagebox

sys.path.append(os.path.abspath('resources'))
sys.path.append(os.path.abspath(os.path.join('resources', 'packages')))
import sentry_sdk

import utils

__author__ = "Kataiser"
__copyright__ = "Copyright (C) 2018-2022 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors"
__license__ = "GPL-3.0"
__email__ = "Mecharon1.gm@gmail.com"


def main(launch: bool = True):
    try:
        import settings
        enable_sentry: bool = settings.get('sentry_level') != 'Never'
    except Exception:
        enable_sentry = True  # will almost certainly crash later anyway if this happens

    try:
        if enable_sentry:
            # set up Sentry (https://sentry.io/)
            sentry_sdk.init(dsn=utils.get_api_key('sentry'),
                            release=VERSION,
                            attach_stacktrace=True,
                            max_breadcrumbs=50,
                            debug=DEBUG,
                            environment="Debug build" if DEBUG else "Release",
                            request_bodies='small')

            with sentry_sdk.configure_scope() as scope:
                user_pc_name: str = socket.gethostname()
                try:
                    user_identifier: str = getpass.getuser()
                except ModuleNotFoundError:
                    user_identifier = user_pc_name

                scope.user = {'username': f'{user_pc_name}_{user_identifier}'}

        import main

        if launch:
            main.launch()
    except SystemExit:
        raise
    except Exception:
        handle_crash()


# displays and reports current traceback
def handle_crash():
    formatted_exception = traceback.format_exc()

    try:
        if not exc_already_reported(formatted_exception):
            sentry_sdk.add_breadcrumb(message=str(os.listdir('resources')), level='fatal')
            sentry_sdk.capture_exception()
    except Exception:
        # Sentry has failed us :(
        messagebox.showerror("TF2 Rich Presence",
                             f"{formatted_exception}"
                             f"\nTF2 Rich Presence {VERSION} has crashed, and the error can't be reported to the developer."
                             f"\n(Consider opening an issue at https://github.com/Kataiser/tf2-rich-presence/issues){out_of_date_warning()}")
    else:
        messagebox.showerror("TF2 Rich Presence",
                             f"{formatted_exception}"
                             f"\nTF2 Rich Presence {VERSION} has crashed, and the error has been reported to the developer."
                             f"\n(Consider opening an issue at https://github.com/Kataiser/tf2-rich-presence/issues){out_of_date_warning()}")

    # program closes now


# don't report the same exception twice
def exc_already_reported(tb: str) -> bool:
    try:
        tb_hash: str = str(zlib.crc32(tb.encode('UTF8', errors='replace')))  # technically not a hash but w/e
        db: dict = utils.access_db()

        if tb_hash in db['tb_hashes']:
            return True
        else:
            db['tb_hashes'].append(tb_hash)
            utils.access_db(db)
            return False
    except Exception:
        return False


# if a crash happens, tell the user that an update is available
def out_of_date_warning() -> str:
    try:
        available_version: str = utils.access_db()['available_version']

        if available_version:
            return f"\n\nBTW an newer version for TF2 Rich Presence is available ({available_version}), which may have fixed this crash."
        else:
            return ""
    except Exception:
        return ""


DEBUG = True
VERSION = '{tf2rpvnum}'

if __name__ == '__main__':
    main()
