import json
import sys

import requests
from bs4 import BeautifulSoup


def main():
    save_file_name = 'community_server_ips.json'

    try:
        with open(save_file_name, 'r', errors='ignore') as community_server_ips_json:
            out = json.load(community_server_ips_json)
    except FileNotFoundError:
        out = {}

    providers_page = get_with_retries('https://teamwork.tf/community/providers').text
    providers_page_soup = BeautifulSoup(providers_page, 'lxml')

    for outer_div in providers_page_soup.find_all('div'):
        if outer_div.get('class') == ['provider-tile-container']:
            provider_page_url = f'https://teamwork.tf{outer_div.find("a").get("href")}'

            for inner_div in outer_div.find_all('div'):
                if inner_div.get('class') == ['quickplay-tile-head']:
                    provider_name = inner_div.find('h3').string

            print(provider_name, provider_page_url)

            provider_page = get_with_retries(provider_page_url).text
            provider_page_soup = BeautifulSoup(provider_page, 'lxml')

            ips = []
            server_name = ''

            for server_div in provider_page_soup.find_all('div'):
                for div_in_server_div in server_div.find_all('div'):
                    if div_in_server_div.get('class') == ['col-md-8', 'col-sm-8', 'col-xs-8', 'server-name']:
                        server_name: str = div_in_server_div.string
                        server_name = server_name.lstrip().rstrip()

                for kbd in server_div.find_all('kbd'):
                    kbd_string = str(kbd.string)

                    if ':' in kbd_string:
                        ips.append((kbd_string, server_name))
                        out[kbd_string] = (provider_name, server_name)

            print(ips)

    with open(save_file_name, 'wb') as community_server_ips_json:
        community_server_ips_json.write(json.dumps(out, indent=4, ensure_ascii=False).encode('utf8'))


def get_with_retries(url):
    while True:
        try:
            return requests.get(url, timeout=15)
        except Exception as error:
            print(f"Error while accessing URL {url}: ({error}). Retrying...", file=sys.stderr)


if __name__ == '__main__':
    main()
