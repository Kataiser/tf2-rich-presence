# Copyright (C) 2018-2022 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import time
import traceback
from concurrent.futures import Future
from typing import Dict, Optional, Tuple, Union

import launcher
import logger
import settings
import utils


# TODO: an auto-updater (https://github.com/Squirrel/Squirrel.Windows maybe?)

# uses Github API to get the tag of the newest public release and compare it to the current version number, returns url etc.
# asynchronous thanks to requests-futures
class UpdateChecker:
    def __init__(self, log: logger.Log):
        self.log: logger.Log = log
        self.api_future: Optional[Future] = None
        self.checked_response: bool = False
        self.popup: bool = False

    # initiate the API request, which runs in a seperate thread
    def initiate_update_check(self, popup: bool, timeout: float = float(settings.get('request_timeout'))):
        if self.api_future is not None:
            self.log.debug("Skipping update check because it's already running")
            return

        self.log.debug(f"Checking for updates, timeout: {timeout} secs")
        self.popup = popup
        self.checked_response = False
        from requests_futures.sessions import FuturesSession
        self.api_future = FuturesSession(max_workers=1).get('https://api.github.com/repos/Kataiser/tf2-rich-presence/releases/latest', timeout=timeout, headers={'Connection': 'close'})

    # request either finished or failed
    def update_check_ready(self) -> bool:
        return self.api_future is not None and self.api_future.done() and not self.checked_response

    # parse API result or handle errors
    def receive_update_check(self, raise_exceptions: bool = False) -> Optional[Tuple[str, str, str]]:
        import requests
        self.checked_response = True

        try:
            result = self.api_future.result()
        except (requests.Timeout, requests.exceptions.ReadTimeout):
            self.log.error(f"Update check timed out", reportable=False)

            if raise_exceptions:
                raise
        except requests.RequestException:
            self.log.error(f"Connection error in updater: {traceback.format_exc()}", reportable=False)

            if raise_exceptions:
                raise
        except Exception:
            self.log.error(f"Non-connection based update error: {traceback.format_exc()}")
        else:
            self.log.debug(f"Update check took {round(result.elapsed.microseconds / 1000000, 3)} seconds")
            response: dict = result.json()
            self.api_future = None

            try:
                newest_version: str = response['tag_name']
                downloads_url: str = response['html_url']
                changelog: str = response['body']
            except KeyError:
                if 'message' in response and 'API rate limit exceeded' in response['message']:
                    rate_limit_message: str = f"Github {response['message'].split('(')[0][:-1]}"
                    raise RateLimitError(rate_limit_message)
                else:
                    raise

            changelog_formatted: str = format_changelog(changelog)

            if launcher.VERSION == newest_version:
                self.log.debug(f"Up to date ({launcher.VERSION})")
            else:  # out of date
                self.log.error(f"Out of date, newest version is {newest_version} (this is {launcher.VERSION})", reportable=False)

                # save available version for the launcher
                db: Dict[str, Union[bool, list, str]] = utils.access_db()
                db['available_version'] = newest_version
                utils.access_db(db)

                return newest_version, downloads_url, changelog_formatted


def format_changelog(log_text: str) -> str:
    return f'  {log_text}'.replace('## ', '').replace('\r\n', '\n').replace('\n- ', '\n - ').replace('\n', '\n  ')


class RateLimitError(Exception):
    pass


if __name__ == '__main__':
    update_checker = UpdateChecker(logger.Log())
    update_checker.initiate_update_check(True, 10.0)
    while not update_checker.update_check_ready():
        time.sleep(0.2)
    print(update_checker.receive_update_check())
