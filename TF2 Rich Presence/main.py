import datetime
import gc
import json
import os
import time
import traceback
from typing import Dict, Union, TextIO, Any, List, Tuple

import psutil
from discoIPC import ipc

import configs
import custom_maps
import logger as log


def main():
    # TF2 rich presence by Kataiser
    # {tf2rpvnum}
    # https://github.com/Kataiser/tf2-rich-presence
    log.dev = True
    log.info("Starting TF2 Rich Presence {tf2rpvnum}")
    log.current_log()

    if log.dev:
        log.cleanup(20)
    else:
        log.cleanup(5)

    TF2RichPresense().run()


class TF2RichPresense:
    def __init__(self):
        self.start_time: int = int(time.time())
        self.activity: Dict[str, Union[str, Dict[str, int], Dict[str, str]]] = {'details': 'In menus',  # this is what gets modified and sent to Discord via discoIPC
                                                                                'timestamps': {'start': self.start_time},
                                                                                'assets': {'small_image': 'tf2_icon_small', 'small_text': 'Team Fortress 2', 'large_image': 'main_menu',
                                                                                           'large_text': 'In menus'},
                                                                                'state': ''}
        self.client_connected: bool = False
        self.client = None

        # load maps database
        try:
            maps_db: TextIO = open(os.path.join('resources', 'maps.json'), 'r')
        except FileNotFoundError:
            maps_db: TextIO = open('maps.json', 'r')

        self.map_gamemodes: dict = json.load(maps_db)
        maps_db.close()

        self.loop_iteration: int = 0

    def run(self):
        while True:
            self.loop_body()

            # rich presence only updates every 15 seconds, but it listens constantly so sending every 5 seconds is fine
            time.sleep(5)

            # runs garbage collection after waiting
            log.debug(f"This GC: {gc.collect()}")
            log.debug(f"Total GC: {gc.get_stats()}")

    # the main logic. runs every 5 seconds
    def loop_body(self):
        self.loop_iteration += 1
        log.debug(f"Loop iteration this app session: {self.loop_iteration}")

        tf2_is_running: bool = False
        steam_is_running: bool = False
        discord_is_running: bool = False

        # looks through all running processes to look for TF2, Steam, and Discord
        before_process_time: float = time.perf_counter()
        processes_searched: int = 0
        for process in psutil.process_iter():
            try:
                with process.oneshot():
                    processes_searched += 1
                    p_name: str = process.name()

                    if p_name == 'hl2.exe':
                        path_to: str = process.cmdline()[0][:-7]
                        log.debug(f"hl2.exe path: {path_to}")

                        if 'Team Fortress 2' in path_to:
                            self.start_time = process.create_time()
                            log.debug(f"TF2 start time: {self.start_time}")
                            tf2_location: str = path_to
                            tf2_is_running = True
                    elif p_name == 'Steam.exe':
                        steam_location: str = process.cmdline()[0][:-9]
                        log.debug(f"Steam.exe path: {steam_location}")
                        steam_is_running = True
                    elif 'Discord' in p_name:
                        log.debug(f"Discord is running at {p_name}")
                        discord_is_running = True
            except Exception:
                log.error(f"psutil error for {process}: {traceback.format_exc()}")

            if tf2_is_running and steam_is_running and discord_is_running:
                log.debug("Broke from process loop")
                break

            time.sleep(0.001)
        log.debug(f"Process loop took {time.perf_counter() - before_process_time} sec for {processes_searched} processes")

        if steam_is_running:
            # reads a steam config file
            valid_usernames: List[str] = configs.steam_config_file(steam_location)

        # used for display only
        current_time = datetime.datetime.now()
        current_time_formatted: str = current_time.strftime('%I:%M:%S %p')

        if tf2_is_running and discord_is_running:
            if not self.client_connected:
                try:
                    # connects to Discord
                    self.client = ipc.DiscordIPC('429389143756374017')
                    self.client.connect()
                    self.client_state: Tuple[Any, bool, str, int, str, Any] = (self.client.client_id, self.client.connected, self.client.ipc_path, self.client.pid, self.client.platform, self.client.socket)
                    log.debug(f"Initial client state: {self.client_state}")
                except Exception as client_connect_error:
                    if client_connect_error == "Can't connect to Discord Client.":  # Discord is still running but an RPC client can't be established
                        log.debug("Can't RPC")
                        print(f"{current_time_formatted}\nCan't connect to Discord for Rich Presence.\n")
                        raise SystemExit
                    else:  # some other error
                        raise

                # sends first status, starts on main menu
                self.activity['timestamps']['start'] = self.start_time
                self.client.update_activity(self.activity)
                log.debug(f"Sent over RPC: {self.activity}")
                self.client_connected = True

            # modifies a few tf2 config files
            configs.class_config_files(tf2_location)

            state_line, details_line = interpret_console_log(os.path.join(tf2_location, 'tf', 'console.log'), valid_usernames)

            if state_line != 'In menus' and state_line != 'In queue':
                # not in menus = in a game
                try:
                    map_fancy, current_gamemode, gamemode_fancy = self.map_gamemodes[state_line]
                    self.activity['details'] = 'Map: {}'.format(map_fancy)
                    self.activity['assets']['large_image'] = current_gamemode
                    self.activity['assets']['large_text'] = gamemode_fancy
                except KeyError:
                    # is a custom map
                    self.activity['details'] = 'Map: {}'.format(state_line)

                    custom_gamemode, custom_gamemode_fancy = custom_maps.find_custom_map_gamemode(state_line)
                    self.activity['assets']['large_image'] = custom_gamemode
                    self.activity['assets']['large_text'] = custom_gamemode_fancy + ' [custom/community map]'

                self.activity['state'] = 'Class: {}'.format(details_line)
            else:
                # in menus displays the main menu
                self.activity['details'] = state_line
                self.activity['state'] = details_line
                self.activity['assets']['large_image'] = 'main_menu'
                self.activity['assets']['large_text'] = 'Main menu'

            # output to terminal, just for monitoring
            print(current_time_formatted)
            print("{} ({})".format(self.activity['details'], self.activity['assets']['large_text']))
            print(self.activity['state'])

            time_elapsed = int(time.time() - self.start_time)
            print("{} elapsed".format(datetime.timedelta(seconds=time_elapsed)))
            print()

            # send everything to discord
            self.client.update_activity(self.activity)
            log.debug(f"Sent over RPC: {self.activity}")
            self.client_state = (self.client.client_id, self.client.connected, self.client.ipc_path, self.client.pid, self.client.platform, self.client.socket)
            log.debug(f"self.client state: {self.client_state}")
            if not self.client_connected:
                log.critical('self.client is disconnected')
                log.report_log("self.client disconnect")
        elif not discord_is_running:
            log.debug("Discord isn't running")
            print("{}\nDiscord isn't running\n".format(current_time_formatted))
        else:  # tf2 isn't running
            if self.client_connected:
                try:
                    log.debug("Disconnecting client")
                    self.client.disconnect()  # doesn't work...
                    self.client_state = (self.client.client_id, self.client.connected, self.client.ipc_path, self.client.pid, self.client.platform, self.client.socket)
                    log.debug(f"self.client state after disconnect: {self.client_state}")
                except Exception as err:
                    log.error(f"client error while disconnecting: {err}")

                raise SystemExit  # ...but this does
            else:
                log.debug("TF2 isn't running")
                print("{}\nTF2 isn't running\n".format(current_time_formatted))

            # to prevent connecting when already connected
            self.client_connected = False

        return self.client_connected, self.client


# reads a console.log and returns current map and class
def interpret_console_log(console_log_path: str, user_usernames: list) -> tuple:
    # defaults
    current_map: str = ''
    current_class: str = ''
    
    match_types: Dict[str, str] = {'match group 12v12 Casual Match': 'Casual', 'match group MvM Practice': 'MvM', 'match group 6v6 Ladder Match': 'Competitive'}
    disconnect_messages = ('Server shutting down', 'Steam config directory', 'Lobby destroyed', 'Disconnect:', 'Missing map')

    # console.log is a log of tf2's console (duh), only exists if tf2 has -condebug (see the bottom of config_files)
    consolelog_filename: Union[bytes, str] = console_log_path
    log.debug(f"Looking for console.log at {consolelog_filename}")
    log.console_log_path = consolelog_filename

    if not os.path.exists(consolelog_filename):
        log.critical("console.log doesn't exist, issuing warning")
        no_condebug_warning()

    with open(consolelog_filename, 'r', errors='replace') as consolelog_file:
        consolelog_file_size: int = os.stat(consolelog_filename).st_size
        lines: List[str] = consolelog_file.readlines()
        log.debug(f"console.log: {consolelog_file_size} bytes, {len(lines)} lines")
        if len(lines) > 11000:
            lines = lines[-10000:]
            log.debug(f"Limited to reading {len(lines)} lines")

        # iterates though every line in the log (I KNOW) and learns everything from it
        line_used: str = ''
        for line in lines:
            if 'Map:' in line:
                current_map = line[5:-1]
                current_class = 'unselected'  # this variable is poorly named
                line_used = line

            if 'selected' in line and 'candidates' not in line:
                current_class = line[:-11]
                line_used = line

            if 'Disconnect by user' in line and [i for i in user_usernames if i in line]:
                current_map = 'In menus'  # so is this one
                current_class = 'Not queued'
                line_used = line

            for disconnect_message in disconnect_messages:
                if disconnect_message in line:
                    current_map = 'In menus'
                    current_class = 'Not queued'
                    line_used = line
                    break

            if '[PartyClient] Entering queue ' in line:
                current_map = 'In menus'
                current_class = 'Queued for {}'.format(match_types[line[33:-1]])
                line_used = line

            if '[PartyClient] Entering s' in line:  # full line: [Partyclient] Entering standby queue
                current_map = 'In menus'
                current_class = 'Queued for a party\'s match'
                line_used = line

            if '[PartyClient] L' in line:  # full line: [Partyclient] Leaving queue
                current_class = 'Not queued'
                line_used = line

    log.debug(f"Got '{current_map}' and '{current_class}' from this line: '{line_used[:-1]}'")
    return current_map, current_class


# alerts the user that they don't seem to have -condebug
def no_condebug_warning():
    print("\nYour TF2 installation doesn't seem to be set up properly. To fix:"
          "\n1. Right click on Team Fortress 2 in your Steam library"
          "\n2. Open properties (very bottom)"
          "\n3. Click \"Set launch options...\""
          "\n4. Add -condebug"
          "\n5. OK and Close"
          "\n6. Restart TF2\n")
    # -condebug is kinda necessary so just wait to restart if it's not there
    input('Press enter to try again\n')
    log.debug("Restarting")
    raise SystemExit


def handle_crash(exception):
    formatted_exception = traceback.format_exc()
    log.critical(formatted_exception)
    print(f"TF2 Rich Presence has crashed, the error should now be reported to the developer.\nHere's the full error message if you're interested.\n{formatted_exception}")
    log.report_log(exception)
    time.sleep(5)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        handle_crash(error)
