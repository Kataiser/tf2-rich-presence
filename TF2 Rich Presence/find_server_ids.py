import json
import sys

import requests
from bs4 import BeautifulSoup


# downloads server information (IPs and names) from teamwork.tf
def main():
    with open('maps.json', 'r') as maps_json:
        maps_db = json.load(maps_json)

    official_maps = [maps_db[map_filename][0].lower().replace(' ', '') for map_filename in maps_db]

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

            ip_pairs = []  # only used for progress display
            ips = []  # ditto
            server_name = ''

            # every server a provider... provides
            for server_div in provider_page_soup.find_all('div'):
                for div_in_server_div in server_div.find_all('div'):
                    if div_in_server_div.get('class') == ['col-md-8', 'col-sm-8', 'col-xs-8', 'server-name']:  # WHY
                        server_name: str = div_in_server_div.string
                        server_name = server_name.lstrip().rstrip()  # remove leading and trailing whitespace

                for kbd in server_div.find_all('kbd'):  # kbd tag = keyboard. means monospace font in HTML
                    kbd_string = str(kbd.string)

                    if ':' in kbd_string and kbd_string not in ips:  # kbd tags are used for several things. this makes sure it's an IP
                        ip_pairs.append((kbd_string, server_name))
                        ips.append(kbd_string)
                        out[kbd_string] = (provider_name, server_name)

            print(ip_pairs)

    # make sure no map names are in server names
    ips_to_delete = []

    for out_ip in out:
        server_name_check = out[out_ip][1].lower().replace(' ', '')

        if "24/7" not in server_name_check:
            for map_name in official_maps:
                if map_name in server_name_check:
                    ips_to_delete.append(out_ip)
                    break

    for ip_to_delete in ips_to_delete:
        del out[ip_to_delete]
    print(f"\nRemoved {len(ips_to_delete)} servers with map names")

    with open(save_file_name, 'wb') as community_server_ips_json:
        community_server_ips_json.write(json.dumps(out, indent=4, ensure_ascii=False).encode('utf8'))  # the encoding stuff is because the json library hates unicode


# a requests.get with error handling in an infinite loop
def get_with_retries(url):
    retries_made = 0

    while True:
        try:
            return requests.get(url, timeout=2)
        except Exception as error:
            print(f"Error while accessing URL {url}: ({error}). Retrying...", file=sys.stderr)

            retries_made += 1
            if retries_made == 10 and 'providers' not in url:
                pass


if __name__ == '__main__':
    main()
