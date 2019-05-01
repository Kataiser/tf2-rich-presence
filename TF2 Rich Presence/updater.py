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
        newest_version, downloads_url, changelog, prerelease = access_github_api(timeout)
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
        elif prerelease:
            log.debug(f"Up to date ({current_version}) (prerelease {newest_version} is available)")
        else:  # out of date
            log.error(f"Out of date, newest version is {newest_version} (this is {current_version})")
            print(f"This version ({current_version}) is out of date (newest version is {newest_version}).\nGet the update at {downloads_url}")
            print(f"\n{newest_version} changelog:\n{changelog}\n(If you're more than one version out of date, there may have been more changes and fixes than this.)\n")


# actually accesses the Github api, in a seperate function for tests
def access_github_api(time_limit: float) -> Tuple[str, str, str, bool]:
    r: Response = requests.get('https://api.github.com/repos/Kataiser/tf2-rich-presence/releases/latest', timeout=time_limit)

    response: dict = r.json()
    newest_version_api: str = response['tag_name']
    downloads_url_api: str = response['html_url']
    changelog_api: str = response['body']
    prerelease_api = response['prerelease']

    changelog_formatted: str = f'  {changelog_api}'.replace('## ', '').replace('\n-', '\n -').replace('\n', '\n  ')
    return newest_version_api, downloads_url_api, changelog_formatted, prerelease_api


# either timed out or some other exception
def failure_message(current_version: str, error_message: str = None):
    if error_message:
        line1 = f"Couldn't connect to GitHub to check for updates ({error_message}).\n"
    else:
        line1 = "Couldn't connect to GitHub to check for updates.\n"

    line2 = "To check for updates yourself, go to https://github.com/Kataiser/tf2-rich-presence/releases\n"
    line3 = f"(you are currently running {current_version}).\n"
    print(f"{line1}{line2}{line3}")


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
