import traceback

import requests

import logger as log


def check(current_version, timeout):
    log.debug(f"Checking for updates, timeout: {timeout} secs")

    try:
        r = requests.get('https://api.github.com/repos/Kataiser/tf2-rich-presence/releases/latest', timeout=timeout)
        response = r.json()
        newest_version = response['tag_name']
        downloads_url = response['html_url']
        changelog = response['body'].replace('## ', '')
    except requests.exceptions.Timeout:
        log.error(f"Update check timed out")
        failure_message(current_version, f"(timed out after {timeout} seconds)")
    except Exception as other_error:
        log.error(f"Non-timout update error: {traceback.format_exc()}")
        failure_message(current_version, other_error)
    else:
        if current_version != newest_version:  # out of date
            log.error(f"Out of date, newest version is {newest_version}")
            print(f"This version ({current_version}) is out of date (newest version is {newest_version}).\nGet the update at {downloads_url}")
            print(f"\n{newest_version} changelog:\n{changelog}\n")


def failure_message(current_version, error_message):
    line1 = f"Couldn't connect to GitHub to check for updates {error_message}.\n"
    line2 = "To check for updates yourself, go to https://github.com/Kataiser/tf2-rich-presence/releases\n"
    line3 = f"(you are currently running {current_version}).\n"
    print(f"{line1}{line2}{line3}")


if __name__ == '__main__':
    check('v1.4.2', 5)
