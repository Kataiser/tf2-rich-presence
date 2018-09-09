import datetime
import gc
import json
import os
import platform
import time
import traceback
from ctypes import Structure, windll, c_uint, sizeof, byref
from typing import Dict, Union, TextIO, Any, List, Tuple

import psutil
from discoIPC import ipc

import configs
import custom_maps
import logger
import settings


def main():
    # TF2 rich presence by Kataiser
    # {tf2rpvnum}
    # https://github.com/Kataiser/tf2-rich-presence

    log_init = logger.Log()
    log_init.to_stderr = True
    app = TF2RichPresense(log_init)

    try:
        log_init.info("Starting TF2 Rich Presence {tf2rpvnum}")
        log_init.debug(f"Current log: {log_init.filename}")
        log_init.info(f'Log level: {log_init.log_level}')
        log_init.cleanup(20)
        log_init.debug(f"CPU: {psutil.cpu_count(logical=False)} cores, {psutil.cpu_count()} threads")
        log_init.debug(f"CPU frequency info: {psutil.cpu_freq()}")

        platform_info = {'architecture': platform.architecture, 'machine': platform.machine, 'system': platform.system, 'platform': platform.platform,
                         'processor': platform.processor, 'win32_ver': platform.win32_ver, 'python_version_tuple': platform.python_version_tuple}
        for platform_part in platform_info.keys():
            try:
                if platform_part == 'platform':
                    print()
                    platform_info[platform_part] = platform_info[platform_part](aliased=True)
                else:
                    platform_info[platform_part] = platform_info[platform_part]()
            except Exception:
                log_init.error(f"Exception during platform.{platform_part}(), skipping\n{traceback.format_exc()}")
        log_init.debug(f"Platform: {platform_info}")

        app.run()
    except (KeyboardInterrupt, SystemExit):
        raise SystemExit
    except Exception as error:
        app.handle_crash(error)


class TF2RichPresense:
    def __init__(self, log):
        self.log = log
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
            current_settings = settings.access_settings_file()
            self.log.debug(f"Current settings (default: {current_settings == settings.get_setting_default(return_all=True)}): {current_settings}")
            self.loop_body()
            self.log.debug(f"Settings cache stats: {settings.get.cache_info()}")

            # rich presence only updates every 15 seconds, but it listens constantly so sending every 5 (by default) seconds is fine
            if settings.get('scale_wait_time'):
                idle_duration = get_idle_duration()
                sleep_time: float = calculate_wait_time(settings.get('wait_time'), idle_duration)
                self.log.debug(f"Sleeping for {sleep_time} secs, user has been idle for {idle_duration} secs")
            else:
                sleep_time = settings.get('wait_time')
                self.log.debug(f"Sleeping for {sleep_time} secs, scaling is disabled")

            time.sleep(sleep_time)

            # runs garbage collection after waiting
            self.log.debug(f"This GC: {gc.collect()}")
            self.log.debug(f"Total GC: {gc.get_stats()}")

    # the main logic. runs every 5 seconds
    def loop_body(self):
        self.loop_iteration += 1
        self.log.debug(f"Loop iteration this app session: {self.loop_iteration}")

        tf2_is_running: bool = False
        steam_is_running: bool = False
        discord_is_running: bool = False

        # looks through all running processes to look for TF2, Steam, and Discord
        before_process_time: float = time.perf_counter()
        processes_searched: int = 0

        cpu_usage = psutil.cpu_percent()
        self.log.debug(f"CPU usage: {cpu_usage}%")

        for process in psutil.process_iter():
            try:
                with process.oneshot():
                    processes_searched += 1
                    p_name: str = process.name()

                    if p_name == 'hl2.exe':
                        path_to: str = process.cmdline()[0][:-7]
                        self.log.debug(f"hl2.exe path: {path_to}")

                        if 'Team Fortress 2' in path_to:
                            self.start_time = process.create_time()
                            self.log.debug(f"TF2 start time: {self.start_time}")
                            tf2_location: str = path_to
                            tf2_is_running = True
                    elif p_name == 'Steam.exe':
                        steam_location: str = process.cmdline()[0][:-9]
                        self.log.debug(f"Steam.exe path: {steam_location}")
                        steam_is_running = True
                    elif 'Discord' in p_name and '.exe' in p_name:
                        self.log.debug(f"Discord is running at {p_name}")
                        discord_is_running = True
            except Exception:
                self.log.error(f"psutil error for {process}: {traceback.format_exc()}")

            if tf2_is_running and steam_is_running and discord_is_running:
                self.log.debug("Broke from process loop")
                break

            if cpu_usage > 25 or cpu_usage == 0.0:
                time.sleep(0.001)
        self.log.debug(f"Process loop took {time.perf_counter() - before_process_time} sec for {processes_searched} processes")

        if steam_is_running:
            # reads a steam config file
            valid_usernames: List[str] = configs.steam_config_file(self.log, steam_location)

        # used for display only
        current_time = datetime.datetime.now()
        current_time_formatted: str = current_time.strftime('%I:%M:%S %p')

        if tf2_is_running and discord_is_running:
            # modifies a few tf2 config files
            configs.class_config_files(self.log, tf2_location)

            top_line, bottom_line, server_ip = self.interpret_console_log(os.path.join(tf2_location, 'tf', 'console.log'), valid_usernames)

            if not self.client_connected:
                try:
                    # connects to Discord
                    self.client = ipc.DiscordIPC('429389143756374017')
                    self.client.connect()
                    client_state: Tuple[Any, bool, str, int, str, Any] = (
                        self.client.client_id, self.client.connected, self.client.ipc_path, self.client.pid, self.client.platform, self.client.socket)
                    self.log.debug(f"Initial client state: {client_state}")
                except Exception as client_connect_error:
                    if str(client_connect_error) == "Can't connect to Discord Client.":  # Discord is still running but an RPC client can't be established
                        self.log.error("Can't connect to RPC")
                        print(f"{current_time_formatted}\nCan't connect to Discord for Rich Presence.\n")
                        raise SystemExit
                    else:  # some other error
                        raise

                # sends first status, starts on main menu
                self.activity['timestamps']['start'] = self.start_time
                self.client.update_activity(self.activity)
                self.log.debug(f"Sent over RPC: {self.activity}")
                self.client_connected = True

            if top_line == 'In menus':
                # in menus displays the main menu
                self.activity['assets']['small_image'] = 'tf2_icon_small'
                self.activity['assets']['small_text'] = 'Team Fortress 2'

                if bottom_line == 'Queued for Casual':
                    self.activity['assets']['large_image'] = 'casual'
                    self.activity['assets']['large_text'] = bottom_line
                elif bottom_line == 'Queued for Competitive':
                    self.activity['assets']['large_image'] = 'comp'
                    self.activity['assets']['large_text'] = bottom_line
                elif bottom_line == 'Queued for MvM':
                    self.activity['assets']['large_image'] = 'mvm_queued'
                    self.activity['assets']['large_text'] = bottom_line
                else:
                    self.activity['assets']['large_image'] = 'main_menu'
                    self.activity['assets']['large_text'] = 'Main menu'
            else:
                # not in menus = in a game
                if bottom_line != 'unselected':
                    self.activity['assets']['small_image'] = bottom_line.lower()
                    self.activity['assets']['small_text'] = bottom_line

                bottom_line = f"Class: {bottom_line}"

                try:
                    map_fancy, current_gamemode, gamemode_fancy = self.map_gamemodes[top_line]
                    map_out = map_fancy
                    self.activity['assets']['large_image'] = current_gamemode
                    self.activity['assets']['large_text'] = gamemode_fancy
                except KeyError:
                    # is a custom map
                    custom_gamemode, custom_gamemode_fancy = custom_maps.find_custom_map_gamemode(self.log, top_line)
                    map_out = top_line
                    self.activity['assets']['large_image'] = custom_gamemode
                    self.activity['assets']['large_text'] = f'{custom_gamemode_fancy} [custom/community map]'

                if settings.get('hide_provider'):
                    top_line = f'Map: {map_out}'
                else:
                    server_provider = self.find_provider_for_ip(server_ip)
                    if not server_provider:
                        top_line = f'Map: {map_out}'
                    else:
                        top_line = f'Map: {map_out} ({server_provider} server)'

            self.activity['details'] = top_line
            self.activity['state'] = bottom_line

            # output to terminal, just for monitoring
            print(current_time_formatted)
            print(f"{self.activity['details']} ({self.activity['assets']['large_text']})")
            print(self.activity['state'])
            time_elapsed = int(time.time() - self.start_time)
            print(f"{datetime.timedelta(seconds=time_elapsed)} elapsed")
            print()

            # send everything to discord
            self.client.update_activity(self.activity)
            self.log.debug(f"Sent over RPC: {self.activity}")
            client_state = (self.client.client_id, self.client.connected, self.client.ipc_path, self.client.pid, self.client.platform, self.client.socket)
            self.log.debug(f"client state: {client_state}")
            if not self.client_connected:
                self.log.critical('self.client is disconnected')
                self.log.report_log("self.client disconnect")
        elif not discord_is_running:
            self.log.debug("Discord isn't running")
            print(f"{current_time_formatted}\nDiscord isn't running\n")
        else:  # tf2 isn't running
            if self.client_connected:
                try:
                    self.log.debug("Disconnecting client")
                    self.client.disconnect()  # doesn't work...
                    client_state = (self.client.client_id, self.client.connected, self.client.ipc_path, self.client.pid, self.client.platform, self.client.socket)
                    self.log.debug(f"client state after disconnect: {client_state}")
                except Exception as err:
                    self.log.error(f"client error while disconnecting: {err}")

                self.log.debug("Restarting")
                raise SystemExit  # ...but this does
            else:
                self.log.debug("TF2 isn't running")
                print(f"{current_time_formatted}\nTF2 isn't running\n")

            # to prevent connecting when already connected
            self.client_connected = False

        return self.client_connected, self.client

    # reads a console.log and returns current map, class, and server ip
    def interpret_console_log(self, console_log_path: str, user_usernames: list, byte_limit=settings.get('console_scan_kb')) -> tuple:
        # defaults
        current_map: str = ''
        current_class: str = ''
        current_ip: str = ''
        build_number: Union[str, None] = None

        match_types: Dict[str, str] = {'match group 12v12 Casual Match': 'Casual', 'match group MvM Practice': 'MvM', 'match group 6v6 Ladder Match': 'Competitive'}
        disconnect_messages = ('Server shutting down', 'Steam config directory', 'Lobby destroyed', 'Disconnect:', 'Missing map')
        tf2_classes = ('Scout', 'Soldier', 'Pyro', 'Demoman', 'Heavy', 'Engineer', 'Medic', 'Sniper', 'Spy')

        hide_queued_gamemode = settings.get('hide_queued_gamemode')

        # console.log is a log of tf2's console (duh), only exists if tf2 has -condebug (see the bottom of config_files)
        consolelog_filename: Union[bytes, str] = console_log_path
        self.log.debug(f"Looking for console.log at {consolelog_filename}")
        self.log.console_log_path = consolelog_filename
        self.log.debug("Set console_log_path in logger")

        if not os.path.exists(consolelog_filename):
            self.log.error(f"console.log doesn't exist, issuing warning (files/dirs in /tf/: {os.listdir(os.path.dirname(console_log_path))})")
            self.no_condebug_warning()

        with open(consolelog_filename, 'r', errors='replace') as consolelog_file:
            consolelog_file_size: int = os.stat(consolelog_filename).st_size

            line_limit_bytes = byte_limit * 1000
            if consolelog_file_size > line_limit_bytes:
                skip_to_byte = consolelog_file_size - line_limit_bytes
                consolelog_file.seek(skip_to_byte, 0)  # skip to last few KBs

                lines: List[str] = consolelog_file.readlines()
                self.log.debug(f"console.log: {consolelog_file_size} bytes, skipped to {skip_to_byte}, {len(lines)} lines read")
            else:
                lines: List[str] = consolelog_file.readlines()
                self.log.debug(f"console.log: {consolelog_file_size} bytes, {len(lines)} lines")

        # iterates though every line in the log (I KNOW) and learns everything from it
        line_used: str = ''
        for line in lines:
            if 'Map:' in line:
                current_map = line[5:-1]
                current_class = 'unselected'  # this variable is poorly named
                line_used = line

            if 'selected' in line:
                current_class_possibly = line[:-11]

                if current_class_possibly in tf2_classes:
                    current_class = current_class_possibly
                    line_used = line

            if 'Disconnect by user' in line and [i for i in user_usernames if i in line]:
                current_map = 'In menus'  # so is this one
                current_class = 'Not queued'
                current_ip = ''
                line_used = line

            for disconnect_message in disconnect_messages:
                if disconnect_message in line:
                    current_map = 'In menus'
                    current_class = 'Not queued'
                    current_ip = ''
                    line_used = line
                    break

            if '[PartyClient] Entering queue ' in line:
                current_map = 'In menus'
                current_ip = ''
                line_used = line

                if hide_queued_gamemode:
                    current_class = "Queued"
                else:
                    current_class = f"Queued for {match_types[line[33:-1]]}"

            if '[PartyClient] Entering s' in line:  # full line: [PartyClient] Entering standby queue
                current_map = 'In menus'
                current_class = 'Queued for a party\'s match'
                current_ip = ''
                line_used = line

            if '[PartyClient] L' in line:  # full line: [PartyClient] Leaving queue
                current_class = 'Not queued'
                line_used = line

            if 'Build:' in line:
                build_number = line[7:-1]

            if 'Connected to' in line:
                current_ip = line[13:-1]

        self.log.debug(f"TF2 build number: {build_number}")
        self.log.debug(f"Got '{current_map}', '{current_class}', and {current_ip} from this line: '{line_used[:-1]}'")
        return current_map, current_class, current_ip

    # alerts the user that they don't seem to have -condebug
    def no_condebug_warning(self):
        print("\nYour TF2 installation doesn't yet seem to be set up properly. To fix:"
              "\n1. Right click on Team Fortress 2 in your Steam library"
              "\n2. Open properties (very bottom)"
              "\n3. Click \"Set launch options...\""
              "\n4. Add -condebug"
              "\n5. OK and Close"
              "\n6. Restart TF2\n")
        # -condebug is kinda necessary so just wait to restart if it's not there
        input("Press enter to retry\n")
        self.log.debug("Restarting")
        raise SystemExit

    # displays and reports current traceback
    def handle_crash(self, exception: Exception, silent=False):
        formatted_exception = traceback.format_exc()
        self.log.critical(formatted_exception)

        if not silent:
            print(f"\n{formatted_exception}\nTF2 Rich Presence has crashed, the error should now be reported to the developer."
                  f"\n(Consider opening an issue at https://github.com/Kataiser/tf2-rich-presence/issues)"
                  f"\nRestarting in 2 seconds...")

        self.log.report_log(str(exception))
        if not silent:
            time.sleep(2)
        raise SystemExit

    # find what server provider an IP belongs to
    def find_provider_for_ip(self, ip):
        try:
            community_server_ips_json = open('community_server_ips.json', 'r')
        except FileNotFoundError:
            community_server_ips_json = open(os.path.join('resources', 'community_server_ips.json'), 'r')

        community_server_ips_dict = json.load(community_server_ips_json)
        community_server_ips_json.close()

        community_server_ips_list = []
        for ip_list in community_server_ips_dict.values():
            community_server_ips_list.extend([ip for ip in ip_list])

        if ip != '' and ip in community_server_ips_list:
            for provider_name in community_server_ips_dict.keys():
                if ip in community_server_ips_dict[provider_name]:
                    self.log.debug(f"IP {ip} is run by {provider_name}")
                    return provider_name

        self.log.debug(f"IP {ip} is not run by a known provider")
        return None


# https://www.bself.log.pythonlibrary.org/2010/05/05/python-how-to-tell-how-long-windows-has-been-idle/
# http://stackoverflow.com/questions/911856/detecting-idle-time-in-python
class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]


# how long the user has been idle for, in seconds
def get_idle_duration() -> float:
    last_input_info = LASTINPUTINFO()
    last_input_info.cbSize = sizeof(last_input_info)
    windll.user32.GetLastInputInfo(byref(last_input_info))
    millis = windll.kernel32.GetTickCount() - last_input_info.dwTime
    return millis / 1000.0


# calculates delay, in seconds, between updates
def calculate_wait_time(base: int, afk: float) -> float:
    # https://www.desmos.com/calculator/hliplhcd8q
    max_time: int = (2 * base) + 20
    scaled: float = 0.15 * (afk - 2 * base - 10) + base
    wait_time: float = max(min(max_time, scaled), base)
    return round(wait_time, 2)


if __name__ == '__main__':
    # self.log.sentry_enabled = False
    main()
