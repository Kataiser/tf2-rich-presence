# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import functools
import json
import os
from typing import Dict, List

import logger


# get the gamemode of either a vanilla or a custom map
@functools.lru_cache(maxsize=None)
def get_map_gamemode(log, map_filename: str):
    if map_filename == '':
        log.error("Map filename is blank")
        return map_filename, 'unknown_map', 'Unknown gamemode'

    map_gamemodes: Dict[str, List[str]] = load_maps_db()

    if map_filename in map_gamemodes:
        return map_gamemodes[map_filename]
    elif not map_gamemodes:
        log.error("maps.json failed to load")

    log.debug(f"Finding gamemode for custom map: {map_filename}")

    # determine based on common substrings
    for gamemode_substring in gamemode_substrings:
        if gamemode_substring in map_filename:
            gamemode = gamemode_substrings[gamemode_substring]
            gamemode_fancy = gamemodes[gamemode]
            log.debug(f"Determined gamemode to be {(gamemode, gamemode_fancy)}) based on substring ({gamemode_substring}_)")
            return map_filename, gamemode, gamemode_fancy

    # determine based on the map prefix
    map_prefix: str = map_filename.split('_')[0]
    if map_prefix in gamemode_prefixes and '_' in map_filename:
        gamemode: str = gamemode_prefixes[map_prefix]
        gamemode_fancy: str = gamemodes[gamemode]
        log.debug(f"Determined gamemode to be {(gamemode, gamemode_fancy)}) based on prefix ({map_prefix}_)")
        return map_filename, gamemode, gamemode_fancy

    log.error("Couldn't get map gamemode")  # probably trading
    return map_filename, 'unknown_map', 'Unknown gamemode'


# load maps database from maps.json
@functools.lru_cache(maxsize=1)
def load_maps_db() -> Dict[str, List[str]]:
    maps_db_path = os.path.join('resources', 'maps.json') if os.path.isdir('resources') else 'maps.json'

    if os.path.isfile(maps_db_path):
        with open(maps_db_path, 'r') as maps_db:
            return json.load(maps_db)
    else:
        return {}


gamemodes: Dict[str, str] = {'ctf': 'Capture the Flag', 'control-point': 'Control Point', 'attack-defend': 'Attack/Defend', 'medieval-mode': 'Attack/Defend (Medieval Mode)',
                             'territorial-control': 'Territorial Control', 'payload': 'Payload', 'payload-race': 'Payload Race', 'koth': 'King of the Hill',
                             'special-delivery': 'Special Delivery', 'mvm': 'Mann vs. Machine', 'beta-map': 'Robot Destruction', 'mannpower': 'Mannpower', 'passtime': 'PASS Time',
                             'player-destruction': 'Player Destruction', 'arena': 'Arena', 'training': 'Training', 'surfing': 'Surfing', 'trading': 'Trading', 'jumping': 'Jumping',
                             'deathmatch': 'Deathmatch', 'cp-orange': 'Orange', 'versus-saxton-hale': 'Versus Saxton Hale', 'deathrun': 'Deathrun', 'achievement': 'Achievement',
                             'breakout': 'Jail Breakout', 'slender': 'Slender', 'dodgeball': 'Dodgeball', 'mario-kart': 'Mario Kart', 'prophunt': 'Prop Hunt', 'class-wars': 'Class Wars',
                             'stop-that-tank': 'Stop that Tank!', 'zombie': 'Zombie'}

gamemode_prefixes: Dict[str, str] = {'ctf': 'ctf', 'tc': 'territorial-control', 'pl': 'payload', 'plr': 'payload-race', 'koth': 'koth', 'sd': 'special-delivery', 'mvm': 'mvm',
                                     'rd': 'beta-map', 'pass': 'passtime', 'pd': 'player-destruction', 'arena': 'arena', 'tr': 'training', 'surf': 'surfing', 'cp': 'control-point',
                                     'trade': 'trading', 'jump': 'jumping', 'dm': 'deathmatch', 'vsh': 'versus-saxton-hale', 'dr': 'deathrun', 'achievement': 'achievement', 'jb': 'breakout',
                                     'slender': 'slender', 'tfdb': 'dodgeball', 'mario': 'mario-kart', 'ph': 'prophunt', 'zs': 'zombie', 'ze': 'zombie', 'zf': 'zombie', 'zm': 'zombie',
                                     'duel': 'deathmatch', 'sn': 'deathmatch', 'ba': 'breakout', 'jail': 'breakout', 'idle': 'trading'}
gamemode_substrings: Dict[str, str] = {'cp_orange': 'cp-orange', 'training': 'training'}

if __name__ == '__main__':
    print(get_map_gamemode(logger.Log(), 'pl_borneo'))
    print(get_map_gamemode(logger.Log(), 'cp_catwalk_a5c'))
