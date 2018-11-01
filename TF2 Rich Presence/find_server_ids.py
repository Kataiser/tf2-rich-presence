import json
import sys

import requests
from bs4 import BeautifulSoup


# downloads server information (IPs and names) from teamwork.tf
def main():
    save_file_name = 'community_server_ips.json'

    # finds out loads the old database
    try:
        with open(save_file_name, 'rb') as community_server_ips_json:
            out = json.load(community_server_ips_json)
    except FileNotFoundError:
        out = {}

    # download the main providers page
    providers_page = get_with_retries('https://teamwork.tf/community/providers').text
    providers_page_soup = BeautifulSoup(providers_page, 'lxml')

    for outer_div in providers_page_soup.find_all('div'):  # trying to find a link to each provider page
        if outer_div.get('class') == ['provider-tile-container']:
            provider_page_url = f'https://teamwork.tf{outer_div.find("a").get("href")}'

            # get the name of the provider from the button
            for inner_div in outer_div.find_all('div'):
                if inner_div.get('class') == ['quickplay-tile-head']:
                    provider_name = inner_div.find('h3').string

            print(provider_name, provider_page_url)

            # download the particular provider page
            provider_page = get_with_retries(provider_page_url).text
            provider_page_soup = BeautifulSoup(provider_page, 'lxml')

            ips = []  # only used for progress display
            server_name = ''

            # every server a provider... provides
            for server_div in provider_page_soup.find_all('div'):
                for div_in_server_div in server_div.find_all('div'):
                    if div_in_server_div.get('class') == ['col-md-8', 'col-sm-8', 'col-xs-8', 'server-name']:  # WHY
                        server_name: str = div_in_server_div.string
                        server_name = server_name.lstrip().rstrip()  # remove leading and trailing whitespace

                for kbd in server_div.find_all('kbd'):  # kbd tag = keyboard. means monospace font in HTML
                    kbd_string = str(kbd.string)

                    if ':' in kbd_string:  # kbd tags are used for several things. this makes sure it's an IP
                        ips.append((kbd_string, server_name))
                        out[kbd_string] = (provider_name, server_name)

            print(ips)

    with open(save_file_name, 'wb') as community_server_ips_json:
        community_server_ips_json.write(json.dumps(out, indent=4, ensure_ascii=False).encode('utf8'))  # the encoding stuff is because the json library hates unicode


# a requests.get with error handling in an infinite loop
def get_with_retries(url):
    while True:
        try:
            return requests.get(url, timeout=15)
        except Exception as error:
            print(f"Error while accessing URL {url}: ({error}). Retrying...", file=sys.stderr)


if __name__ == '__main__':
    main()
