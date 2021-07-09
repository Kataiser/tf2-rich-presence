# Copyright (C) 2018-2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import time
from typing import Dict, List, Optional, Set, Tuple

import gamemodes
import launcher
import localization
import logger
import server
import settings


# this could be in main.py due to being so closely linked to the main logic, but I figured this was better for organization
class GameState:
    def __init__(self, log: Optional[logger.Log] = None, loc: Optional[localization.Localizer] = None):
        self.in_menus: bool = True
        self.tf2_map: str = ''  # these have "tf2_" to avoid conflicting with reserved keywords
        self.tf2_class: str = "unselected"
        self.map_fancy: str = ''
        self.server_address: str = ''
        self.queued_state: str = "Not queued"
        self.hosting: bool = False
        self.player_count: str = ''
        self.kills: str = ''
        self.gamemode: str = ''
        self.gamemode_fancy: str = ''
        self.custom_map: bool = False
        self.game_start_time: int = int(time.time())
        self.map_change_time: int = int(time.time())
        self.map_line: str = ''

        self.update_rpc: bool = True
        # don't track whether the GUI needs to be updated, main just always calls its updates and lets it handle whether or not it needs to set elements
        self.last_server_request_time: float = 0.0
        self.last_server_request_data: Dict[str, str] = {}
        self.last_server_request_address: str = ''
        self.updated_server_state: bool = False
        self.force_zero_map_time: bool = False

        if log:
            self.log: logger.Log = log
        else:
            self.log = logger.Log()
            self.log.error(f"Initialized GameState without a log, defaulting to one at {self.log.filename}")

        if loc:
            self.loc: localization.Localizer = loc
        else:
            self.loc = localization.Localizer()
            self.log.error("Initialized GameState without a localizer")

    def __repr__(self) -> str:
        return f"game_state.GameState ({str(self)})"

    def __str__(self) -> str:
        if self.in_menus:
            return f"in menus, queued=\"{self.queued_state}\""
        else:
            return f"{self.tf2_class} on {self.map_fancy}, gamemode={self.gamemode}, hosting={self.hosting}, queued=\"{self.queued_state}\", server={self.server_address}"

    # mess of logic that generates an activity dict for RPC
    def activity(self) -> dict:
        self.update_rpc = False

        if self.in_menus:
            top_line: str = self.loc.text("In menus")
            bottom_line: str = self.loc.text(self.queued_state)
            small_image: str = 'tf2_logo'
            small_text: str = self.loc.text("Team Fortress 2")
            large_image: str = 'main_menu'
            large_text_base: str = self.loc.text("In menus")

            if self.queued_state == "Queued for Casual":
                large_image = 'casual'
                large_text_base = self.loc.text(self.queued_state)
            elif self.queued_state == "Queued for Competitive":
                large_image = 'comp'
                large_text_base = self.queued_state
            elif "Queued for MvM" in self.queued_state:
                large_image = 'mvm_queued'
                large_text_base = self.loc.text(self.queued_state)
        else:
            if self.tf2_class == "unselected":
                small_image = 'tf2_logo'
                small_text = "Team Fortress 2"
            else:
                small_image = self.tf2_class.lower()
                small_text = self.loc.text(self.tf2_class)

            if self.custom_map:
                large_image = self.gamemode
                large_text_base = self.loc.text(self.gamemode_fancy)
            else:
                large_text_base = self.map_fancy

                if self.tf2_map in map_fallbacks:
                    large_image = f'z_{map_fallbacks[self.tf2_map]}'
                else:
                    large_image = f'z_{self.tf2_map}'

            if self.hosting or self.custom_map:
                top_line = self.map_line
            else:
                top_line = self.get_line('top', True)

            if self.queued_state == "Not queued":
                if self.hosting or self.custom_map:
                    bottom_line = self.get_line('bottom' if self.hosting else 'top', True)
                    # yes this means the bottom line can use the top line setting, but I basically consider it to be the lines shifted down by one and truncated
                else:
                    bottom_line = self.get_line('bottom', True)
            else:
                bottom_line = self.queued_state

            # TODO: fix queued in game

            if not self.updated_server_state:
                self.log.error("Haven't updated server data since last activity generation")
            self.updated_server_state = False

        if not top_line:
            self.log.error("Top line is blank")
            top_line = "In menus"
        if not bottom_line:
            self.log.error("Bottom line is blank")
            bottom_line = "Not queued"
        if not large_image:
            self.log.error("Large image is blank")
            large_image = 'main_menu'
        if not large_text_base:
            self.log.error("Large text base is blank")
            large_text_base = "In menus"
        if not small_image:
            self.log.error("Small image is blank")
            small_image = 'tf2_logo'
        if not small_text:
            self.log.error("Small text is blank")
            small_text = "Team Fortress 2"

        large_text: str = self.loc.text("{0} - TF2 Rich Presence {1}").format(large_text_base, launcher.VERSION)

        return {'details': top_line, 'state': bottom_line, 'timestamps': {'start': self.game_start_time},
                'assets': {'large_image': large_image, 'large_text': large_text, 'small_image': small_image, 'small_text': small_text}}

    # set everything straight from console.log parse results
    def set_bulk(self, state: Tuple[bool, str, str, str, str, bool]):
        prev_state: str = str(self)

        self.set_in_menus(state[0])
        self.set_hosting(state[5])
        self.set_tf2_map(state[1])
        self.set_tf2_class(state[2])
        self.set_queued_state(state[4])
        self.server_address = state[3]  # this isn't a setter because it doesn't directly mean changed server data

        if str(self) != prev_state:  # don't use self.update_rpc because of server data changes not mattering here
            self.log.debug(f"Game state updated from ({prev_state}) to ({str(self)})")

    def set_in_menus(self, in_menus: bool):
        if in_menus != self.in_menus:
            self.in_menus = in_menus
            self.update_rpc = True

            if in_menus:
                self.log.debug("Now in menus, wiping game state")
                self.set_tf2_map('')
                self.set_tf2_class('')
                self.set_hosting(False)
                self.custom_map = False
                self.server_address = ''

    def set_tf2_map(self, tf2_map: str):
        if tf2_map != self.tf2_map:
            self.tf2_map = tf2_map
            self.update_rpc = True

            if tf2_map:
                self.map_change_time = int(time.time())
                self.map_fancy, self.gamemode, self.gamemode_fancy = gamemodes.get_map_gamemode(self.log, self.tf2_map)
                self.custom_map = self.tf2_map == self.map_fancy
                self.map_line = self.loc.text("Map: {0} (hosting)").format(self.map_fancy) if self.hosting else self.loc.text("Map: {0}").format(self.map_fancy)
                self.log.debug(f"Set map to {(self.tf2_map, self.map_fancy, self.gamemode)}, custom map={self.custom_map}")

    def set_tf2_class(self, tf2_class: str):
        tf2_class = tf2_class if tf2_class else "unselected"  # because console.log parse just gives an empty string when unselected

        if tf2_class != self.tf2_class:
            self.tf2_class = tf2_class
            self.update_rpc = True

    def set_player_count(self, player_count: str):
        if player_count != self.player_count:
            self.player_count = player_count
            self.update_rpc = True

    def set_kills(self, kills: str):
        if kills != self.kills:
            self.kills = kills
            self.update_rpc = True

    def set_queued_state(self, queued_state: str):
        if queued_state != self.queued_state:
            self.queued_state = queued_state
            self.update_rpc = True

    def set_hosting(self, hosting: bool):
        if hosting != self.hosting:
            self.hosting = hosting
            self.update_rpc = True

    # modes can include player count, kills, neither, or both
    def update_server_data(self, modes: List[str], usernames: Set[str]):
        self.updated_server_state = True

        if modes:
            if ('Player count' in modes and 'player_count' not in self.last_server_request_data) or ('Kills' in modes and 'kills' not in self.last_server_request_data):
                # for changing server data modes mid-game
                self.clear_server_data_cache()

            server_data: Dict[str, str] = self.get_match_data(self.server_address, modes, usernames)

            # get_match_data doesn't set these (but it could)
            if 'Player count' in modes:
                self.set_player_count(server_data['player_count'])
            else:
                self.set_player_count('')

            if 'Kills' in modes:
                self.set_kills(server_data['kills'])
            else:
                self.set_kills('')
        else:
            self.set_player_count('')
            self.set_kills('')

    # force new server query
    def clear_server_data_cache(self):
        self.log.debug("Clearing server data cache")
        self.last_server_request_time = 0.0
        self.last_server_request_data = {}
        self.last_server_request_address = ''

    # convert seconds to a pretty timestamp, keep leading zeros though
    def time_on_map(self) -> str:
        if self.force_zero_map_time:
            return self.loc.text("Time on map: {0}").format('0:00')
        else:
            seconds_on_map: float = time.time() - self.map_change_time
            time_format: str = '%M:%S' if seconds_on_map <= 3600 else '%H:%M:%S'
            map_time_formatted: str = time.strftime(time_format, time.gmtime(seconds_on_map)).removeprefix('0')
            return self.loc.text("Time on map: {0}").format(map_time_formatted)

    # get either the top or bottom line, based on user settings
    def get_line(self, line: str = 'top', rpc: bool = False) -> str:
        line_setting: str = settings.get('top_line' if line == 'top' else 'bottom_line')

        if line_setting == 'Player count':
            return self.player_count
        elif line_setting == 'Kills':
            return self.kills
        elif line_setting == 'Time on map':
            if rpc:
                self.update_rpc = True  # because new time on map guarantees changed RPC
            return self.time_on_map()
        elif line_setting == 'Class':
            return self.loc.text("Class: {0}").format(self.loc.text(self.tf2_class))

    # get player count and/or user score (kills) from the game server (not actually a getter method)
    def get_match_data(self, *args, **kwargs):
        return server.get_match_data(self, *args, **kwargs)


# because Discord limits to 150 RPC images
map_fallbacks: Dict[str, str] = {'cp_5gorge': 'cp_gorge', 'cp_granary': 'arena_granary', 'arena_nucleus': 'koth_nucleus', 'ctf_foundry': 'cp_foundry', 'arena_sawmill': 'koth_sawmill',
                                 'ctf_sawmill': 'koth_sawmill', 'arena_badlands': 'cp_badlands', 'koth_badlands': 'cp_badlands', 'tr_dustbowl': 'cp_dustbowl',
                                 'ctf_thundermountain': 'pl_thundermountain', 'ctf_well': 'cp_well', 'arena_well': 'cp_well'}
ambiguous_maps: Tuple[str, ...] = ('cp_5gorge', 'cp_gorge', 'arena_granary', 'arena_nucleus', 'ctf_foundry', 'arena_sawmill', 'koth_sawmill', 'ctf_sawmill',  'arena_badlands', 'cp_badlands',
                                   'koth_badlands',  'tr_dustbowl', 'ctf_thundermountain', 'ctf_well', 'cp_well', 'arena_well')
