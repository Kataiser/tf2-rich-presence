import datetime
import json
import os
import random
import time
import traceback

import certifi
import psutil
import urllib3
from discoIPC import ipc

import logger as log
import updater


def main():
    # TF2 rich presence by Kataiser
    # {tf2rpvnum}
    # https://github.com/Kataiser/tf2-rich-presence

    log.dev = True
    log.info("Starting TF2 Rich Presence {tf2rpvnum}")
    log.cleanup(5)
    log.current_log()

    updater.check('{tf2rpvnum}', 5)

    match_types = {'match group 12v12 Casual Match': 'Casual', 'match group MvM Practice': 'MvM', 'match group 6v6 Ladder Match': 'Competitive'}
    disconnect_messages = ('Server shutting down', 'Steam config directory', 'Lobby destroyed', 'Disconnect:', 'Missing map')
    start_time = int(time.time())
    activity = {'details': 'In menus',  # this is what gets modified and sent to Discord via discoIPC
                'timestamps': {'start': start_time},
                'assets': {'small_image': 'tf2_icon_small', 'small_text': 'Team Fortress 2', 'large_image': 'main_menu', 'large_text': 'In menus'},
                'state': ''}
    client_connected = False

    # load maps database
    try:
        maps_db = open(os.path.join('resources', 'maps.json'), 'r')
    except FileNotFoundError:
        maps_db = open('maps.json', 'r')

    map_gamemodes = json.load(maps_db)
    maps_db.close()

    loop_iteration = 0
    while True:
        loop_iteration += 1
        log.debug(f"Loop iteration this app session: {loop_iteration}")

        tf2_is_running = False
        steam_is_running = False
        discord_is_running = False

        # looks through all running processes to look for TF2, Steam, and Discord
        before_process_time = time.perf_counter()
        processes_searched = 0
        for process in psutil.process_iter():
            try:
                with process.oneshot():
                    processes_searched += 1
                    p_name = process.name()

                    if p_name == "hl2.exe":
                        path_to = process.cmdline()[0][:-7]
                        log.debug(f"hl2.exe path: {path_to}")

                        if 'Team Fortress 2' in path_to:
                            start_time = process.create_time()
                            log.debug(f"TF2 start time: {start_time}")
                            tf2_location = path_to
                            tf2_is_running = True
                    elif p_name == "Steam.exe":
                        steam_location = process.cmdline()[0][:-9]
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
            username = steam_config_file(steam_location)

        # used for display only
        current_time = datetime.datetime.now()
        current_time_formatted = current_time.strftime('%I:%M:%S %p')

        if tf2_is_running and discord_is_running:
            if not client_connected:
                # connects to Discord
                client = ipc.DiscordIPC('429389143756374017')
                client.connect()
                client_state = (client.client_id, client.connected, client.ipc_path, client.pid, client.platform, client.socket)
                log.debug(f"Initial client state: {client_state}")

                # sends first status, starts on main menu
                activity['timestamps']['start'] = start_time
                client.update_activity(activity)
                log.debug(f"Sent over RPC: {activity}")
                client_connected = True

            # defaults
            current_map = ''
            current_class = ''

            # modifies a few tf2 config files
            class_config_files(tf2_location)

            # console.log is a log of tf2's console (duh), only exists if tf2 has -condebug (see the bottom of config_files)
            consolelog_filename = os.path.join(tf2_location, 'tf', 'console.log')
            log.debug(f"Looking for console.log at {consolelog_filename}")
            log.console_log_path = consolelog_filename
            with open(consolelog_filename, 'r', errors='replace') as consolelog_file:
                consolelog_file_size = os.stat(consolelog_filename).st_size
                log.debug(f"console.log: {consolelog_file_size} bytes, {len(consolelog_file.readlines())} lines")
                if consolelog_file_size > 1100000:  # if the file size of console.log is over 1.1 MB
                    consolelog_file.seek(consolelog_file_size - 1000000)  # skip to the last MB
                    log.debug(f"Skipping to byte {consolelog_file_size - 1000000} in console.log")

                line = consolelog_file.readline()

                # iterates though every line in the log (I KNOW) and learns everything from it
                line_used = ''
                while line != '':
                    if 'Map:' in line:
                        current_map = line[5:-1]
                        current_class = 'unselected'  # this variable is poorly named
                        line_used = line

                    if 'selected' in line and 'candidates' not in line:
                        current_class = line[:-11]
                        line_used = line

                    if 'Disconnect by user' in line and username in line:
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

                    if '[PartyClient] Entering s' in line:  # full line: [PartyClient] Entering standby queue
                        current_map = 'In menus'
                        current_class = 'Queued for a party\'s match'
                        line_used = line

                    if '[PartyClient] L' in line:  # full line: [PartyClient] Leaving queue
                        current_class = 'Not queued'
                        line_used = line

                    line = consolelog_file.readline()

            log.debug(f"Got '{current_map}' and '{current_class}' from this line: '{line_used[:-1]}'")

            if current_map != 'In menus' and current_map != 'In queue':
                # not in menus = in a game
                try:
                    map_fancy, current_gamemode, gamemode_fancy = map_gamemodes[current_map]
                    activity['details'] = 'Map: {}'.format(map_fancy)
                    activity['assets']['large_image'] = current_gamemode
                    activity['assets']['large_text'] = gamemode_fancy
                except KeyError:
                    # is a custom map
                    activity['details'] = 'Map: {}'.format(current_map)

                    custom_gamemode, custom_gamemode_fancy = find_custom_map_gamemode(current_map)
                    activity['assets']['large_image'] = custom_gamemode
                    activity['assets']['large_text'] = custom_gamemode_fancy + ' [custom/community map]'

                activity['state'] = 'Class: {}'.format(current_class)
            else:
                # in menus displays the main menu
                activity['details'] = current_map
                activity['state'] = current_class
                activity['assets']['large_image'] = 'main_menu'
                activity['assets']['large_text'] = 'Main menu'

            # output to terminal, just for monitoring
            print(current_time_formatted)
            print("{} ({})".format(activity['details'], activity['assets']['large_text']))
            print(activity['state'])

            time_elapsed = int(time.time() - start_time)
            print("{} elapsed".format(datetime.timedelta(seconds=time_elapsed)))
            print()

            # send everything to discord
            client.update_activity(activity)
            log.debug(f"Sent over RPC: {activity}")
            client_state = (client.client_id, client.connected, client.ipc_path, client.pid, client.platform, client.socket)
            log.debug(f"Client state: {client_state}")
            if not client.connected:
                log.critical('Client is disconnected')
                log.report_log()
        elif not discord_is_running:
            log.debug("Discord isn't running")
            print("{}\nDiscord isn't running\n".format(current_time_formatted))
        else:
            if client_connected:
                try:
                    log.debug("Disconnecting client")
                    client.disconnect()  # doesn't work...
                    log.debug(f"Client state after disconnect: {client_state}")
                except Exception as err:
                    log.error(f"Client error while disconnecting: {err}")

                if random.random() < 0.1:
                    log.report_log()  # send 10% of logs when closing TF2, for telemetry more than bugfixing
                raise SystemExit  # ...but this does
            else:
                log.debug("TF2 isn't running")
                print("{}\nTF2 isn't running\n".format(current_time_formatted))

            # to prevent connecting when already connected
            client_connected = False

        # rich presence only updates every 15 seconds, but it listens constantly so sending every 5 seconds is fine
        time.sleep(5)


# allows the console to output 'class selected' on class choose
def class_config_files(exe_location):
    log.debug(f"Reading (and possibly modifying) class configs at {exe_location}")
    tf2_classes = ['Scout', 'Soldier', 'Pyro', 'Demoman', 'Heavy', 'Engineer', 'Medic', 'Sniper', 'Spy']

    for tf2_class in tf2_classes:
        # 'echo' means 'output to console' in source-speak
        selected_line = 'echo "{} selected"'.format(tf2_class)

        config_filename = tf2_class.lower().replace('heavy', 'heavyweapons')  # valve why

        # config files are at 'Steam\steamapps\common\Team Fortress 2\tf\cfg'
        try:
            # reads each existing class.cfg
            class_config_file = open(os.path.join(exe_location, 'tf', 'cfg', f'{config_filename}.cfg'), 'r+', errors='replace')
            if selected_line not in class_config_file.read():
                # if it doesn't already have the echo line, add it
                log.debug(f"'{selected_line}' not found in {class_config_file.name}, adding it")
                class_config_file.write('\n\n' + selected_line)
            else:
                log.debug(f"{selected_line} found in {class_config_file.name}")
        except FileNotFoundError:
            # the config file doesn't exist, so create it and add the echo line
            class_config_file = open(os.path.join(exe_location, 'tf', 'cfg', f'{config_filename}.cfg'), 'w')
            log.debug(f"Created {class_config_file.name}")
            class_config_file.write(selected_line)

        # I know a 'with open()' is better but eh
        class_config_file.close()


# reads steams launch options save file to find -condebug
def steam_config_file(exe_location):
    log.debug("Looking for -condebug")
    found_condebug = False

    for user_id_folder in next(os.walk(exe_location + 'userdata'))[1]:  # possibly multiple users for the same steam install
        try:
            # 'C:\Program Files (x86)\Steam\userdata\*user id number*\config\localconfig.vdf'
            with open(os.path.join(exe_location, 'userdata', user_id_folder, 'config', 'localconfig.vdf'), 'r+', errors='replace') as global_config_file:
                lines = global_config_file.readlines()
                log.debug(f"Reading {global_config_file.name} ({len(lines)} lines) for -condebug")
                tf2_line_num = 0

                for line in enumerate(lines):
                    if line[1].startswith('\t\t"PersonaName"\t\t'):
                        possible_username = line[1].replace('\t', '')[14:-2]
                        log.debug(f"Possible username: {possible_username}")
                    if line[1] == '\t\t\t\t\t"440"\n':  # looks for tf2's ID and finds the line number
                        log.debug(f"Found TF2's ID at line {line[0]}")
                        tf2_line_num = line[0]

                for line_offset in range(1, 21):
                    launchoptions_line = lines[tf2_line_num + line_offset]
                    if 'LaunchOptions' in launchoptions_line and'-condebug' in launchoptions_line:
                        # oh also this might be slow to update
                        found_condebug = True
                        log.debug(f"Found -condebug with offset {line_offset} in line: {launchoptions_line[:-1]}")
                        found_username = possible_username
                        log.debug(f"Username with -condebug: {found_username}")
                        return found_username
        except FileNotFoundError:
            pass

    if not found_condebug:
        log.debug("-condebug not found, telling user")
        # yell at the user to fix their settings
        print("\nYour TF2 installation doesn't seem to be set up properly. To fix:"
              "\n1. Right click on Team Fortress 2 in your Steam library"
              "\n2. Open properties (very bottom)"
              "\n3. Click \"Set launch options...\""
              "\n4. Add -condebug"
              "\n5. OK and Close\n")
        # -condebug is kinda necessary so just wait to restart if it's not there
        input('Press enter to try again\n')
        log.debug("Restarting")
        raise SystemExit


# uses teamwork.tf's API to find the gamemode of a custom map
def find_custom_map_gamemode(map_filename):
    log.debug(f"Finding gamemode for custom map: {map_filename}")
    days_since_epoch_now = int(time.time() / 86400)

    # to avoid constantly using internet, each map is cached to custom_maps.json
    try:
        custom_maps_db = open(os.path.join('resources', 'custom_maps.json'), 'r')
    except FileNotFoundError:
        custom_maps_db = open('custom_maps.json', 'r')

    custom_map_gamemodes = json.load(custom_maps_db)
    custom_maps_db.close()
    log.debug(f"{len(custom_map_gamemodes)} maps cached: {list(custom_map_gamemodes.keys())}")

    # look for map in loaded cache
    try:
        cached_data = custom_map_gamemodes[map_filename]
        if days_since_epoch_now - cached_data[2] <= 5:  # custom map cache expires after 5 days
            log.debug(f"{map_filename}'s gamemode is {list(cached_data[:-1])} (from cache)")
            return cached_data[:-1]
        else:
            log.debug(f"Outdated cache ({cached_data[2]} -> {days_since_epoch_now})")
            raise KeyError
    except KeyError:
        gamemodes = {'ctf': 'Capture the Flag', 'control-point': 'Control Point (Domination)', 'attack-defend': 'Attack/Defend', 'medieval-mode': 'Attack/Defend (Medieval Mode)',
                     'territorial-control': 'Territorial Control', 'payload': 'Payload', 'payload-race': 'Payload Race', 'koth': 'King of the Hill', 'special-delivery': 'Special Delivery',
                     'mvm': 'Mann vs. Machine', 'beta-map': 'Robot Destruction', 'mannpower': 'Mannpower', 'passtime': 'PASS Time', 'player-destruction': 'Player Destruction',
                     'arena': 'Arena', 'training': 'Training', 'surfing': 'Surfing', 'trading': 'Trading', 'jumping': 'Jumping', 'deathmatch': 'Deathmatch', 'cp-orange': 'Orange',
                     'versus-saxton-hale': 'Versus Saxton Hale', 'deathrun': 'Deathrun', 'achievement': 'Achievement', 'breakout': 'Jail Breakout', 'slender': 'Slender',
                     'dodgeball': 'Dodgeball', 'mario-kart': 'Mario Kart'}

        # I'd prefer requests but that would bloat the filesize (more)
        before_request_time = time.perf_counter()
        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        r = http.request('GET', 'https://teamwork.tf/api/v1/map-stats/map/{}?key=nvsDhCxoVHcSiAZ7pFBTWbMy91RaIYgq'.format(map_filename))
        map_info = json.loads(r.data.decode('utf-8'))
        log.debug(f"API lookup took {time.perf_counter() - before_request_time} secs")

        try:
            # parses the api result
            log.debug(f"All gamemodes found: {map_info['all_gamemodes']}")
            first_gamemode = map_info['all_gamemodes'][0]
            first_gamemode_fancy = gamemodes[first_gamemode]
            # modify the cache locally
            custom_map_gamemodes[map_filename] = [first_gamemode, first_gamemode_fancy, days_since_epoch_now]

            # load the cache to actually modify it
            try:
                custom_maps_db = open(os.path.join('resources', 'custom_maps.json'), 'w')
            except FileNotFoundError:
                custom_maps_db = open('custom_maps.json', 'w')

            json.dump(custom_map_gamemodes, custom_maps_db, indent=4)
            custom_maps_db.close()

            # ex: 'mvm', 'Mann vs. Machine'
            log.debug(f"{map_filename}'s gamemode is {[first_gamemode, first_gamemode_fancy]} (fresh from teamwork.tf)")
            return first_gamemode, first_gamemode_fancy
        except KeyError:
            log.error("KeyError, probably unrecognized gamemode")
        except IndexError:
            log.error("IndexError, possibly unrecognized gamemode or something similar")

        # unrecognized gamemodes
        first_gamemode = 'unknown_map'
        first_gamemode_fancy = 'Unknown gamemode'
        custom_map_gamemodes[map_filename] = [first_gamemode, first_gamemode_fancy, days_since_epoch_now]

        try:
            custom_maps_db = open(os.path.join('resources', 'custom_maps.json'), 'w')
        except FileNotFoundError:
            custom_maps_db = open('custom_maps.json', 'w')

        json.dump(custom_map_gamemodes, custom_maps_db, indent=4)
        custom_maps_db.close()

        log.debug(f"{map_filename}'s gamemode is {[first_gamemode, first_gamemode_fancy]} (fresh from the API)")
        return first_gamemode, first_gamemode_fancy


if __name__ == '__main__':
    try:
        main()
    except Exception:
        log.critical(traceback.format_exc())
        log.report_log()
