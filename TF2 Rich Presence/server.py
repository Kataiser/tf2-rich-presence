# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import socket
import time
import traceback

import a2s

import settings


# get player count or user score (kills) from the game server
def get_match_data(self, address: str, mode: str, force: bool = False) -> str:
    RATE_LIMIT: int = 10
    time_since_last: float = time.time() - self.last_server_request_time

    if time_since_last < RATE_LIMIT and self.last_server_request_address == address and not force:
        self.log.debug(f"Skipping getting server data ({round(time_since_last, 1)} < {RATE_LIMIT}), persisting {self.last_server_request_data}")
        return self.last_server_request_data
    else:
        self.last_server_request_time = time.time()
        self.last_server_request_address = address
        self.log.debug(f"Getting match data from server ({address}) with mode {mode}")

        if mode not in ('Player count', 'Kills'):
            self.log.error(f"Match info mode is invalid ({mode})")
            self.last_server_request_data = ""
            self.last_server_request_time -= RATE_LIMIT
            return self.last_server_request_data
        if ':' not in address:
            self.log.error(f"Server address is invalid ({address})")
            self.last_server_request_data = ""
            self.last_server_request_time -= RATE_LIMIT
            return self.last_server_request_data

        ip: str
        socket_: str
        ip, socket_ = address.split(':')

        try:
            if mode == 'Player count':
                server_info = a2s.info((ip, int(socket_)), timeout=settings.get('request_timeout'))
                # there's a decent amount of extra data here that isn't used but could be (server name, bot count, tags, etc.)
            else:
                players_info = a2s.players((ip, int(socket_)), timeout=settings.get('request_timeout'))
        except (a2s.BrokenMessageError, a2s.BrokenMessageError, socket.timeout, socket.gaierror, ConnectionRefusedError):
            self.log.error(f"Couldn't get server info: {traceback.format_exc()}")
            self.last_server_request_data = ""
            self.last_server_request_time -= RATE_LIMIT
            return self.last_server_request_data

        if mode == 'Player count':  # probably not worth doing an extra request each time if using kills mode
            if server_info.protocol != 17:
                self.log.error(f"Server protocol is {server_info.protocol}, not 17")
            if server_info.game_id != 440:
                self.log.error(f"Server game ID is {server_info.game_id}, not 440")
            if server_info.game != 'Team Fortress':
                self.log.error(f"Server game is {server_info.folder}, not Team Fortress")

        if mode == 'Player count':
            if 'valve' in server_info.keywords:
                max_players: int = 24
            else:
                max_players = server_info.max_players

            self.last_server_request_data = self.loc.text("Players: {0}/{1}").format(server_info.player_count, max_players)
            return self.last_server_request_data
        else:
            for player in players_info:
                if player.name in self.valid_usernames:
                    self.last_server_request_data = self.loc.text("Kills: {0}").format(player.score)
                    return self.last_server_request_data

            self.log.error("User doesn't seem to be in the server")
            self.last_server_request_data = self.loc.text("Kills: {0}").format(0)
            return self.last_server_request_data
