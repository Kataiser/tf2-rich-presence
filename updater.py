import requests

import logger as log


def check(current_version, timeout):
    log.debug(f"Checking for updates, timeout: {timeout} secs")
    try:
        r = requests.get('https://api.github.com/repos/Kataiser/tf2-rich-presence/releases/latest', timeout=timeout)
    except requests.exceptions.Timeout:
        log.error(f"Update check timed out")
        line1 = "Couldn't connect to GitHub to check for updates (timed out after {} seconds).\n".format(timeout)
        line2 = "To check for updates yourself, go to https://github.com/Kataiser/tf2-rich-presence/releases\n"
        line3 = "(you are currently running {}).\n".format(current_version)
        print(f"{line1}{line2}{line3}")
    else:
        response = r.json()
        newest_version = response['tag_name']

        if current_version != newest_version:  # out of date
            log.error(f"Out of date, newest version is {newest_version}")
            downloads_url = response['html_url']
            print(f"This version ({current_version}) is out of date (newest version is {newest_version}).\nGet the update at {downloads_url}\n")


if __name__ == '__main__':
    check('v1.4.2', 5)
