# Copyright (C) 2018-2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import functools
import json
import os
from typing import Dict, List, Tuple, Union

import game_state
import launcher
import logger


# get the gamemode of either a vanilla or a custom map
@functools.cache
def get_map_gamemode(log: logger.Log, map_filename: str) -> Union[Tuple[str, str, str, bool], list]:
    if map_filename == '':
        log.error("Map filename is blank")
        return map_filename, 'unknown', 'Unknown gamemode', False

    map_gamemodes: Dict[str, List[str]] = load_maps_db()

    if map_filename in map_gamemodes:
        map_data: list = map_gamemodes[map_filename]
        map_data.append(False)

        # add some formatting for maps with multiple gamemodes
        if map_filename in game_state.ambiguous_maps:
            if map_data[1] in modes_short:
                map_data[0] = f'{map_data[0]} ({modes_short[map_data[1]]})'
            else:
                map_data[0] = f'{map_data[0]} ({map_data[2]})'

        return map_data
    elif not map_gamemodes:
        log.error("maps.json failed to load")

    log.debug(f"Finding gamemode for custom map: {map_filename}")

    # determine based on common substrings
    for gamemode_substring in substrings:
        if gamemode_substring in map_filename:
            gamemode: str = substrings[gamemode_substring]
            gamemode_fancy: str = modes[gamemode]
            log.debug(f"Determined gamemode to be {(gamemode, gamemode_fancy)}) based on substring ({gamemode_substring}_)")
            return map_filename, gamemode, gamemode_fancy, True

    # determine based on the map prefix
    map_prefix: str = map_filename.split('_')[0]
    if map_prefix in prefixes and '_' in map_filename:
        gamemode = prefixes[map_prefix]
        gamemode_fancy = modes[gamemode]
        log.debug(f"Determined gamemode to be {(gamemode, gamemode_fancy)}) based on prefix ({map_prefix}_)")
        return map_filename, gamemode, gamemode_fancy, True

    log.debug("Couldn't determine map gamemode from filename")  # probably trading
    return map_filename, 'unknown', 'Unknown gamemode', True


# load maps database from maps.json
@functools.cache
def load_maps_db() -> Dict[str, List[str]]:
    maps_db_path = 'maps.json' if launcher.DEBUG else os.path.join('resources', 'maps.json')

    if os.path.isfile(maps_db_path):
        with open(maps_db_path, 'r') as maps_db:
            return json.load(maps_db)
    else:
        return {}


modes: Dict[str, str] = {'ctf': 'Capture the Flag', 'control-point': 'Control Point', 'attack-defend': 'Attack/Defend', 'medieval-mode': 'Attack/Defend (Medieval Mode)',
                         'territorial-control': 'Territorial Control', 'payload': 'Payload', 'payload-race': 'Payload Race', 'koth': 'King of the Hill', 'special-delivery': 'Special Delivery',
                         'mvm': 'Mann vs. Machine', 'beta-map': 'Robot Destruction', 'mannpower': 'Mannpower', 'passtime': 'PASS Time', 'player-destruction': 'Player Destruction',
                         'arena': 'Arena', 'training': 'Training', 'surfing': 'Surfing', 'trading': 'Trading', 'jumping': 'Jumping', 'deathmatch': 'Deathmatch', 'cp-orange': 'Orange',
                         'versus-saxton-hale': 'Versus Saxton Hale', 'deathrun': 'Deathrun', 'achievement': 'Achievement', 'breakout': 'Jail Breakout', 'slender': 'Slender',
                         'dodgeball': 'Dodgeball', 'zombie': 'Zombie', 'mario-kart': 'Mario Kart', 'prophunt': 'Prop Hunt', 'mge-mod': 'MGE Mod'}

prefixes: Dict[str, str] = {'ctf': 'ctf', 'tc': 'territorial-control', 'pl': 'payload', 'plr': 'payload-race', 'koth': 'koth', 'sd': 'special-delivery', 'mvm': 'mvm', 'rd': 'beta-map',
                            'pass': 'passtime', 'pd': 'player-destruction', 'arena': 'arena', 'tr': 'training', 'surf': 'surfing', 'cp': 'control-point', 'trade': 'trading', 'jump': 'jumping',
                            'dm': 'deathmatch', 'vsh': 'versus-saxton-hale', 'dr': 'deathrun', 'achievement': 'achievement', 'jb': 'breakout', 'slender': 'slender', 'tfdb': 'dodgeball',
                            'zs': 'zombie', 'ze': 'zombie', 'zf': 'zombie', 'zm': 'zombie', 'duel': 'deathmatch', 'sn': 'deathmatch', 'ba': 'breakout', 'jail': 'breakout', 'idle': 'trading',
                            'mario': 'mario-kart', 'ph': 'prophunt', 'mge': 'mge-mod'}

substrings: Dict[str, str] = {'cp_orange': 'cp-orange', 'training': 'training'}
modes_short: Dict[str, str] = {'ctf': 'CTF', 'control-point': '5CP', 'attack-defend': 'A/D', 'medieval-mode': 'A/D (Medieval)',
                               'koth': 'KotH', 'mvm': 'MvM'}  # yes there are some unused ones but hey, futureproofing
have_drawing: tuple[str, ...] = ('attack-defend', 'control-point', 'ctf', 'koth', 'mannpower', 'mvm', 'passtime', 'payload', 'payload-race', 'special-delivery', 'training')
localization_excluded: tuple[str, ...] = ('surfing', 'trading', 'jumping', 'deathmatch', 'cp-orange', 'versus-saxton-hale', 'deathrun', 'achievement', 'breakout', 'slender', 'dodgeball',
                                          'zombie', 'mario-kart', 'prophunt', 'mge-mod')

if __name__ == '__main__':
    print(get_map_gamemode(logger.Log(), 'pl_borneo'))
    print(get_map_gamemode(logger.Log(), 'cp_catwalk_a5c'))
