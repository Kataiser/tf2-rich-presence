import json

import requests
from bs4 import BeautifulSoup


def main():
    try:
        with open('community_server_ips.json', 'r') as community_server_ips_json:
            out = json.load(community_server_ips_json)
    except FileNotFoundError:
        out = {}

    providers_page = requests.get('https://teamwork.tf/community/providers').text
    providers_page_soup = BeautifulSoup(providers_page, 'lxml')

    for outer_div in providers_page_soup.find_all('div'):
        if outer_div.get('class') == ['provider-tile-container']:
            provider_page_url = f'https://teamwork.tf{outer_div.find("a").get("href")}'

            for inner_div in outer_div.find_all('div'):
                if inner_div.get('class') == ['quickplay-tile-head']:
                    provider_name = inner_div.find('h3').string

            print(provider_name, provider_page_url)

            try:
                ips: list = out[provider_name]
            except KeyError:
                ips = []

            provider_page = requests.get(provider_page_url).text
            provider_page_soup = BeautifulSoup(provider_page, 'lxml')

            for kbd in provider_page_soup.find_all('kbd'):
                kbd_string = str(kbd.string)

                if ':' in kbd_string and kbd_string not in ips:
                    ips.append(kbd_string)

            print(ips)
            out[provider_name] = ips

            if not ips:
                del out[provider_name]

    with open('community_server_ips.json', 'w') as community_server_ips_json:
        json.dump(out, community_server_ips_json, indent=4)


if __name__ == '__main__':
    main()
