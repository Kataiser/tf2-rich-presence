# Copyright (C) 2018-2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import socket
import time
import traceback
from typing import Dict, List, Optional, Set

import a2s

import localization
import settings


# get player count and/or user score (kills) from the game server
def get_match_data(self, address: str, modes: List[str], usernames: Optional[Set[str]] = None, force: bool = False) -> Dict[str, str]:
    rate_limit: int = int(settings.get('server_rate_limit'))
    time_since_last: float = time.time() - self.last_server_request_time

    if time_since_last < rate_limit and self.last_server_request_address == address and not force:
        self.log.debug(f"Skipping getting server data ({round(time_since_last, 1)} < {rate_limit}), persisting {self.last_server_request_data}")
        return self.last_server_request_data
    else:
        self.last_server_request_time = time.time()
        self.last_server_request_address = address
        self.log.debug(f"Getting match data from server ({address}) with mode(s) {modes}")

        if ':' not in address:
            if address:
                self.log.error(f"Server address ({address}) is invalid")
            else:
                self.log.debug(f"Server address is blank, assuming hosting")

            self.last_server_request_data = unknown_data(self.loc, modes)
            self.last_server_request_time -= rate_limit  # ignores rate limit
            return self.last_server_request_data

        ip: str
        ip_socket: str
        ip, ip_socket = address.split(':')
        server_data: Dict[str, str] = {}

        try:
            if 'Player count' in modes:
                server_info = a2s.info((ip, int(ip_socket)), timeout=settings.get('request_timeout'))
                # there's a decent amount of extra data here that isn't used but could be (server name, bot count, tags, etc.)
            if 'Kills' in modes:
                players_info = a2s.players((ip, int(ip_socket)), timeout=settings.get('request_timeout'))
        except (a2s.BrokenMessageError, a2s.BrokenMessageError, socket.gaierror, ConnectionRefusedError):
            self.log.error(f"Couldn't get server info: {traceback.format_exc()}")
            self.last_server_request_data = unknown_data(self.loc, modes)
            self.last_server_request_time -= rate_limit
            return self.last_server_request_data
        except socket.timeout:
            self.log.debug("Timed out getting server info, persisting previous data")
            self.last_server_request_time -= rate_limit
            return self.last_server_request_data

        if 'Player count' in modes:
            # do some validation, probably not worth doing an extra request each time if only using kills mode
            if server_info.protocol != 17:
                self.log.error(f"Server protocol is {server_info.protocol}, not 17")
            if server_info.game_id != 440:
                self.log.error(f"Server game ID is {server_info.game_id}, not 440")
            if server_info.game not in ('Team Fortress', 'tf'):
                self.log.error(f"Server game is {server_info.folder}, not Team Fortress or tf")

            if 'valve' in server_info.keywords:
                max_players: int = 24
            else:
                max_players = server_info.max_players

            player_count: str = self.loc.text("Players: {0}/{1}").format(server_info.player_count, max_players)
            self.log.debug(f"Got player count from server: \"{player_count}\"")
            server_data['player_count'] = player_count

        if 'Kills' in modes:
            kills: str = ""

            if not usernames:
                self.log.error("Trying to get kills data without usernames")
                usernames = set()

            for player in players_info:
                if player.name in usernames:
                    kills: str = self.loc.text("Kills: {0}").format(player.score)
                    self.log.debug(f"Got kill count from server: \"{kills}\"")
                    break

            if not kills:
                self.log.debug("User doesn't seem to be in the server, assuming still loading in")
                kills = self.loc.text("Kills: {0}").format(0)
                self.last_server_request_time -= rate_limit

            server_data['kills'] = kills

        self.last_server_request_data = server_data
        return self.last_server_request_data


def unknown_data(loc: localization.Localizer, modes: List[str]) -> Dict[str, str]:
    server_data = {}

    if 'Player count' in modes:
        server_data['player_count'] = loc.text("Players: {0}/{1}").format("?", "?")
    if 'Kills' in modes:
        server_data['kills'] = loc.text("Kills: {0}").format("?")

    return server_data
