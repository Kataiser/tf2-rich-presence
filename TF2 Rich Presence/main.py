"""Discord Rich Presence for Team Fortress 2"""

# TF2 Rich Presence {tf2rpvnum}
# https://github.com/Kataiser/tf2-rich-presence
#
# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import copy
import datetime
import json
import os
import platform
import time
import traceback
from typing import Any, Dict, List, TextIO, Tuple, Union

import colorama
import psutil
from discoIPC import ipc

import configs
import console_log
import custom_maps
import localization
import logger
import processes
import settings
import utils

__author__ = "Kataiser"
__copyright__ = "Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors"
__license__ = "GPL-3.0"
__email__ = "Mecharon1.gm@gmail.com"


def launch():
    log_main = logger.Log()
    log_main.to_stderr = True

    try:
        app = TF2RichPresense(log_main)
        log_main.info("Starting TF2 Rich Presence {tf2rpvnum}")
        log_main.cleanup(20)
        log_main.debug(f"CPU: {psutil.cpu_count(logical=False)} cores, {psutil.cpu_count()} threads")

        platform_info = {'architecture': platform.architecture, 'machine': platform.machine, 'system': platform.system, 'platform': platform.platform,
                         'processor': platform.processor, 'python_version_tuple': platform.python_version_tuple}
        for platform_part in platform_info:
            try:
                if platform_part == 'platform':
                    platform_info[platform_part] = platform_info[platform_part](aliased=True)
                else:
                    platform_info[platform_part] = platform_info[platform_part]()
            except Exception:
                log_main.error(f"Exception during platform.{platform_part}(), skipping\n{traceback.format_exc()}")
        log_main.debug(f"Platform: {platform_info}")

        default_settings = settings.get_setting_default(return_all=True)
        current_settings = settings.access_registry()
        if current_settings == default_settings:
            log_main.debug("Current settings are default")
        else:
            log_main.debug(f"Non-default settings: {settings.compare_settings(default_settings, current_settings)}")

        app.run()
    except (KeyboardInterrupt, SystemExit):
        raise SystemExit
    except Exception:
        try:
            formatted_exception = traceback.format_exc()
            log_main.critical(formatted_exception)
        except NameError:
            pass

        raise


class TF2RichPresense:
    def __init__(self, log):
        self.log = log
        self.activity: Dict[str, Union[str, Dict[str, int], Dict[str, str]]] = \
            {'details': 'In menus',  # this is what gets modified and sent to Discord via discoIPC
             'timestamps': {'start': int(time.time())},
             'assets': {'small_image': 'tf2_icon_small', 'small_text': 'Team Fortress 2', 'large_image': 'main_menu', 'large_text': 'Main menu'},
             'state': ''}
        self.old_activity1: Dict = {}  # for the console output
        self.old_activity2: Dict = {}  # for sending to Discord
        self.activity_translated = {}
        self.client_connected: bool = False
        self.client = None
        self.test_state = 'init'
        self.should_mention_discord = True
        self.should_mention_tf2 = True
        self.last_notify_time = None
        self.has_checked_class_configs = False
        self.process_scanner = processes.ProcessScanner(self.log)
        self.loc = localization.Localizer(self.log, settings.get('language'))
        self.current_time_formatted = ""
        self.current_map = None  # don't trust this variable
        self.time_changed_map = time.time()
        self.has_seen_kataiser = False
        self.old_console_log_mtime = None
        self.old_console_log_interpretation = ('', '')

        # load maps database
        try:
            maps_db: TextIO = open(os.path.join('resources', 'maps.json'), 'r')
        except FileNotFoundError:
            maps_db: TextIO = open('maps.json', 'r')

        self.map_gamemodes: dict = json.load(maps_db)
        maps_db.close()

        self.loop_iteration: int = 0

    def __repr__(self):
        return f"main.TF2RichPresense (state={self.test_state})"

    def run(self):
        while True:
            self.loop_body()

            # rich presence only updates every 15 seconds, but it listens constantly so sending every 2 seconds (by default) is fine
            sleep_time = settings.get('wait_time')
            self.log.debug(f"Sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)

    # the main logic. runs every 2 seconds (by default)
    def loop_body(self):
        self.loop_iteration += 1
        self.log.debug(f"Loop iteration this app session: {self.loop_iteration}")

        self.old_activity1 = copy.deepcopy(self.activity)
        self.old_activity2 = copy.deepcopy(self.activity)
        if self.loc.text("Time on map: {0}").replace('{0}', '') in self.old_activity1['state']:
            self.old_activity1['state'] = ''

        # this as a one-liner is beautiful :)
        p_data = self.process_scanner.scan()

        if p_data['Steam']['running'] and len(p_data) == 3:
            # reads a steam config file
            valid_usernames: List[str] = configs.steam_config_file(self.log, p_data['Steam']['path'])

        # used for display only
        current_time = datetime.datetime.now().strftime('%I:%M:%S %p')
        self.current_time_formatted = current_time[1:] if current_time.startswith('0') else current_time

        if p_data['TF2']['running'] and p_data['Discord']['running']:
            if not self.has_checked_class_configs:
                # modifies a few tf2 config files
                configs.class_config_files(self.log, p_data['TF2']['path'])
                self.has_checked_class_configs = True

            console_log_path = os.path.join(p_data['TF2']['path'], 'tf', 'console.log')
            top_line, bottom_line = self.interpret_console_log(console_log_path, valid_usernames, p_data['TF2']['time'])
            # TODO: use a state machine and much more consistent var names

            if top_line == 'In menus':
                # in menus displays the main menu
                self.test_state = 'menus'
                self.current_map = None
                self.activity['assets']['small_image'] = 'tf2_icon_small'
                self.activity['assets']['small_text'] = 'Team Fortress 2'

                if bottom_line == 'Queued for Casual':
                    self.activity['assets']['large_image'] = 'casual'
                    self.activity['assets']['large_text'] = bottom_line
                elif bottom_line == 'Queued for Competitive':
                    self.activity['assets']['large_image'] = 'comp'
                    self.activity['assets']['large_text'] = bottom_line
                elif 'Queued for MvM' in bottom_line:
                    self.activity['assets']['large_image'] = 'mvm_queued'
                    self.activity['assets']['large_text'] = bottom_line
                else:
                    self.activity['assets']['large_image'] = 'main_menu'
                    self.activity['assets']['large_text'] = 'Main menu'
            elif top_line != '':  # not in menus = in a game
                self.test_state = 'in game'
                class_pic_type: str = settings.get('class_pic_type').lower()

                if class_pic_type == 'none, use tf2 logo' or bottom_line == 'unselected':
                    self.activity['assets']['small_image'] = 'tf2_icon_small'
                    self.activity['assets']['small_text'] = 'Team Fortress 2'
                else:
                    small_class_image = f'{bottom_line.lower()}_{class_pic_type}'
                    self.log.debug(f"Setting class small image to {small_class_image}")

                    self.activity['assets']['small_image'] = small_class_image
                    self.activity['assets']['small_text'] = bottom_line

                if settings.get('map_time'):
                    if self.current_map != top_line:  # top_line means the current map here... I should probably refactor that
                        self.current_map = top_line
                        self.time_changed_map = time.time()

                    # convert seconds to a pretty timestamp
                    seconds_on_map = time.time() - self.time_changed_map
                    time_format = '%M:%S' if seconds_on_map <= 3600 else '%H:%M:%S'
                    map_time_formatted = time.strftime(time_format, time.gmtime(seconds_on_map))

                    # I know I could just set the start time in activity, but I'd rather that always meant time with the game open
                    class_line = self.loc.text("Class: {0}").format(self.loc.text(bottom_line))
                    bottom_line = self.loc.text("Time on map: {0}").format(map_time_formatted)
                else:
                    bottom_line = self.loc.text("Class: {0}").format(self.loc.text(bottom_line))

                try:
                    map_fancy, current_gamemode, gamemode_fancy = self.map_gamemodes[top_line]
                    map_out = map_fancy
                    self.activity['assets']['large_image'] = current_gamemode
                    self.activity['assets']['large_text'] = gamemode_fancy
                except KeyError:
                    # is a custom map
                    custom_gamemode, custom_gamemode_fancy_english = custom_maps.find_custom_map_gamemode(self.log, top_line, False)
                    custom_gamemode_fancy = self.loc.text(custom_gamemode_fancy_english)
                    map_out = top_line
                    self.activity['assets']['large_image'] = custom_gamemode
                    self.activity['assets']['large_text'] = "{0} {1}".format(custom_gamemode_fancy, self.loc.text("[custom/community map]"))

                top_line = self.loc.text("Map: {0}").format(map_out)
            else:
                # console.log is empty or close to empty
                pass

            self.activity['details'] = top_line
            self.activity['state'] = bottom_line
            self.activity['timestamps']['start'] = p_data['TF2']['time']

            activity_comparison = copy.deepcopy(self.activity)
            if self.loc.text("Time on map: {0}").replace('{0}', '') in activity_comparison['state']:
                activity_comparison['state'] = ''

            if activity_comparison != self.old_activity1:
                # output to terminal, just for monitoring
                print(f"{self.current_time_formatted}{self.generate_delta(self.last_notify_time)}{colorama.Style.BRIGHT}")

                if [d for d in ('Queued', 'Main menu') if d in self.activity['assets']['large_text']]:
                    # if queued or on the main menu, simplify cmd output
                    print(self.loc.text(self.activity['details']))
                else:
                    print(f"{self.loc.text(self.activity['details'])} ({self.loc.text(self.activity['assets']['large_text'])})")

                    if settings.get('map_time'):
                        print(class_line)  # this means the current class. god this desperately needs a refactor

                print(self.loc.text(self.activity['state']))
                print(colorama.Style.RESET_ALL, end='')

                time_elapsed = datetime.timedelta(seconds=int(time.time() - p_data['TF2']['time']))
                print(self.loc.text("{0} elapsed").format(str(time_elapsed).replace('0:', '', 1)))
                print()

                self.log.debug(f"Activity changed, outputting (old: {self.old_activity1}, new: {self.activity})")
                self.last_notify_time = time.time()
            else:
                self.log.debug("Activity hasn't changed, not outputting")

            if self.activity != self.old_activity2:
                # send everything to discord
                large_text_base = self.activity['assets']['large_text']
                self.activity['assets']['large_text'] += self.loc.text(" - TF2 Rich Presence {0}").format('{tf2rpvnum}')
                self.send_rpc_activity()
                self.activity['assets']['large_text'] = large_text_base
                # this gets reset because the old activity doesn't have it
            else:
                self.log.debug("Activity hasn't changed, not sending to Discord")

            if not self.client_connected:
                self.log.critical("self.client is disconnected when it shouldn't be")
        elif not p_data['TF2']['running']:
            self.test_state = 'no tf2'

            if self.client_connected:
                try:
                    self.log.debug("Disconnecting client")
                    self.client.disconnect()  # doesn't work...
                    client_state = (self.client.client_id, self.client.connected, self.client.ipc_path, self.client.pid, self.client.platform, self.client.socket)
                    self.log.debug(f"client state after disconnect: {client_state}")
                except Exception as err:
                    self.log.error(f"client error while disconnecting: {err}")

                self.log.info("Restarting")
                del self.log
                raise SystemExit  # ...but this does
            else:
                self.log.info(f"TF2 isn't running (mentioning to user: {self.should_mention_tf2})")

                if self.should_mention_tf2:
                    print(f'{self.current_time_formatted}{self.generate_delta(self.last_notify_time)}{colorama.Style.BRIGHT}')
                    print(self.loc.text("Team Fortress 2 isn't running"))
                    print(colorama.Style.RESET_ALL)
                    self.should_mention_discord = True
                    self.should_mention_tf2 = False
                    self.last_notify_time = time.time()

            # to prevent connecting when already connected
            self.client_connected = False
        else:
            # Discord isn't running
            self.test_state = 'no discord'
            self.log.info(f"Discord isn't running (mentioning to user: {self.should_mention_discord})")

            if self.should_mention_discord:
                print(f'{self.current_time_formatted}{self.generate_delta(self.last_notify_time)}{colorama.Style.BRIGHT}')
                print(self.loc.text("Discord isn't running"))
                print(colorama.Style.RESET_ALL)
                self.should_mention_discord = False
                self.should_mention_tf2 = True
                self.last_notify_time = time.time()

        return self.client_connected, self.client

    # reads a console.log and returns current map and class
    def interpret_console_log(self, *args, **kwargs) -> tuple:
        return console_log.interpret(self, *args, **kwargs)

    # generate text that displays the difference between now and old_time
    def generate_delta(self, old_time: float) -> str:
        if old_time:
            time_diff = round(time.time() - old_time)

            if time_diff > 86400:
                divided_diff = round(time_diff / 86400, 1)
                if divided_diff == 1:
                    return f" (+{divided_diff} {self.loc.text('day')})"
                else:
                    return f" (+{divided_diff} {self.loc.text('days')})"
            elif time_diff > 3600:
                divided_diff = round(time_diff / 3600, 1)
                if divided_diff == 1:
                    return f" (+{divided_diff} {self.loc.text('hour')})"
                else:
                    return f" (+{divided_diff} {self.loc.text('hours')})"
            elif time_diff > 60:
                divided_diff = round(time_diff / 60, 1)
                if divided_diff == 1:
                    return f" (+{divided_diff} {self.loc.text('minute')})"
                else:
                    return f" (+{divided_diff} {self.loc.text('minutes')})"
            else:
                if time_diff == 1:
                    return f" (+{time_diff} {self.loc.text('second')})"
                else:
                    return f" (+{time_diff} {self.loc.text('seconds')})"
        else:
            return ""

    # sends localized RPC data, connecting to Discord initially if need be
    def send_rpc_activity(self):
        try:
            if not self.client_connected:
                # connects to Discord and sends first status, starts on main menu
                self.client = ipc.DiscordIPC(utils.get_api_key('discord'))
                self.client.connect()
                client_state: Tuple[Any, bool, str, int, str, Any] = (
                    self.client.client_id, self.client.connected, self.client.ipc_path, self.client.pid, self.client.platform, self.client.socket)
                self.log.debug(f"Initial RPC client state: {client_state}")

            # localize activity
            self.activity_translated = copy.deepcopy(self.activity)
            self.activity_translated['details'] = self.loc.text(self.activity['details'])
            self.activity_translated['assets']['small_text'] = self.loc.text(self.activity['assets']['small_text'])
            self.activity_translated['assets']['large_text'] = self.loc.text(self.activity['assets']['large_text'])

            # stop DB.json spam as the map time increases
            if settings.get('map_time') and self.test_state == 'in game':
                self.log.debug("Not localizing activity['state'] due to map time")
            else:
                self.activity_translated['state'] = self.loc.text(self.activity['state'])

            self.client.update_activity(self.activity_translated)
            self.log.info(f"Sent over RPC: {self.activity_translated}")
            client_state = (self.client.client_id, self.client.connected, self.client.ipc_path, self.client.pid, self.client.platform, self.client.socket)
            self.log.debug(f"client state: {client_state}")
            self.client_connected = True
        except Exception as client_connect_error:
            if str(client_connect_error) in ("Can't send data to Discord via IPC.", "Can't connect to Discord Client."):
                # often happens when Discord is in the middle of starting up
                self.log.error(str(client_connect_error))

                print(f'{self.current_time_formatted}{colorama.Style.BRIGHT}')
                print(self.loc.text("Can't connect to Discord for Rich Presence."))
                print(colorama.Style.RESET_ALL)

                time.sleep(settings.get('wait_time'))
                del self.log
                raise SystemExit
            else:
                raise


if __name__ == '__main__':
    launch()
