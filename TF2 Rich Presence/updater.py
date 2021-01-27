# Copyright (C) 2018-2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import traceback
from typing import Dict, Optional, Tuple, Union

import launcher
import logger
import utils


# TODO: an auto-updater (https://github.com/Squirrel/Squirrel.Windows maybe?)

# uses Github api to get the tag of the newest public release and compare it to the current version number, returns url and
def check_for_update(log: logger.Log, current_version: str, timeout: float) -> Optional[Tuple[str, str, str]]:
    log.debug(f"Checking for updates, timeout: {timeout} secs")
    import requests

    try:
        newest_version, downloads_url, changelog = access_github_api(timeout)
    except (requests.Timeout, requests.exceptions.ReadTimeout):
        log.error(f"Update check timed out", reportable=False)
    except requests.RequestException:
        log.error(f"Connection error in updater: {traceback.format_exc()}", reportable=False)
    except Exception:
        log.error(f"Non-connection based update error: {traceback.format_exc()}")
    else:
        if current_version == newest_version:
            log.debug(f"Up to date ({current_version})")
        else:  # out of date
            log.error(f"Out of date, newest version is {newest_version} (this is {current_version})", reportable=False)

            # save available version for the launcher
            db: Dict[str, Union[bool, list, str]] = utils.access_db()
            db['available_version'] = newest_version
            utils.access_db(db)

            return newest_version, downloads_url, changelog

    return None


# actually accesses the Github api, in a seperate function for tests
def access_github_api(time_limit: float) -> Tuple[str, str, str]:
    import requests
    from requests import Response
    r: Response = requests.get('https://api.github.com/repos/Kataiser/tf2-rich-presence/releases/latest', timeout=time_limit)
    response: dict = r.json()

    try:
        newest_version_api: str = response['tag_name']
        downloads_url_api: str = response['html_url']
        changelog_api: str = response['body']
    except KeyError:
        if 'message' in response and 'API rate limit exceeded' in response['message']:
            rate_limit_message: str = f"Github {response['message'].split('(')[0][:-1]}"
            raise RateLimitError(rate_limit_message)
        else:
            raise

    changelog_formatted: str = format_changelog(changelog_api)
    return newest_version_api, downloads_url_api, changelog_formatted


def format_changelog(log_text: str) -> str:
    return f'  {log_text}'.replace('## ', '').replace('\r\n', '\n').replace('\n- ', '\n - ').replace('\n', '\n  ')


class RateLimitError(Exception):
    pass


if __name__ == '__main__':
    check_for_update(logger.Log(), launcher.VERSION, 10.0)
