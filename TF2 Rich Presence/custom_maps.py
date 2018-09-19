import json
import os
import time
import traceback
from typing import TextIO, Dict, KeysView, List, Tuple, Union

import requests
from requests import Response

import logger
import settings


# uses teamwork.tf's API to find the gamemode of a custom map
def find_custom_map_gamemode(log, map_filename: str, timeout: float = settings.get('request_timeout')) -> Tuple[str, str]:
    if map_filename == '':
        log.error("Map filename is blank")
        return 'unknown_map', 'Unknown gamemode'

    log.debug(f"Finding gamemode for custom map: {map_filename}")
    seconds_since_epoch_now: int = int(time.time())

    # to avoid constantly using internet, each map is cached to custom_maps.json
    custom_map_gamemodes = access_custom_maps_cache()
    log.debug(f"{len(custom_map_gamemodes)} maps cached: {list(custom_map_gamemodes.keys())}")

    # look for map in loaded cache
    try:
        cached_data: list = custom_map_gamemodes[map_filename]
        if seconds_since_epoch_now - cached_data[2] <= settings.get('map_invalidation_hours') * 3600:  # custom map cache expiration
            log.debug(f"{map_filename}'s gamemode is {list(cached_data[:-1])} (from cache)")
            return cached_data[0], cached_data[1]
        else:
            log.debug(f"Outdated cache ({cached_data[2]} -> {seconds_since_epoch_now})")
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
        try:
            r: Response = requests.get(f'https://teamwork.tf/api/v1/map-stats/map/{map_filename}?key={settings.get_api_key("teamwork")}', timeout=timeout)
            map_info: dict = r.json()
            log.debug(f"API lookup took {time.perf_counter() - before_request_time} secs")
        except requests.ConnectTimeout:
            log.debug("Timeout connecting to teamwork.tf, defaulting to \"Unknown gamemode\" and not caching")
            first_gamemode: str = 'unknown_map'
            first_gamemode_fancy: str = 'Unknown gamemode'
            return first_gamemode, first_gamemode_fancy
        except Exception:
            log.error(f"Error connecting to teamwork.tf: {traceback.format_exc()}")
            return 'unknown_map', 'Unknown gamemode'

        # parses the api result
        try:
            log.debug(f"All gamemodes found: {map_info['all_gamemodes']}")
            map_gamemode: List[str] = map_info['all_gamemodes']
            for gamemode in map_gamemode:
                if gamemode in gamemodes_keys:
                    log.debug(f"Using gamemode {gamemode}")
                    first_gamemode_fancy: str = gamemodes[gamemode]
                    # modify the cache locally
                    custom_map_gamemodes[map_filename] = [gamemode, first_gamemode_fancy, seconds_since_epoch_now]

                    # load the cache to actually modify it
                    access_custom_maps_cache(dict_input=custom_map_gamemodes)

                    # ex: 'mvm', 'Mann vs. Machine'
                    log.debug(f"{map_filename}'s gamemode is {[gamemode, first_gamemode_fancy]} (fresh from teamwork.tf)")
                    return gamemode, first_gamemode_fancy
        except KeyError:
            log.error(f"Couldn't find gamemode for that custom map (KeyError while parsing the api result). Full json response: \n{map_info}")

        # unrecognized gamemodes
        first_gamemode: str = 'unknown_map'
        first_gamemode_fancy: str = 'Unknown gamemode'
        custom_map_gamemodes[map_filename] = [first_gamemode, first_gamemode_fancy, seconds_since_epoch_now]

        access_custom_maps_cache(dict_input=custom_map_gamemodes)

        log.debug(f"{map_filename}'s gamemode is {[first_gamemode, first_gamemode_fancy]} (fresh from the API)")
        return first_gamemode, first_gamemode_fancy


# reads or writes custom_maps.json, the cache of custom maps
def access_custom_maps_cache(dict_input: Union[dict, None] = None) -> dict:
    if dict_input is None:
        file_mode: str = 'r'
    else:
        file_mode: str = 'w'

    try:
        custom_maps_cache_file: TextIO = open(os.path.join('resources', 'custom_maps.json'), file_mode)
    except FileNotFoundError:
        custom_maps_cache_file: TextIO = open('custom_maps.json', file_mode)

    if dict_input is None:
        loaded_cache: dict = json.load(custom_maps_cache_file)
        custom_maps_cache_file.close()
        return loaded_cache
    else:
        json.dump(dict_input, custom_maps_cache_file, indent=4)
        custom_maps_cache_file.close()


if __name__ == '__main__':
    print(find_custom_map_gamemode(logger.Log(), 'cp_catwalk_a5c'))
