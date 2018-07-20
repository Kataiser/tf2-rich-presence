import json

import certifi
import urllib3
import logger as log


def check(current_version, timeout):
    log.debug(f"Checking for updates, timeout: {timeout} secs")
    try:
        user_agent = {'user-agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0'}
        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where(), headers=user_agent)
        r = http.request('GET', 'https://api.github.com/repos/Kataiser/tf2-rich-presence/releases/latest', timeout=timeout)
    except urllib3.exceptions.MaxRetryError:
        log.error(f"Update check timed out")
        line1 = "\nCouldn't connect to GitHub to check for updates (timed out after {} seconds).\n".format(timeout)
        line2 = "To check for updates yourself, go to https://github.com/Kataiser/tf2-rich-presence/releases\n"
        line3 = "(you are currently running {}).\n".format(current_version)
        print(f"{line1}{line2}{line3}")
    else:
        response = json.loads(r.data.decode('utf-8'))
        newest_version = response['tag_name']

        if current_version != newest_version:  # out of date
            log.error(f"Out of date, newest version is {newest_version}")
            downloads_url = response['html_url']
            print(f"\nThis version ({current_version}) is out of date (newest version is {newest_version}).\nGet the update at {downloads_url}\n")


if __name__ == '__main__':
    check('v1.4.2', 5)
