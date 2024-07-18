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
    gamemodes_reversed['N/A'] = 'control-point'
    gamemode_replacements = [('d(M', 'd (M'), ('t(D', 't (D'), (' Mode', ''), ('Developer aidTest', 'No gamemode'), ('Developer aidControl Point', 'Control Point'), ('Capture point', 'Control Point')]
    gamemode_overrides = {'tc_hydro': ('territorial-control', 'Territorial Control'),
                          'cp_degrootkeep': ('attack-defend', 'Attack/Defend (Medieval)'),
                          'cp_degrootkeep_rats': ('attack-defend', 'Attack/Defend (Medieval)'),
                          'cp_standin_final': ('control-point', 'Control Point (Domination)'),
                          'cp_cloak': ('control-point', 'Control Point')}
    map_gamemodes = {'itemtest': ('itemtest', 'unknown', 'Unknown gamemode'),
                     'devtest': ('devtest', 'unknown', 'Unknown gamemode'),
                     'background01': ('background01', 'unknown', 'Unknown gamemode'),
                     'pl_embargo': ('Embargo', 'payload', 'Payload'),
                     'pl_odyssey': ('Odyssey', 'payload', 'Payload'),
                     'koth_megaton': ('Megaton', 'koth', 'King of the Hill'),
                     'koth_cachoeira': ('Cachoeira', 'koth', 'King of the Hill'),
                     'cp_overgrown': ('Overgrown', 'attack-defend', 'Attack/Defend'),
                     'cp_hadal': ('Hadal', 'attack-defend', 'Attack/Defend'),
                     'ctf_applejack': ('Applejack', 'ctf', 'Capture the Flag'),
                     'pd_atom_smash': ('Atom Smash', 'player-destruction', 'Player Destruction'),
                     'cp_canaveral_5cp': ('Canaveral', 'control-point', 'Control Point'),
                     'cp_burghausen': ('Burghausen', 'attack-defend', 'Attack/Defend (Medieval)')}

    r = requests.get('https://wiki.teamfortress.com/wiki/List_of_maps')
    soup = BeautifulSoup(r.text, 'lxml')

    for tr in soup.find_all('table')[1].find_all('tr'):
        try:
            map_file = tr.find('code').text
            map_name = tr.find_all('td')[1].text
        except AttributeError:
            continue

        if map_file == 'itemtest':
            continue

        gamemode_fancy = tr.find_all('td')[2].text.strip()

        for replacement in gamemode_replacements:
            gamemode_fancy = gamemode_fancy.replace(*replacement)

        map_mode = gamemodes_reversed[gamemode_fancy]

        if map_file in gamemode_overrides:
            map_mode, gamemode_fancy = gamemode_overrides[map_file]

        if map_mode and map_name:
            map_file = map_file.replace(' ', '')
            map_gamemodes[map_file] = (map_name.partition('(')[0].strip(), map_mode, gamemode_fancy)

    for map_file in map_gamemodes:
        print(f"{map_file}: {map_gamemodes[map_file]}")

    out = json.dumps(map_gamemodes, sort_keys=True).replace('], ', '],\n    ').replace('{', '{\n    ').replace('}', '\n}')

    print()
    print(out)

    with open('maps.json', 'w') as maps_db:
        maps_db.write(out)


if __name__ == '__main__':
    main()
