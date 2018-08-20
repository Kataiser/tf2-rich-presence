import traceback
from typing import Tuple

import requests
from requests import Response

import logger as log
import main


def check_for_update(current_version: str, timeout: float):
    log.debug(f"Checking for updates, timeout: {timeout} secs")

    try:
        newest_version, downloads_url, changelog = access_github_api(timeout)
    except requests.exceptions.Timeout:
        log.error(f"Update check timed out")
        failure_message(current_version, f"(timed out after {int(timeout)} seconds)")
    except Exception as other_error:
        log.error(f"Non-timout update error: {traceback.format_exc()}")
        failure_message(current_version, str(other_error))
    else:
        if current_version != newest_version:  # out of date
            log.error(f"Out of date, newest version is {newest_version}")
            print(f"This version ({current_version}) is out of date (newest version is {newest_version}).\nGet the update at {downloads_url}")
            print(f"\n{newest_version} changelog:\n{changelog}\n(If you're more than one version out of date, there may have been more changes and fixes than this.)\n")


def access_github_api(time_limit: float) -> Tuple[str, str, str]:
    r: Response = requests.get('https://api.github.com/repos/Kataiser/tf2-rich-presence/releases/latest', timeout=time_limit)
    response: dict = r.json()
    newest_version_api: str = response['tag_name']
    downloads_url_api: str = response['html_url']
    changelog_api: str = response['body'].replace('## ', '')
    return newest_version_api, downloads_url_api, changelog_api


def failure_message(current_version: str, error_message: str):
    line1 = f"Couldn't connect to GitHub to check for updates {error_message}.\n"
    line2 = "To check for updates yourself, go to https://github.com/Kataiser/tf2-rich-presence/releases\n"
    line3 = f"(you are currently running {current_version}).\n"
    print(f"{line1}{line2}{line3}")


if __name__ == '__main__':
    try:
        log.to_stderr = False
        check_for_update('{tf2rpvnum}', 5)
    except Exception as error:
        main.handle_crash(error)
