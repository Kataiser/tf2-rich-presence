import json
import os
import time
from typing import TextIO, Dict, KeysView, List

import requests
from requests import Response

import logger as log


# uses teamwork.tf's API to find the gamemode of a custom map
def find_custom_map_gamemode(map_filename):
    log.debug(f"Finding gamemode for custom map: {map_filename}")
    days_since_epoch_now: int = int(time.time() / 86400)

    # to avoid constantly using internet, each map is cached to custom_maps.json
    try:
        custom_maps_db: TextIO = open(os.path.join('resources', 'custom_maps.json'), 'r')
    except FileNotFoundError:
        custom_maps_db = open('custom_maps.json', 'r')

    custom_map_gamemodes: dict = json.load(custom_maps_db)
    custom_maps_db.close()
    log.debug(f"{len(custom_map_gamemodes)} maps cached: {list(custom_map_gamemodes.keys())}")

    # look for map in loaded cache
    try:
        cached_data: list = custom_map_gamemodes[map_filename]
        if days_since_epoch_now - cached_data[2] <= 5:  # custom map cache expires after 5 days
            log.debug(f"{map_filename}'s gamemode is {list(cached_data[:-1])} (from cache)")
            return cached_data[:-1]
        else:
            log.debug(f"Outdated cache ({cached_data[2]} -> {days_since_epoch_now})")
            raise KeyError
    except KeyError:
        gamemodes: Dict[str, str] = {'ctf': 'Capture the Flag', 'control-point': 'Control Point', 'attack-defend': 'Attack/Defend', 'medieval-mode': 'Attack/Defend (Medieval Mode)',
                                     'territorial-control': 'Territorial Control', 'payload': 'Payload', 'payload-race': 'Payload Race', 'koth': 'King of the Hill',
                                     'special-delivery': 'Special Delivery', 'mvm': 'Mann vs. Machine', 'beta-map': 'Robot Destruction', 'mannpower': 'Mannpower', 'passtime': 'PASS Time',
                                     'player-destruction': 'Player Destruction', 'arena': 'Arena', 'training': 'Training', 'surfing': 'Surfing', 'trading': 'Trading', 'jumping': 'Jumping',
                                     'deathmatch': 'Deathmatch', 'cp-orange': 'Orange', 'versus-saxton-hale': 'Versus Saxton Hale', 'deathrun': 'Deathrun', 'achievement': 'Achievement',
                                     'breakout': 'Jail Breakout', 'slender': 'Slender', 'dodgeball': 'Dodgeball', 'mario-kart': 'Mario Kart'}
        gamemodes_keys: KeysView[str] = gamemodes.keys()

        before_request_time: float = time.perf_counter()
        r: Response = requests.get('https://teamwork.tf/api/v1/map-stats/map/{}?key=nvsDhCxoVHcSiAZ7pFBTWbMy91RaIYgq'.format(map_filename))
        map_info: dict = r.json()
        log.debug(f"API lookup took {time.perf_counter() - before_request_time} secs")

        # parses the api result
        log.debug(f"All gamemodes found: {map_info['all_gamemodes']}")
        map_gamemode: List[str] = map_info['all_gamemodes']
        for gamemode in map_gamemode:
            if gamemode in gamemodes_keys:
                log.debug(f"Using gamemode {gamemode}")
                first_gamemode_fancy: str = gamemodes[gamemode]
                # modify the cache locally
                custom_map_gamemodes[map_filename] = [gamemode, first_gamemode_fancy, days_since_epoch_now]

                # load the cache to actually modify it
                try:
                    custom_maps_db = open(os.path.join('resources', 'custom_maps.json'), 'w')
                except FileNotFoundError:
                    custom_maps_db = open('custom_maps.json', 'w')

                json.dump(custom_map_gamemodes, custom_maps_db, indent=4)
                custom_maps_db.close()

                # ex: 'mvm', 'Mann vs. Machine'
                log.debug(f"{map_filename}'s gamemode is {[gamemode, first_gamemode_fancy]} (fresh from teamwork.tf)")
                return gamemode, first_gamemode_fancy

        # unrecognized gamemodes
        first_gamemode: str = 'unknown_map'
        first_gamemode_fancy: str = 'Unknown gamemode'
        custom_map_gamemodes[map_filename] = [first_gamemode, first_gamemode_fancy, days_since_epoch_now]

        try:
            custom_maps_db = open(os.path.join('resources', 'custom_maps.json'), 'w')
        except FileNotFoundError:
            custom_maps_db = open('custom_maps.json', 'w')

        json.dump(custom_map_gamemodes, custom_maps_db, indent=4)
        custom_maps_db.close()

        log.debug(f"{map_filename}'s gamemode is {[first_gamemode, first_gamemode_fancy]} (fresh from the API)")
        return first_gamemode, first_gamemode_fancy
