# Copyright (C) 2018-2022 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import time
from typing import Dict, Optional, Tuple

import console_log
import gamemodes
import gui
import launcher
import localization
import logger
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
        self.server_name: str = ''
        self.player_count: str = ''
        self.server_players: tuple[int, int] = (0, 0)
        self.gamemode: str = ''
        self.gamemode_fancy: str = ''
        self.custom_map: bool = False
        self.game_start_time: int = int(time.time())
        self.map_change_time: int = int(time.time())
        self.map_line: str = ''

        self.update_rpc: bool = True
        # don't track whether the GUI needs to be updated, main just always calls its updates and lets it handle whether or not it needs to set elements
        self.force_zero_map_time: bool = False
        self.console_log_file_position: int = 0

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
            return f"{self.tf2_class} on {self.map_fancy}, gamemode={self.gamemode}, hosting={self.hosting}, queued=\"{self.queued_state}\", server=\"{self.server_name}\""

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

            if self.tf2_map in gui.missing_fg_maps:
                self.log.error(f"gui_images/fg_maps/{self.tf2_map}.webp doesn't exist, using gamemode image for Discord")
                force_gamemode_image = True
            else:
                force_gamemode_image = False

            if self.custom_map or force_gamemode_image:
                large_image = self.gamemode

                if self.gamemode in gamemodes.localization_excluded:
                    large_text_base = self.gamemode_fancy
                else:
                    large_text_base = self.loc.text(self.gamemode_fancy)
            else:
                large_text_base = self.map_fancy

                if self.tf2_map in map_fallbacks:
                    large_image = f'z_{map_fallbacks[self.tf2_map]}'
                else:
                    large_image = f'z_{self.tf2_map}'

            if self.hosting or self.custom_map or force_gamemode_image:
                top_line = self.map_line
            else:
                top_line = self.get_line('top', True)

            if self.queued_state == "Not queued":
                if self.hosting or self.custom_map or force_gamemode_image:
                    bottom_line = self.get_line('bottom' if self.hosting else 'top', True)
                    # yes this means the bottom line can use the top line setting, but I basically consider it to be the lines shifted down by one and truncated
                else:
                    bottom_line = self.get_line('bottom', True)
            else:
                bottom_line = self.queued_state

            # TODO: fix queued in game

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
    def set_bulk(self, state: console_log.ConsoleLogParsed):
        prev_state: str = str(self)

        self.set_in_menus(state.in_menus)
        self.set_hosting(state.hosting)
        self.set_tf2_map(state.tf2_map)
        self.set_tf2_class(state.tf2_class)
        self.set_queued_state(state.queued_state)
        self.set_server_name(state.server_name)
        self.set_player_count(state.server_players, state.server_players_max)
        self.console_log_file_position = state.file_position

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
                self.set_server_name('')
                self.set_player_count(0, 0)
                self.custom_map = False

    def set_tf2_map(self, tf2_map: str):
        if tf2_map != self.tf2_map:
            self.tf2_map = tf2_map
            self.update_rpc = True

            if tf2_map:
                self.map_change_time = int(time.time())
                self.map_fancy, self.gamemode, self.gamemode_fancy, self.custom_map = gamemodes.get_map_gamemode(self.log, self.tf2_map)
                self.map_line = self.loc.text("Map: {0} (hosting)").format(self.map_fancy) if self.hosting else self.loc.text("Map: {0}").format(self.map_fancy)
                self.log.debug(f"Set map to {(self.tf2_map, self.map_fancy, self.gamemode)}, custom map={self.custom_map}")

    def set_tf2_class(self, tf2_class: str):
        tf2_class = tf2_class if tf2_class else "unselected"  # because console.log parse just gives an empty string when unselected

        if tf2_class != self.tf2_class:
            self.tf2_class = tf2_class
            self.update_rpc = True

    def set_server_name(self, server_name: str):
        if server_name != self.server_name:
            self.server_name = server_name
            self.update_rpc = True

    def set_player_count(self, server_players: int, server_players_max: int):
        player_count = self.loc.text("Players: {0}/{1}").format(server_players, server_players_max)

        if player_count != self.player_count:
            self.player_count = player_count
            self.server_players = (server_players, server_players_max)

            if 'Player count' in (settings.get('top_line'), settings.get('bottom_line')):
                self.update_rpc = True

    def set_queued_state(self, queued_state: str):
        if queued_state != self.queued_state:
            self.queued_state = queued_state
            self.update_rpc = True

    def set_hosting(self, hosting: bool):
        if hosting != self.hosting:
            self.hosting = hosting
            self.update_rpc = True

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
    def get_line(self, line: str = 'top', rpc: bool = False) -> Optional[str]:
        line_setting: str = settings.get('top_line' if line == 'top' else 'bottom_line')

        if line_setting == 'Server name':
            return self.server_name
        elif line_setting == 'Player count':
            return self.player_count
        elif line_setting == 'Time on map':
            if rpc:
                self.update_rpc = True  # because new time on map guarantees changed RPC

            return self.time_on_map()
        elif line_setting == 'Class':
            return self.loc.text("Class: {0}").format(self.loc.text(self.tf2_class))
        elif line_setting == 'Map':
            return self.map_fancy
        else:
            self.log.error(f"Couldn't get {line} line for activity ({line_setting=})")


# because Discord limits to 150 RPC images
# ^ update: 300 now, but still might as well keep the image count down a little
map_fallbacks: Dict[str, str] = {'cp_granary': 'arena_granary', 'arena_nucleus': 'koth_nucleus', 'arena_sawmill': 'koth_sawmill', 'arena_badlands': 'cp_badlands',
                                 'koth_badlands': 'cp_badlands', 'tr_dustbowl': 'cp_dustbowl', 'ctf_thundermountain': 'pl_thundermountain', 'ctf_well': 'cp_well', 'arena_well': 'cp_well'}
ambiguous_maps: Tuple[str, ...] = ('cp_5gorge', 'cp_gorge', 'arena_granary', 'arena_nucleus', 'ctf_foundry', 'arena_sawmill', 'koth_sawmill', 'ctf_sawmill',  'arena_badlands', 'cp_badlands',
                                   'koth_badlands',  'tr_dustbowl', 'ctf_thundermountain', 'ctf_well', 'cp_well', 'arena_well', 'vsh_nucleus')
