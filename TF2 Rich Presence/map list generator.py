# Copyright (C) 2018-2022 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import json

import requests
from bs4 import BeautifulSoup

import gamemodes


def main():
    gamemodes_reversed = {gamemodes.modes[key]: key for key in gamemodes.modes}
    gamemodes_reversed['Attack/Defend (Medieval)'] = 'attack-defend'
    gamemodes_reversed['Control Point (Domination)'] = 'control-point'
    gamemodes_reversed['No gamemode'] = 'beta-map'
    gamemode_replacements = [('d(M', 'd (M'), ('t(D', 't (D'), (' Mode', ''), ('Developer aidTest', 'No gamemode'), ('Developer aidControl Point', 'Control Point')]
    map_gamemodes = {'itemtest': ('itemtest', 'unknown', 'Unknown gamemode'),
                     'devtest': ('devtest', 'unknown', 'Unknown gamemode'),
                     'background01': ('background01', 'unknown', 'Unknown gamemode'),
                     'koth_sharkbay': ('Sharkbay', 'koth', 'King of the Hill'),
                     'koth_rotunda': ('Rotunda', 'koth', 'King of the Hill'),
                     'pl_phoenix': ('Phoenix', 'payload', 'Payload'),
                     'pl_cashworks': ('Cashworks', 'payload', 'Payload'),
                     'pl_venice': ('Venice', 'payload', 'Payload'),
                     'cp_reckoner': ('Reckoner', 'control-point', 'Control Point'),
                     'cp_sulfur': ('Sulfur', 'attack-defend', 'Attack/Defend'),
                     'cp_hardwood_final': ('Hardwood', 'attack-defend', 'Attack/Defend'),
                     'ctf_pelican_peak': ('Pelican Peak', 'ctf', 'Capture the Flag'),
                     'pd_selbyen': ('Selbyen', "player-destruction", "Player Destruction"),
                     'vsh_tinyrock': ('Tiny Rock', 'versus-saxton-hale', 'Versus Saxton Hale'),
                     'vsh_distillery': ('Distillery', 'versus-saxton-hale', 'Versus Saxton Hale'),
                     'vsh_skirmish': ('Skirmish', 'versus-saxton-hale', 'Versus Saxton Hale'),
                     'vsh_nucleus': ('Nucleus', 'versus-saxton-hale', 'Versus Saxton Hale')}

    r = requests.get('https://wiki.teamfortress.com/wiki/List_of_maps')
    soup = BeautifulSoup(r.text, 'lxml')

    for tr in soup.find_all('tr'):
        try:
            map_file = tr.find('code').text
            map_name = tr.find('b').text
        except AttributeError:
            continue

        if map_file == 'itemtest':
            continue

        gamemode_fancy = tr.find_all('td')[2].text.strip()

        for replacement in gamemode_replacements:
            gamemode_fancy = gamemode_fancy.replace(*replacement)

        map_mode = gamemodes_reversed[gamemode_fancy]

        if map_mode and map_name:
            map_file = map_file.replace(' ', '')
            map_gamemodes[map_file] = (map_name, map_mode, gamemode_fancy)

    for map_file in map_gamemodes:
        print(f"{map_file}: {map_gamemodes[map_file]}")

    out = json.dumps(map_gamemodes, sort_keys=True).replace('], ', '],\n    ').replace('{', '{\n    ').replace('}', '\n}')

    print()
    print(out)

    with open('maps.json', 'w') as maps_db:
        maps_db.write(out)


if __name__ == '__main__':
    main()
