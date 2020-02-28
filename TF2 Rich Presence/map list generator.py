# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import json
import sys

import requests
from bs4 import BeautifulSoup

import custom_maps
import logger


def main():
    common_custom = map_stats()
    common_custom.update(map_explorer())  # basically a set dict

    official_out = json.dumps(official(), sort_keys=True).replace('], ', '],\n        ')
    common_custom_out = json.dumps(common_custom, sort_keys=True).replace('], ', '],\n        ')

    out = json.dumps({'official': 'replace1', 'common_custom': 'replace2'}, indent=4)\
        .replace('"replace1"', '{\n        ' + official_out[1:]).replace('"replace2"', '{\n        ' + common_custom_out[1:])

    print(out)
    with open('maps.json', 'w') as maps_db:
        maps_db.write(out)


def official() -> dict:
    gamemodes = {custom_maps.gamemodes[key]: key for key in custom_maps.gamemodes}  # reversed key/value order
    gamemodes['Attack/Defend (Medieval)'] = 'attack-defend'
    gamemodes['Control Point (Domination)'] = 'control-point'
    gamemodes['No gamemode'] = 'beta-map'
    gamemode_replacements = [('d(M', 'd (M'), ('t(D', 't (D'), (' Mode', ''), ('Developer aidTest', 'No gamemode'), ('Developer aidControl Point', 'Control Point')]
    map_gamemodes = {}

    r = requests.get('https://wiki.teamfortress.com/wiki/List_of_maps')
    soup = BeautifulSoup(r.text, 'lxml')

    for tr in soup.find_all('tr'):
        try:
            map_file = tr.find('code').text
            map_name = tr.find('b').text
        except AttributeError:
            continue

        gamemode_fancy = tr.find_all('td')[2].text[1:-1]

        for replacemment in gamemode_replacements:
            gamemode_fancy = gamemode_fancy.replace(*replacemment)

        map_mode = gamemodes[gamemode_fancy]

        if map_mode and map_name:
            map_file = map_file.replace(' ', '')
            map_gamemodes[map_file] = (map_name, map_mode, gamemode_fancy)
            print(f"{map_file}: {map_gamemodes[map_file]}")

    return map_gamemodes


def map_stats() -> dict:
    custom_map_gamemodes = {}

    r = requests.get('https://teamwork.tf/community/map-stats#topavgplayernonofficial')
    soup = BeautifulSoup(r.text, 'lxml')

    log = logger.Log()
    log.enabled = False

    for div in soup.find_all('div'):
        if div.get('id') == 'topavgplayernonofficial':
            for a in div.find_all('a'):
                map_file = a.find('strong').text.strip()
                map_mode = custom_maps.find_custom_map_gamemode(log, map_file, timeout=10)

                if map_mode[0] == 'unknown_map':
                    print(f"FAILED: {map_file}", file=sys.stderr)
                else:
                    custom_map_gamemodes[map_file] = map_mode
                    print(f"{map_file}: {custom_map_gamemodes[map_file]}")

    return custom_map_gamemodes


def map_explorer() -> dict:
    custom_map_gamemodes = {}
    official_maps = custom_maps.load_maps_db()['official']

    r = requests.get('https://teamwork.tf/community/map-explorer')
    soup = BeautifulSoup(r.text, 'lxml')

    log = logger.Log()
    log.enabled = False

    map_divs = [div for div in soup.find_all('div') if div.get('class') == ['col-md-3', 'col-sm-6']]

    for map_div in map_divs[:100]:
        map_file = map_div.find('h3').text

        if map_file not in official_maps:
            map_mode = custom_maps.find_custom_map_gamemode(log, map_file, timeout=10)

            if map_mode[0] == 'unknown_map':
                print(f"FAILED: {map_file}", file=sys.stderr)
            else:
                if map_file == 'cp_degrootkeep':
                    custom_map_gamemodes[map_file] = ('medieval-mode', 'Control Point (Medieval Mode)')
                elif map_file == 'cp_dustbowl_forest':
                    custom_map_gamemodes[map_file] = ('control-point', 'Control Point')
                elif map_file == 'vsh_towertop_final':
                    custom_map_gamemodes[map_file] = ('versus-saxton-hale', 'Versus Saxton Hale')
                else:
                    custom_map_gamemodes[map_file] = map_mode

                print(f"{map_file}: {custom_map_gamemodes[map_file]}")

    return custom_map_gamemodes


if __name__ == '__main__':
    main()
