import os
import sys
import traceback
from typing import Tuple

sys.path.append(os.path.abspath(os.path.join('resources', 'python', 'packages')))
sys.path.append(os.path.abspath(os.path.join('resources')))
import requests
from requests import Response

import logger
import main
import settings


# uses Github api to get the tag of the newest public release and compare it to the current version number, alerting the user if out of date
def check_for_update(current_version: str, timeout: float):
    log = logger.Log()

    if not settings.get('check_updates'):
        log.debug("Updater is disabled, skipping")
        raise SystemExit

    log.debug(f"Checking for updates, timeout: {timeout} secs")

    try:
        newest_version, downloads_url, changelog = access_github_api(timeout)
    except requests.exceptions.Timeout:
        log.error(f"Update check timed out")
        failure_message(current_version, f"timed out after {int(timeout)} seconds")
    except Exception:
        log.error(f"Non-timout update error: {traceback.format_exc()}")
        failure_message(current_version, sys.exc_info()[1])
    else:
        if current_version == newest_version:
            log.debug(f"Up to date ({current_version})")
        else:  # out of date
            log.error(f"Out of date, newest version is {newest_version}")
            print(f"This version ({current_version}) is out of date (newest version is {newest_version}).\nGet the update at {downloads_url}")
            print(f"\n{newest_version} changelog:\n{changelog}\n(If you're more than one version out of date, there may have been more changes and fixes than this.)\n")


# actually accesses the Github api, in a seperate function for tests
def access_github_api(time_limit: float) -> Tuple[str, str, str]:
    r: Response = requests.get('https://api.github.com/repos/Kataiser/tf2-rich-presence/releases/latest', timeout=time_limit)
    response: dict = r.json()
    newest_version_api: str = response['tag_name']
    downloads_url_api: str = response['html_url']
    changelog_api: str = response['body'].replace('## ', '')
    return newest_version_api, downloads_url_api, changelog_api


# either timed out or some other exception
def failure_message(current_version: str, error_message: str):
    line1 = f"Couldn't connect to GitHub to check for updates ({error_message}).\n"
    line2 = "To check for updates yourself, go to https://github.com/Kataiser/tf2-rich-presence/releases\n"
    line3 = f"(you are currently running {current_version}).\n"
    print(f"{line1}{line2}{line3}")


if __name__ == '__main__':
    # this gets run by the batch file, before the restart loop and main.py
    try:
        check_for_update('{tf2rpvnum}', settings.get('request_timeout'))
    except (KeyboardInterrupt, SystemExit):
        raise SystemExit
    except Exception as error:
        main.handle_crash(error, silent=True)
