# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import functools
import json
import sys

import requests
from bs4 import BeautifulSoup

import custom_maps
import logger
import utils


def main():
    common_custom = map_stats()
    common_custom.update(map_explorer())  # basically a set dict
    common_custom.update(creators_tf_cp())

    for custom_map in list(common_custom.keys()):
        if custom_map.split('_')[0] in custom_maps.gamemode_prefixes and '_' in custom_map:
            del common_custom[custom_map]
        else:
            for gamemode_substring in custom_maps.gamemode_substrings:
                if gamemode_substring in custom_map:
                    del common_custom[custom_map]

    official_out = json.dumps(official(), sort_keys=True).replace('], ', '],\n        ')
    common_custom_out = json.dumps(common_custom, sort_keys=True).replace('], ', '],\n        ')

    out = json.dumps({'official': 'replace1', 'common_custom': 'replace2'}, indent=4) \
        .replace('"replace1"', '{\n        ' + official_out[1:]) \
        .replace('"replace2"', '{\n        ' + common_custom_out[1:])

    print()
    print(out)

    with open('maps.json', 'w') as maps_db:
        maps_db.write(out)


def official() -> dict:
    gamemodes = {custom_maps.gamemodes[key]: key for key in custom_maps.gamemodes}  # reversed key/value order
    gamemodes['Attack/Defend (Medieval)'] = 'attack-defend'
    gamemodes['Control Point (Domination)'] = 'control-point'
    gamemodes['No gamemode'] = 'beta-map'
    gamemode_replacements = [('d(M', 'd (M'), ('t(D', 't (D'), (' Mode', ''), ('Developer aidTest', 'No gamemode'), ('Developer aidControl Point', 'Control Point')]
    map_gamemodes = {'background01': ('Background01', 'beta-map', 'No gamemode'),
                     'devtest': ('Devtest', 'beta-map', 'No gamemode'),
                     'koth_megalo': ('Megalo', 'koth', 'King of the Hill'),
                     'koth_undergrove_event': ('Moldergrove', 'koth', 'King of the Hill'),
                     'pl_bloodwater': ('Bloodwater', 'payload', 'Payload'),
                     'pl_hasslecastle': ('Hassle Castle', 'payload', 'Payload')}

    r = requests.get('https://wiki.teamfortress.com/wiki/List_of_maps')
    soup = BeautifulSoup(r.text, 'lxml')

    for tr in soup.find_all('tr'):
        try:
            map_file = tr.find('code').text
            map_name = tr.find('b').text
        except AttributeError:
            continue

        gamemode_fancy = tr.find_all('td')[2].text[1:-1]

        for replacement in gamemode_replacements:
            gamemode_fancy = gamemode_fancy.replace(*replacement)

        map_mode = gamemodes[gamemode_fancy]

        if map_mode and map_name:
            map_file = map_file.replace(' ', '')
            map_gamemodes[map_file] = (map_name, map_mode, gamemode_fancy)

    for map_file in map_gamemodes:
        print(f"{map_file}: {map_gamemodes[map_file]}")

    return map_gamemodes


@functools.lru_cache(maxsize=1)
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


@functools.lru_cache(maxsize=1)
def map_explorer() -> dict:
    custom_map_gamemodes = {}
    official_maps = utils.load_maps_db()['official']

    r = requests.get('https://teamwork.tf/community/map-explorer')
    soup = BeautifulSoup(r.text, 'lxml')

    log = logger.Log()
    log.enabled = False

    map_divs = [div for div in soup.find_all('div') if div.get('class') == ['col-md-3', 'col-sm-6']]

    for map_div in map_divs[:100]:
        map_file = map_div.find('h3').text

        if map_file not in official_maps and not map_file.split('_')[0] in custom_maps.gamemode_prefixes:
            map_mode = custom_maps.find_custom_map_gamemode(log, map_file, timeout=10)

            if map_mode[0] == 'unknown_map':
                print(f"FAILED: {map_file}", file=sys.stderr)
            else:
                if map_file == 'cp_degrootkeep':
                    custom_map_gamemodes[map_file] = ('medieval-mode', 'Control Point (Medieval Mode)')
                else:
                    custom_map_gamemodes[map_file] = map_mode

                print(f"{map_file}: {custom_map_gamemodes[map_file]}")

    return custom_map_gamemodes


def creators_tf_cp() -> dict:
    all_cp_creators_maps = {'cp_glassworks_rc6a': ['control-point', 'Control Point'],
                            'cp_kalinka_rc5': ['control-point', 'Control Point'],
                            'cp_powerhouse_fix': ['control-point', 'Control Point'],
                            'cp_rumble_rc5': ['attack-defend', 'Attack/Defend']}

    exclusive_creators_map = {}

    for creators_map in all_cp_creators_maps:
        if creators_map not in map_stats() and creators_map not in map_explorer():
            exclusive_creators_map[creators_map] = all_cp_creators_maps[creators_map]

    return exclusive_creators_map


if __name__ == '__main__':
    main()
