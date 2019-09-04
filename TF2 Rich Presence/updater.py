# Copyright (C) 2019  Kataiser
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import json
import os
import traceback
from typing import Tuple

import requests
from requests import Response

import localization
import logger
import main
import settings


# uses Github api to get the tag of the newest public release and compare it to the current version number, alerting the user if out of date
def check_for_update(current_version: str, timeout: float):
    log = logger.Log()
    loc = localization.Localizer(language=settings.get('language'))

    if '{' in '{tf2rpvnum}' or not settings.get('check_updates'):
        log.debug("Updater is disabled, skipping")
        raise SystemExit

    log.debug(f"Checking for updates, timeout: {timeout} secs")

    try:
        newest_version, downloads_url, changelog = access_github_api(timeout)
    except requests.exceptions.Timeout:
        log.error(f"Update check timed out")
        failure_message(current_version, f"timed out after {int(timeout)} seconds")
    except requests.exceptions.ConnectionError:
        log.error(f"Connection error in updater: {traceback.format_exc()}")
        failure_message(current_version)
    except Exception:
        log.error(f"Non-timeout update error: {traceback.format_exc()}")
        failure_message(current_version, 'unknown error')
    else:
        if current_version == newest_version:
            log.debug(f"Up to date ({current_version})")
        else:  # out of date
            log.error(f"Out of date, newest version is {newest_version} (this is {current_version})")

            # save available version for the settings button
            db_path = os.path.join('resources', 'DB.json') if os.path.isdir('resources') else 'DB.json'
            with open(db_path, 'r+') as db_json:
                db_data = json.load(db_json)
                db_data['available_version']['exists'] = True
                db_data['available_version']['tag'] = newest_version
                db_data['available_version']['url'] = downloads_url
                db_json.seek(0)
                db_json.truncate(0)
                json.dump(db_data, db_json, indent=4)

            print(loc.text("This version ({0}) is out of date (newest version is {1}).").format(current_version, newest_version))
            print(loc.text("Get the update with the download button in settings."), end='\n\n')
            print(loc.text("{0} changelog:").format(newest_version))
            print(changelog)
            print(loc.text("(If you're more than one version out of date, there may have been more changes and fixes than this.)"), end='\n\n')


# actually accesses the Github api, in a seperate function for tests
def access_github_api(time_limit: float) -> Tuple[str, str, str]:
    r: Response = requests.get('https://api.github.com/repos/Kataiser/tf2-rich-presence/releases/latest', timeout=time_limit)

    response: dict = r.json()
    newest_version_api: str = response['tag_name']
    downloads_url_api: str = response['html_url']
    changelog_api: str = response['body']

    changelog_formatted: str = f'  {changelog_api}'.replace('## ', '').replace('\n-', '\n -').replace('\n', '\n  ')
    return newest_version_api, downloads_url_api, changelog_formatted


# either timed out or some other exception
def failure_message(current_version: str, error_message: str = None):
    loc = localization.Localizer(language=settings.get('language'))

    if error_message:
        line1 = loc.text("Couldn't connect to GitHub to check for updates ({0}).").format(error_message)
    else:
        line1 = loc.text("Couldn't connect to GitHub to check for updates.")

    line2 = loc.text("To check for updates yourself, go to {0}").format("https://github.com/Kataiser/tf2-rich-presence/releases")
    line3 = "(you are currently running {0}).".format(current_version)
    print(f"{line1}\n{line2}\n{line3}\n")


def launch():
    # this gets run by the batch file, before the restart loop and main.py
    try:
        check_for_update('{tf2rpvnum}', settings.get('request_timeout'))
    except (KeyboardInterrupt, SystemExit):
        raise SystemExit
    except Exception:
        crash_logger = logger.Log()
        app_for_crash_handling = main.TF2RichPresense(crash_logger)
        app_for_crash_handling.handle_crash(silent=True)


if __name__ == '__main__':
    launch()
