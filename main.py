import datetime
import json
import os
import time

import psutil
import psutil._exceptions as ps_exceptions
from discoIPC import ipc


def main():
    match_types = {'match group 12v12 Casual Match': 'Casual', 'match group MvM Practice': 'MvM', 'match group 6v6 Ladder Match': 'Competitive'}
    start_time = int(time.time())
    activity = {'details': 'In menus',  # this is what gets modified and sent to Discord via discoIPC
                'timestamps': {'start': start_time},
                'assets': {'small_image': 'tf2_icon_small', 'small_text': 'Team Fortress 2', 'large_image': 'main_menu', 'large_text': 'In menus'},
                'state': ''}
    client_connected = False

    try:
        maps_db = open('resources/maps.json', 'r')
    except FileNotFoundError:
        maps_db = open('maps.json', 'r')

    map_gamemodes = json.load(maps_db)
    maps_db.close()

    while True:
        tf2_is_running = False
        steam_is_running = False
        discord_is_running = False

        # looks through all running processes to look for TF2, Steam, and Discord

        for process in psutil.process_iter():
            try:
                with process.oneshot():
                    p_name = process.name()

                    if p_name == "hl2.exe":
                        path_to = process.cmdline()[0][:-7]

                        if 'Team Fortress 2' in path_to:
                            start_time = process.create_time()
                            tf2_location = path_to
                            tf2_is_running = True
                    elif p_name == "Steam.exe":
                        steam_location = process.cmdline()[0][:-9]
                        steam_is_running = True
                    elif 'Discord' in p_name:
                        discord_is_running = True
            except ps_exceptions.NoSuchProcess:
                pass
            except ps_exceptions.AccessDenied:
                pass

            time.sleep(0.001)

        if steam_is_running:
            # reads a steam config file
            steam_config_file(steam_location)

        # used for display only
        current_time = datetime.datetime.now()
        current_time_formatted = current_time.strftime('%I:%M:%S %p')

        if tf2_is_running and discord_is_running:
            if not client_connected:
                # connects to Discord
                client = ipc.DiscordIPC('429389143756374017')
                client.connect()

                # sends first status, starts on main menu
                # start_time = int(time.time())
                activity['timestamps']['start'] = start_time
                client.update_activity(activity)
                client_connected = True

            # defaults
            current_map = ''
            current_class = ''

            # modifies a few tf2 config files
            class_config_files(tf2_location)

            # console.log is a log of tf2's console (duh), only exists if tf2 has -condebug (see the bottom of config_files)
            consolelog_filename = '{}tf\\console.log'.format(tf2_location)
            with open(consolelog_filename, 'r', errors='replace') as consolelog_file:
                line = consolelog_file.readline()

                # iterates though every line in the log (I KNOW) and learns everything from it
                while line != '':
                    if 'Map: ' in line:
                        current_map = line[5:-1]
                        current_class = 'unselected'  # this variable is poorly named

                    if 'selected' in line and 'candidates' not in line:
                        current_class = line[:-11]

                    if 'Lobby destroyed' in line or 'Steam config directory:' in line or 'Dropped ' in line or 'Disconnect: ' in line:
                        current_map = 'In menus'  # so is this one
                        current_class = 'Not queued'

                    if '[PartyClient] Entering queue for ' in line:
                        current_map = 'In menus'
                        current_class = 'Queued for {}'.format(match_types[line[33:-1]])

                    if '[PartyClient] Entering standby queue ' in line:
                        current_map = 'In menus'
                        current_class = 'Queued for a party\'s match'

                    if '[PartyClient] Leaving queue' in line or '[PartyClient] Leaving standby queue' in line:
                        current_class = 'Not queued'

                    line = consolelog_file.readline()

            if current_map != 'In menus' and current_map != 'In queue':
                # not in menus = in a game
                try:
                    map_fancy, current_gamemode, gamemode_fancy = map_gamemodes[current_map]
                    activity['details'] = 'Map: {}'.format(map_fancy)
                    activity['assets']['large_image'] = current_gamemode
                    activity['assets']['large_text'] = gamemode_fancy
                except KeyError:
                    activity['details'] = 'Map: {}'.format(current_map)
                    activity['assets']['large_image'] = 'unknown_map'
                    activity['assets']['large_text'] = 'Unknown gamemode'

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
            time_elapsed = time.time() - start_time
            print("{:02}:{:02} elapsed".format(int(time_elapsed / 60), round(time_elapsed % 60)))
            print()

            # send everything to discord
            client.update_activity(activity)
        elif not discord_is_running:
            print("{}\nDiscord isn't running\n".format(current_time_formatted))
        else:
            if client_connected:
                try:
                    client.disconnect()  # doesn't work...
                except:
                    pass

                raise SystemExit  # ...but this does
            else:
                print("{}\nTF2 isn't running\n".format(current_time_formatted))

            # to prevent connecting when already connected
            client_connected = False

        # rich presence only updates every 15 seconds, but it listens constantly so sending every 5 seconds is fine
        time.sleep(5)


# allows the console to output 'class selected' on class choose
def class_config_files(exe_location):
    tf2_classes = ['Scout', 'Soldier', 'Pyro', 'Demoman', 'Heavy', 'Engineer', 'Medic', 'Sniper', 'Spy']

    for tf2_class in tf2_classes:
        # 'echo' means 'output to console' in source-speak
        selected_line = 'echo "{} selected"'.format(tf2_class)

        config_filename = tf2_class.lower().replace('heavy', 'heavyweapons')  # valve why

        # config files are at 'Steam\steamapps\common\Team Fortress 2\tf\cfg'
        try:
            # reads each existing class.cfg
            class_config_file = open('{}tf\\cfg\\{}.cfg'.format(exe_location, config_filename), 'r+', errors='replace')
            if selected_line not in class_config_file.read():
                # if it doesn't already have the echo line, add it
                class_config_file.write('\n\n' + selected_line)
        except FileNotFoundError:
            # the config file doesn't exist, so create it and add the echo line
            class_config_file = open('{}tf\\cfg\\{}.cfg'.format(exe_location, config_filename), 'w')
            class_config_file.write('\n\n' + selected_line)

        # I know a 'with open()' is better but eh
        class_config_file.close()


# reads steams launch options save file to find -condebug
def steam_config_file(exe_location):
    found_condebug = False

    for user_id_folder in next(os.walk(exe_location + 'userdata'))[1]:  # possibly multiple users for the same steam install
        try:
            # 'C:\Program Files (x86)\Steam\userdata\*user id number*\config\localconfig.vdf'
            with open('{}userdata\\{}\\config\\localconfig.vdf'.format(exe_location, user_id_folder), 'r+', errors='replace') as global_config_file:
                lines = global_config_file.readlines()
                tf2_line_num = 0

                for line in enumerate(lines):
                    if line[1] == '\t\t\t\t\t"440"\n':  # looks for the tf2's number and finds the line number
                        tf2_line_num = line[0]

                for line_offset in range(1, 21):
                    launchoptions_line = lines[tf2_line_num + line_offset]
                    if 'LaunchOptions' in launchoptions_line:
                        if '-condebug' in launchoptions_line:
                            # oh also this might be slow to update
                            found_condebug = True
        except FileNotFoundError:
            pass

    if not found_condebug:
        # yell at the user to fix their settings
        print("\nYour TF2 installation doesn't seem to be set up properly. To fix:"
              "\n1. Right click on Team Fortress 2 in your Steam library"
              "\n2. Open properties (very bottom)"
              "\n3. Click \"Set launch options...\""
              "\n4. Add -condebug"
              "\n5. OK and Close\n")
        # -condebug is kinda necessary so just exit if it's not there
        raise SystemExit


if __name__ == '__main__':
    main()
