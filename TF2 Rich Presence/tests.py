# Copyright (C) 2018-2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import gc
import io
import os
import random
import shutil
import time
import tkinter as tk
import traceback
import unittest

import psutil
import requests
from discoIPC import ipc

import configs
import console_log
import game_state
import gamemodes
import gui
import launcher
import localization
import logger
import main
import processes
import settings
import settings_gui
import updater
import utils


class TestTF2RichPresense(unittest.TestCase):
    def setUp(self):
        settings.access_registry(save=settings.defaults())  # sorry if this changes your settings
        settings.change('request_timeout', 30)

        self.dir = os.getcwd()
        self.log = logger.Log('logs\\tests.log')
        self.log.force_disabled = True
        self.log.to_stderr = False
        self.log.sentry_enabled = False
        self.log.info(f"Starting test: {self.id()}")

        gc.enable()  # because main may have disabled it

    def tearDown(self):
        os.chdir(self.dir)
        del self.log
        settings.access_registry(save=settings.defaults())  # sorry if this changes your settings

    def test_interpret_console_log(self):
        recent_time = int(time.time()) - 10
        app = main.TF2RichPresense(self.log, set_process_priority=False)

        self.assertEqual(app.interpret_console_log('test_resources\\console_in_menus.log', {'not Kataiser'}, float('inf'), True), (True, '', '', '', 'Not queued', False))
        self.assertEqual(app.interpret_console_log('test_resources\\console_in_menus.log', {'not Kataiser'}, 4, True), (True, '', '', '', 'Not queued', False))
        self.assertEqual(app.interpret_console_log('test_resources\\console_queued_casual.log', {'not Kataiser'}, float('inf'), True), (True, '', '', '', 'Queued for Casual', False))
        self.assertEqual(app.interpret_console_log('test_resources\\console_badwater.log', {'not Kataiser'}, float('inf'), True), (False, 'pl_badwater', 'Pyro', '', 'Not queued', True))
        self.assertEqual(app.interpret_console_log('test_resources\\console_badwater.log', {'not Kataiser'}, float('inf'), True, recent_time), (True, '', '', '', 'Not queued', False))
        self.assertEqual(app.interpret_console_log('test_resources\\console_badwater.log', {'not Kataiser'}, 0.2, True), (True, '', '', '', 'Not queued', False))
        self.assertEqual(app.interpret_console_log('test_resources\\console_custom_map.log', {'not Kataiser'}, float('inf'), True),
                         (False, 'cp_catwalk_a5c', 'Soldier', '', 'Not queued', True))
        self.assertEqual(app.interpret_console_log('test_resources\\console_soundemitter.log', {'not Kataiser'}, float('inf'), True), (True, '', '', '', 'Not queued', False))
        self.assertEqual(app.interpret_console_log('test_resources\\console_queued_in_game.log', {'not Kataiser'}, float('inf'), True),
                         (False, 'itemtest', 'Heavy', '', 'Queued for Casual', True))
        self.assertEqual(app.interpret_console_log('test_resources\\console_canceled_load.log', {'not Kataiser'}, float('inf'), True), (True, '', '', '', 'Not queued', False))
        self.assertEqual(app.interpret_console_log('test_resources\\console_chat.log', {'not Kataiser'}, float('inf'), True), (False, 'itemtest', 'Scout', '', 'Not queued', True))
        self.assertEqual(app.interpret_console_log('test_resources\\console_empty.log', {'not Kataiser'}, float('inf'), True), (True, '', '', '', 'Not queued', False))
        self.assertEqual(app.interpret_console_log('test_resources\\console_valve_server.log', {'not Kataiser'}, float('inf'), True),
                         (False, 'pl_snowycoast', 'Pyro', '162.254.194.158:27048', 'Not queued', False))
        self.assertEqual(app.interpret_console_log('test_resources\\console_tf2bd.log', {'Kataiser'}, float('inf'), True),
                         (False, 'ctf_turbine', 'Soldier', '45.141.52.51:27015', 'Not queued', False))

        # tests trimming
        trimtest_small = 'test_resources\\console_badwater.log'
        trimtest_big = 'test_resources\\console_badwater_big.log'
        shutil.copy(trimtest_small, trimtest_big)
        with open(trimtest_big, 'rb+') as console_badwater_sacrifice:
            console_badwater_sacrifice.write(console_badwater_sacrifice.read())  # this just doubles the file size
        initial_size = os.stat(trimtest_big).st_size
        self.assertEqual(app.interpret_console_log(trimtest_big, {'not Kataiser'}), (False, 'pl_badwater', 'Pyro', '', 'Not queued', True))
        trimmed_size = os.stat(trimtest_big).st_size
        self.assertLess(trimmed_size, initial_size)
        self.assertEqual(trimmed_size, (1024 ** 2) * 2)
        os.remove(trimtest_big)

        # tests removing error and empty lines
        errorstest_big = 'test_resources\\console_in_menus.log'
        errorstest_small = 'test_resources\\console_in_menus_small.log'
        shutil.copy(errorstest_big, errorstest_small)
        initial_size = os.stat(errorstest_small).st_size
        with open(errorstest_small, 'r', encoding='UTF8') as errorstest_small_unclean:
            self.assertTrue('DataTable warning' in errorstest_small_unclean.read())
        app.interpret_console_log(errorstest_small, {'not Kataiser'}, float('inf'))
        cleaned_size = os.stat(errorstest_small).st_size
        self.assertLess(cleaned_size, initial_size)
        with open(errorstest_small, 'r', encoding='UTF8') as errorstest_small_cleaned:
            self.assertFalse('DataTable warning' in errorstest_small_cleaned.read())
        self.assertEqual(app.interpret_console_log(errorstest_small, {'not Kataiser'}, float('inf')), (True, '', '', '', 'Not queued', False))
        os.remove(errorstest_small)

    def test_non_ascii_in_usernames(self):
        self.assertFalse(console_log.non_ascii_in_usernames({'Hyde', 'Chocolate Thunder89', 'Sleepy'}))
        self.assertTrue(console_log.non_ascii_in_usernames({'Hyde', 'Chocolate Thunder89', '✿Sleepy✿'}))

    def test_steam_config_file(self):
        app = main.TF2RichPresense(self.log, set_process_priority=False)
        ref_launch_options = '-novid -noipx -refresh 120 -w 1920 -h 1080 -windowed -noborder -useforcedmparms -noforcemaccel -noforcemspd -dxlevel 95'
        self.assertEqual(configs.steam_config_file(app, 'test_resources\\', False), ref_launch_options)
        self.assertEqual(configs.steam_config_file(app, 'test_resources\\', True), None)

    def test_find_tf2_exe(self):
        app = main.TF2RichPresense(self.log, set_process_priority=False)
        self.assertEqual(app.find_tf2_exe('test_resources\\very real steam'), r'test_resources\very real steam 2\steamapps\common\Team Fortress 2\hl2.exe')

    def test_class_config_files(self):
        cfg_path = 'test_resources\\tf\\cfg'
        demo_path = f'{cfg_path}\\demoman.cfg'
        if not os.path.isdir('test_resources\\tf'):
            os.mkdir('test_resources\\tf')
        if os.path.isdir(cfg_path):
            shutil.rmtree(cfg_path)
            time.sleep(0.1)
        os.mkdir(cfg_path)
        configs.class_config_files(self.log, 'test_resources')
        self.assertEqual(len(os.listdir(cfg_path)), 9)
        open(demo_path, 'w').close()
        with open(demo_path, 'r') as demo_file:
            self.assertEqual(demo_file.read(), '')
        configs.class_config_files(self.log, 'test_resources')
        with open(demo_path, 'r') as demo_file:
            self.assertTrue('echo "Demoman selected"' in demo_file.read())
        shutil.rmtree(cfg_path)

    def test_get_steam_username(self):
        if processes.ProcessScanner(self.log).scan()['Steam']['running']:
            self.assertNotEqual(configs.get_steam_username(), '')
        else:
            self.skipTest("Steam isn't running, assuming it's not installed")

    def test_get_match_info(self):
        test_game_state = game_state.GameState(self.log)
        test_addresses = ('162.254.192.155:27053',  # valve
                          'us2.uncledane.com:27015',
                          '51.81.49.25:27015',  # creators.tf
                          '192.223.26.238:27015',  # lazypurple
                          '45.35.1.186:27065')  # blackwonder

        for test_address in test_addresses:
            try:
                server_data = test_game_state.get_match_data(test_address, ['Player count', 'Kills'])
                self.assertTrue(server_data['player_count'].startswith("Players: "))
                self.assertIn(server_data['player_count'].split('/')[1], ('24', '26', '30', '32'))
                self.assertEqual(server_data['kills'], "Kills: 0")
            except AssertionError as error:
                raise AssertionError(f'{test_address}, {error}')

        settings.change('request_timeout', 0.001)
        self.assertEqual(test_game_state.get_match_data(test_addresses[-1], ['Player count', 'Kills']), server_data)
        self.assertEqual(test_game_state.get_match_data('', ['Player count']), {'player_count': 'Players: ?/?'})

    def test_get_map_gamemode(self):
        self.assertEqual(gamemodes.get_map_gamemode(self.log, 'cp_dustbowl'), ['Dustbowl', 'attack-defend', 'Attack/Defend'])
        self.assertEqual(gamemodes.get_map_gamemode(self.log, 'koth_probed'), ['Probed', 'koth', 'King of the Hill'])
        self.assertEqual(gamemodes.get_map_gamemode(self.log, 'cp_catwalk_a5c'), ('cp_catwalk_a5c', 'control-point', 'Control Point'))
        self.assertEqual(gamemodes.get_map_gamemode(self.log, 'cp_orange_x3'), ('cp_orange_x3', 'cp-orange', 'Orange'))
        self.assertEqual(gamemodes.get_map_gamemode(self.log, 'surf_air_arena_v4'), ('surf_air_arena_v4', 'surfing', 'Surfing'))
        self.assertEqual(gamemodes.get_map_gamemode(self.log, 'ytsb8eitybw'), ('ytsb8eitybw', 'unknown', 'Unknown gamemode'))

    def test_logger(self):
        self.log.log_file.close()
        try:
            os.remove(self.log.filename)
        except (FileNotFoundError, PermissionError):
            pass

        self.log.force_disabled = False
        self.log.filename = 'test_resources\\test_self.log'

        try:
            os.remove(self.log.filename)
        except (FileNotFoundError, PermissionError):
            pass

        self.log.log_file = open(self.log.filename, 'a', encoding='UTF8')
        self.log.info("Test1 饏Ӟ򒚦R៣񘺏1ࠞͳⴺۋ")
        self.log.error(str(SystemError("Test2")), reportable=False)
        self.assertEqual(repr(self.log), r'logger.Log at test_resources\test_self.log (enabled=True, level=Debug, stderr=False)')
        settings.change('log_level', 'Error')
        self.log.debug("Gone. Reduced to atoms.")
        settings.change('log_level', 'Off')
        self.assertFalse(self.log.enabled())
        self.log.log_file.close()

        with open(self.log.filename, 'r', encoding='UTF8') as current_log_file:
            current_log_file_read = current_log_file.readlines()
            self.assertEqual(len(current_log_file_read), 2)
            self.assertTrue(current_log_file_read[0].endswith("] INFO: Test1 饏Ӟ򒚦R៣񘺏1ࠞͳⴺۋ\n"))
            self.assertTrue(current_log_file_read[1].endswith("] ERROR: Test2\n"))

        with self.assertRaises(IndexError):
            should_be_empty = current_log_file_read[2]

        os.remove(self.log.filename)

    def test_log_cleanup(self):
        old_dir = os.getcwd()
        os.chdir(os.path.abspath('test_resources'))

        try:
            shutil.rmtree('logs')  # if this test failed last run
            time.sleep(0.1)
        except FileNotFoundError:
            pass

        # make sure the modified times are actually in order
        shutil.copytree('empty_logs', 'logs')
        empty_logs = sorted(os.listdir('logs'))
        for file_num in range(7):
            modified_time = time.time() - file_num
            os.utime(os.path.join('logs', empty_logs[file_num]), times=(modified_time, modified_time))

        self.log.cleanup(4)
        self.assertEqual(os.listdir('logs'), ['0f784a27.log.gz', '267d4853.log.gz', '46b087ff.log.gz', '6cbf1447.log.gz'])
        self.log.cleanup(2)
        self.assertEqual(os.listdir('logs'), ['46b087ff.log.gz', '6cbf1447.log.gz'])
        shutil.rmtree('logs')

        os.chdir(old_dir)

    def test_access_github_api(self):
        try:
            newest_version, downloads_url, changelog = updater.access_github_api(10)
        except updater.RateLimitError as error:
            self.skipTest(error)
        else:
            self.assertTrue(newest_version.startswith('v') and '.' in newest_version)
            self.assertTrue(downloads_url.startswith('https://github.com/Kataiser/tf2-rich-presence/releases/tag/v'))
            self.assertTrue(len(changelog) > 0)

            with self.assertRaises(requests.Timeout):
                updater.access_github_api(0.0001)

    def test_format_changelog(self):
        unformatted = "## Changes\n" \
                      "- This is a change or addition of some sort\n" \
                      "- This is a second change\n" \
                      "## Fixes\n" \
                      "- This is a bug fix\n" \
                      "   - This is a sub-point\n" \
                      "- This is another bug fix\n" \
                      "\n" \
                      "This is some extra text"

        formatted = "  Changes\n" \
                    "   - This is a change or addition of some sort\n" \
                    "   - This is a second change\n" \
                    "  Fixes\n" \
                    "   - This is a bug fix\n" \
                    "     - This is a sub-point\n" \
                    "   - This is another bug fix\n" \
                    "  \n" \
                    "  This is some extra text"

        self.assertEqual(updater.format_changelog(unformatted), formatted)

    def test_settings_check_int(self):
        self.assertTrue(settings_gui.check_int(''))
        self.assertTrue(settings_gui.check_int('1'))
        self.assertTrue(settings_gui.check_int('1000'))
        self.assertTrue(settings_gui.check_int('60'))

        self.assertFalse(settings_gui.check_int('a'))
        self.assertFalse(settings_gui.check_int('abc123qwe098'))
        self.assertFalse(settings_gui.check_int('-1'))

    def test_settings_access(self):
        default_settings = settings.defaults()

        for setting in default_settings:
            self.assertEqual(type(default_settings[setting]), type(settings.get(setting)))

    def test_compare_settings(self):
        self.assertEqual(settings.compare_settings({'a': 'b', 'c': 'd'}, {'a': 'b', 'c': 'e'}), {'c': 'e'})

    def test_fix_settings(self):
        broken = settings.defaults()
        del broken['wait_time']
        broken['fake'] = True
        settings.access_registry(save=broken)
        settings.fix_settings(self.log)
        self.assertEqual(settings.access_registry(), settings.defaults())

    def test_get_api_key(self):
        self.assertEqual(len(utils.get_api_key('discord')), 18)
        self.assertEqual(len(utils.get_api_key('discord2')), 18)
        self.assertEqual(len(utils.get_api_key('sentry')), 91)

    def test_load_maps_db(self):
        maps_db = gamemodes.load_maps_db()
        self.assertEqual(len(maps_db), 123)

        for map_ in maps_db:
            self.assertEqual(len(set(maps_db[map_])), 3)

    def test_discoipc(self):
        # this test fails if Discord isn't running
        test_process_scanner = processes.ProcessScanner(self.log)
        if not test_process_scanner.scan()['Discord']['running']:
            self.skipTest("Discord needs to be running")

        activity = {'details': "Testing TF2 Rich Presence",
                    'timestamps': {'start': int(time.time())},
                    'assets': {'small_image': 'tf2_icon_small', 'small_text': 'Team Fortress 2', 'large_image': 'main_menu',
                               'large_text': 'In menus'},
                    'state': "(Probably don't actually have the game open)"}

        client = ipc.DiscordIPC('429389143756374017')
        time.sleep(0.1)  # this fix works? seriously?
        client.connect()
        client.update_activity(activity)
        client_state = (client.client_id, client.connected, client.ipc_path, isinstance(client.pid, int), client.platform, isinstance(client.socket, io.BufferedRandom), client.socket.name)
        self.assertEqual(client_state, ('429389143756374017', True, '\\\\?\\pipe\\discord-ipc-0', True, 'windows', True, '\\\\?\\pipe\\discord-ipc-0'))

        client.disconnect()
        client_state = (client.client_id, client.connected, client.ipc_path, isinstance(client.pid, int), client.platform, client.socket)
        self.assertEqual(client_state, ('429389143756374017', False, '\\\\?\\pipe\\discord-ipc-0', True, 'windows', None))

    def test_process_scanning(self):
        process_scanner = processes.ProcessScanner(self.log)
        process_scanner.executables['posix'].append('python')
        process_scanner.executables['nt'].append('python')

        self.assertEqual(len(process_scanner.scan()), 3)
        p_info = process_scanner.get_process_info(os.getpid(), ('path', 'time'))

        self.assertEqual(p_info['running'], True)
        self.assertTrue('python' in p_info['path'].lower())  # hope your Python installation is sane
        self.assertGreater(p_info['time'], 1228305600)  # Python 3 release date lol

        self.assertFalse(process_scanner.hl2_exe_is_tf2(os.getpid()))

    def test_settings_gui(self):
        root = tk.Toplevel()
        settings_gui_test = settings_gui.GUI(root, self.log)
        settings_gui_test.wait_time.set(3)
        settings_gui_test.setting_changed()
        working_settings = settings_gui_test.get_working_settings()
        settings_gui_test.update()
        dimensions = settings_gui_test.window_dimensions
        settings_gui_test.language.set('日本語')
        settings_gui_test.update_language('日本語')
        new_dimensions = settings_gui_test.window_dimensions
        settings_gui_test.wait_time.set(3)
        settings_gui_test.save_and_close(force=True)

        self.assertEqual(len(working_settings), len(settings.defaults()))
        self.assertEqual(working_settings['wait_time'], 3)
        self.assertEqual(settings.get('wait_time'), 3)
        self.assertGreaterEqual(dimensions[0], 200)
        self.assertGreaterEqual(dimensions[1], 200)
        self.assertGreaterEqual(new_dimensions[0], 200)
        self.assertGreaterEqual(new_dimensions[1], 200)

    def test_localization(self):
        all_keys = tuple(localization.access_localization_file().keys())
        english_lines = [localization.access_localization_file()[key]['English'] for key in all_keys]
        num_lines_total = len(english_lines)
        incorrect_hashes = []
        test_text = "This text isn't in the file"

        for key in all_keys:
            test_key = localization.hash_text(localization.access_localization_file()[key]['English'])

            if key != test_key:
                incorrect_hashes.append((key, test_key, localization.access_localization_file()[key]['English']))

        self.assertEqual(incorrect_hashes, [])

        for language in ['English', 'German', 'French', 'Spanish', 'Portuguese', 'Italian', 'Dutch', 'Polish', 'Russian', 'Korean', 'Chinese', 'Japanese']:
            localizer = localization.Localizer(language=language, persist_missing=False)
            self.assertEqual(repr(localizer), f'localization.Localizer ({language}, appending=False, 0 missing lines)')

            num_equal_lines = 0
            for line_english in english_lines:
                line_localized = localizer.text(line_english)

                try:
                    self.assertNotEqual(line_localized, "")
                    self.assertEqual(line_localized.count('{0}'), line_english.count('{0}'))
                    self.assertEqual(line_localized.count('{1}'), line_english.count('{1}'))
                except AssertionError as error:
                    raise AssertionError(f"{error}\n{line_english}\n{line_localized}")

                if line_localized == line_english:
                    num_equal_lines += 1

            if language == 'English':
                self.assertEqual(num_equal_lines, num_lines_total)
            else:
                self.assertLess(num_equal_lines, num_lines_total / 4)

            self.assertEqual(localizer.text(test_text), test_text)

        db = utils.access_db()
        self.assertTrue(test_text in db['missing_localization'])
        db['missing_localization'] = []
        utils.access_db(write=db)

    def test_main_simple(self):
        settings.change('wait_time_slow', 1)
        app = main.TF2RichPresense(self.log)
        self.assertEqual(repr(app), 'main.TF2RichPresense (state=init)')
        self.assertEqual(fix_activity_dict(app.game_state.activity()),
                         {'details': 'In menus',
                          'state': 'Not queued',
                          'timestamps': {'start': 0},
                          'assets': {'large_image': 'main_menu',
                                     'large_text': 'In menus - TF2 Rich Presence {tf2rpvnum}',
                                     'small_image': 'tf2_logo',
                                     'small_text': 'Team Fortress 2'}})
        app.run(once=True)
        self.assertEqual(repr(app), 'main.TF2RichPresense (state=no tf2)')
        self.assertEqual(fix_activity_dict(app.game_state.activity()),
                         {'details': 'In menus',
                          'state': 'Not queued',
                          'timestamps': {'start': 0},
                          'assets': {'large_image': 'main_menu',
                                     'large_text': 'In menus - TF2 Rich Presence {tf2rpvnum}',
                                     'small_image': 'tf2_logo',
                                     'small_text': 'Team Fortress 2'}})

        self_process = psutil.Process()
        self.assertEqual(self_process.nice(), psutil.BELOW_NORMAL_PRIORITY_CLASS)
        self.assertEqual(self_process.ionice(), psutil.IOPRIO_LOW)
        self_process.nice(psutil.NORMAL_PRIORITY_CLASS)
        self_process.ionice(psutil.IOPRIO_NORMAL)

        app.send_rpc_activity()

    def test_custom(self):
        settings.change('wait_time_slow', 1)
        big_number_file = f'test_{random.randint(10000, 99999)}.temp'

        with open('custom.py', 'r+') as custom_file:
            custom_old = custom_file.read()
            custom_file.seek(0)
            custom_file.truncate()
            custom_file.write("class TF2RPCustom:"
                              "\n\tdef __init__(self, app): pass"
                              "\n\tdef before_loop(self, app): pass"
                              "\n\tdef modify_game_state(self, app): pass"
                              "\n\tdef modify_gui(self, app): pass"
                              "\n\tdef modify_rpc_activity(self, app): pass"
                              f"\n\tdef after_loop(self, app): open('{big_number_file}', 'w').close()")
            custom_file.flush()

        app = main.TF2RichPresense(self.log, set_process_priority=False)
        app.run(once=True)
        self.assertTrue(os.path.isfile(big_number_file))
        time.sleep(0.2)

        for file in os.listdir():
            if file.startswith('test_') and file.endswith('.temp'):
                os.remove(file)

        with open('custom.py', 'r+') as custom_file:
            custom_file.truncate()
            custom_file.write(custom_old)

    def test_game_state(self):
        game_state_test = game_state.GameState(self.log)
        game_state_test.force_zero_map_time = True
        self.assertTrue(game_state_test.update_rpc)
        self.assertEqual(str(game_state_test), 'in menus, queued="Not queued"')

        game_state_test.set_bulk((True, '', '', '', 'Not queued', False))
        self.assertTrue(game_state_test.update_rpc)
        self.assertEqual(str(game_state_test), 'in menus, queued="Not queued"')
        self.assertEqual(fix_activity_dict(game_state_test.activity()),
                         {'details': 'In menus',
                          'state': 'Not queued',
                          'timestamps': {'start': 0},
                          'assets': {'large_image': 'main_menu',
                                     'large_text': 'In menus - TF2 Rich Presence {tf2rpvnum}',
                                     'small_image': 'tf2_logo',
                                     'small_text': 'Team Fortress 2'}})
        self.assertFalse(game_state_test.update_rpc)

        game_state_test.set_bulk((False, 'koth_highpass', 'Demoman', '', 'Not queued', True))
        self.assertTrue(game_state_test.update_rpc)
        self.assertEqual(str(game_state_test), 'Demoman on Highpass, gamemode=koth, hosting=True, queued="Not queued", server=')
        self.assertEqual(fix_activity_dict(game_state_test.activity()),
                         {'details': 'Map: Highpass (hosting)',
                          'state': 'Time on map: 0:00',
                          'timestamps': {'start': 0},
                          'assets': {'large_image': 'z_koth_highpass',
                                     'large_text': 'Highpass - TF2 Rich Presence {tf2rpvnum}',
                                     'small_image': 'demoman',
                                     'small_text': 'Demoman'}})
        self.assertTrue(game_state_test.update_rpc)

        settings.change('bottom_line', 'Class')
        game_state_test.set_bulk((False, 'koth_highpass', 'Demoman', '', 'Not queued', True))
        self.assertTrue(game_state_test.update_rpc)
        self.assertEqual(str(game_state_test), 'Demoman on Highpass, gamemode=koth, hosting=True, queued="Not queued", server=')
        self.assertEqual(fix_activity_dict(game_state_test.activity()),
                         {'details': 'Map: Highpass (hosting)',
                          'state': 'Class: Demoman',
                          'timestamps': {'start': 0},
                          'assets': {'large_image': 'z_koth_highpass',
                                     'large_text': 'Highpass - TF2 Rich Presence {tf2rpvnum}',
                                     'small_image': 'demoman',
                                     'small_text': 'Demoman'}})
        self.assertFalse(game_state_test.update_rpc)

        settings.access_registry(save=settings.defaults())
        game_state_test.set_bulk((False, 'pl_snowycoast', 'Pyro', '162.254.192.155:27053', 'Not queued', False))
        self.assertTrue(game_state_test.update_rpc)
        game_state_test.update_server_data(['Player count'], {'Kataiser'})
        self.assertEqual(str(game_state_test), 'Pyro on Snowycoast, gamemode=payload, hosting=False, queued="Not queued", server=162.254.192.155:27053')
        self.assertEqual(fix_activity_dict(game_state_test.activity()),
                         {'details': 'Players: 0/0',
                          'state': 'Time on map: 0:00',
                          'timestamps': {'start': 0},
                          'assets': {'large_image': 'z_pl_snowycoast',
                                     'large_text': 'Snowycoast - TF2 Rich Presence {tf2rpvnum}',
                                     'small_image': 'pyro',
                                     'small_text': 'Pyro'}})
        self.assertTrue(game_state_test.update_rpc)

        settings.change('bottom_line', 'Kills')
        settings.change('server_rate_limit', 0)
        game_state_test.update_server_data(['Player count', 'Kills'], {'Kataiser'})
        self.assertEqual(fix_activity_dict(game_state_test.activity()),
                         {'details': 'Players: 0/0',
                          'state': 'Kills: 0',
                          'timestamps': {'start': 0},
                          'assets': {'large_image': 'z_pl_snowycoast',
                                     'large_text': 'Snowycoast - TF2 Rich Presence {tf2rpvnum}',
                                     'small_image': 'pyro',
                                     'small_text': 'Pyro'}})
        self.assertFalse(game_state_test.update_rpc)

        settings.access_registry(save=settings.defaults())
        game_state_test.set_bulk((False, 'cp_catwalk_a5c', 'Soldier', '', 'Queued for Casual', True))
        self.assertTrue(game_state_test.update_rpc)
        self.assertEqual(str(game_state_test), 'Soldier on cp_catwalk_a5c, gamemode=control-point, hosting=True, queued="Queued for Casual", server=')
        self.assertEqual(fix_activity_dict(game_state_test.activity()),
                         {'details': 'Map: cp_catwalk_a5c (hosting)',
                          'state': 'Queued for Casual',
                          'timestamps': {'start': 0},
                          'assets': {'large_image': 'control-point',
                                     'large_text': 'Control Point - TF2 Rich Presence {tf2rpvnum}',
                                     'small_image': 'soldier',
                                     'small_text': 'Soldier'}})
        self.assertFalse(game_state_test.update_rpc)

        game_state_test.set_bulk((False, 'arena_badlands', 'Engineer', '', 'Not queued', True))
        self.assertTrue(game_state_test.update_rpc)
        self.assertEqual(str(game_state_test), 'Engineer on Badlands (Arena), gamemode=arena, hosting=True, queued="Not queued", server=')
        self.assertEqual(fix_activity_dict(game_state_test.activity()),
                         {'details': 'Map: Badlands (Arena) (hosting)',
                          'state': 'Time on map: 0:00',
                          'timestamps': {'start': 0},
                          'assets': {'large_image': 'z_cp_badlands',
                                     'large_text': 'Badlands (Arena) - TF2 Rich Presence {tf2rpvnum}',
                                     'small_image': 'engineer',
                                     'small_text': 'Engineer'}})
        self.assertTrue(game_state_test.update_rpc)

    def test_gui(self):
        gui_test = gui.GUI(self.log)
        gui_test.set_clean_console_log_button_state(True)
        gui_test.set_launch_tf2_button_state(True)

        for state in [i for i in range(5)]:
            gui.test_state(gui_test, state)
            gui_test.safe_update()

        self.assertEqual((gui_test.text_state, gui_test.bg_state, gui_test.fg_state, gui_test.class_state),
                         (('Map: cp_catwalk_a5c (hosting)', 'Players: ?/?', 'Time on map: 2:39', '06:21 elapsed'),
                          ('bg_modes/control-point', 77, 172), 'fg_modes/control-point', 'classes/pyro'))

        for state in [4 - i for i in range(5)]:
            gui.test_state(gui_test, state)
            gui_test.safe_update()

        self.assertEqual((gui_test.text_state, gui_test.bg_state, gui_test.fg_state, gui_test.class_state), (("Team Fortress 2 isn't running",), ('default', 0, 0), '', ''))

        gui_test.bottom_text_queue_state = "Queued for Casual"
        self.assertEqual(gui_test.set_bottom_text('queued', True), "Queued for Casual")
        self.assertEqual(gui_test.set_bottom_text('discord', True), "Can't connect to Discord")
        self.assertEqual(gui_test.set_bottom_text('discord', False), "Queued for Casual")
        self.assertEqual(gui_test.set_bottom_text('queued', False), "")

        gui_test.pause()
        gui_test.unpause()
        gui_test.enable_update_notification()
        gui_test.check_for_updates(popup=True)
        gui_test.holiday()
        gui_test.menu_open_settings()
        gui_test.menu_about(silent=True)

        fg_image = gui_test.fg_image_load('tf2_logo', 120)
        self.assertEqual((fg_image.width(), fg_image.height()), (120, 120))
        gui_test.scale = 2
        gui_test.fg_image_load.cache_clear()
        fg_image = gui_test.fg_image_load('tf2_logo', 120)
        self.assertEqual((fg_image.width(), fg_image.height()), (240, 240))

        with self.assertRaises(SystemExit):
            gui_test.menu_exit()

    def test_set_gui_from_game_state(self):
        app = main.TF2RichPresense(self.log, set_process_priority=False)
        app.game_state.force_zero_map_time = True

        app.game_state.set_bulk((True, '', '', '', 'Not queued', False))
        app.set_gui_from_game_state()
        self.assertEqual((app.gui.text_state, app.gui.bg_state, app.gui.fg_state, app.gui.class_state),
                         (('In menus', 'Not queued', '0:00 elapsed'),
                          ('main_menu', 85, 164), 'tf2_logo', ''))

        app.game_state.set_bulk((False, 'plr_hightower', 'Heavy', '', 'Not queued', True))
        app.game_state.update_server_data(['Player count'], set())
        app.set_gui_from_game_state()
        self.assertEqual((app.gui.text_state, app.gui.bg_state, app.gui.fg_state, app.gui.class_state),
                         (('Map: Hightower (hosting)', 'Players: ?/?', 'Time on map: 0:00', '0:00 elapsed'),
                          ('bg_modes/payload-race', 77, 172), 'fg_maps/plr_hightower', 'classes/heavy'))

        app.game_state.set_bulk((False, 'tr_dustbowl', 'Scout', '', 'Queued for Casual', True))
        app.set_gui_from_game_state()
        self.assertEqual((app.gui.text_state, app.gui.bg_state, app.gui.fg_state, app.gui.class_state),
                         (('Map: Dustbowl (Training) (hosting)', 'Players: ?/?', 'Time on map: 0:00', '0:00 elapsed'),
                          ('bg_modes/training', 77, 172), 'fg_maps/cp_dustbowl', 'classes/scout'))
        self.assertEqual(app.gui.bottom_text_state, {'discord': False, 'kataiser': False, 'queued': True, 'holiday': False})

        app.game_state.set_bulk((False, 'itemtest', 'Spy', '', 'Not queued', True))
        app.set_gui_from_game_state()
        self.assertEqual((app.gui.text_state, app.gui.bg_state, app.gui.fg_state, app.gui.class_state),
                         (('Map: itemtest (hosting)', 'Players: ?/?', 'Time on map: 0:00', '0:00 elapsed'),
                          ('bg_modes/unknown', 77, 172), 'fg_modes/unknown', 'classes/spy'))

        app.game_state.set_bulk((False, 'cp_steel', 'Medic', '162.254.192.155:27053', 'Not queued', False))
        app.game_state.update_server_data(['Player count'], set())
        app.set_gui_from_game_state()
        state = [list(app.gui.text_state), app.gui.bg_state, app.gui.fg_state, app.gui.class_state]
        state[0][1] = 'Players: 0/24' if 'Players: ' in state[0][1] and '/24' in state[0][1] else state[0][1]
        self.assertEqual(state, [['Map: Steel', 'Players: 0/24', 'Time on map: 0:00', '0:00 elapsed'],
                                 ('bg_modes/attack-defend', 77, 172), 'fg_maps/cp_steel', 'classes/medic'])
        self.assertEqual(app.gui.bottom_text_state, {'discord': False, 'kataiser': False, 'queued': False, 'holiday': False})

        app.game_state.set_bulk((False, 'plr_highertower', 'Engineer', '', 'Not queued', True))
        app.game_state.update_server_data(['Player count'], set())
        app.set_gui_from_game_state()
        state = [list(app.gui.text_state), app.gui.bg_state, app.gui.fg_state, app.gui.class_state]
        state[0][1] = 'Players: 0/24' if 'Players: ' in state[0][1] and '/24' in state[0][1] else state[0][1]
        self.assertEqual((app.gui.text_state, app.gui.bg_state, app.gui.fg_state, app.gui.class_state),
                         (('Map: plr_highertower (hosting)', 'Players: ?/?', 'Time on map: 0:00', '0:00 elapsed'),
                          ('bg_modes/payload-race', 77, 172), 'fg_modes/payload-race', 'classes/engineer'))

    def test_game_state_localized(self):
        settings.change('language', 'Spanish')
        game_state_test = game_state.GameState(self.log)
        game_state_test.force_zero_map_time = True

        game_state_test.set_bulk((False, 'ctf_mexico_b4', 'Engineer', '', 'Not queued', True))
        self.assertTrue(game_state_test.update_rpc)
        self.assertEqual(str(game_state_test), 'Engineer on ctf_mexico_b4, gamemode=ctf, hosting=True, queued="Not queued", server=')
        self.assertEqual(fix_activity_dict(game_state_test.activity()),
                         {'details': 'Mapa: ctf_mexico_b4 (alojamiento)',
                          'state': 'El tiempo en el mapa: 0:00',
                          'timestamps': {'start': 0},
                          'assets': {'large_image': 'ctf',
                                     'large_text': 'Capturar la Bandera - TF2 Presencia Rica {tf2rpvnum}',
                                     'small_image': 'engineer',
                                     'small_text': 'Engineer'}})
        self.assertTrue(game_state_test.update_rpc)

    def test_set_gui_from_game_state_localized(self):
        settings.change('language', 'German')
        app = main.TF2RichPresense(self.log, set_process_priority=False)
        app.game_state.force_zero_map_time = True

        app.game_state.set_bulk((False, 'mvm_rottenburg', 'Medic', '', 'Queued for MvM (Boot Camp)', True))
        app.game_state.update_server_data(['Player count'], set())
        app.set_gui_from_game_state()
        self.assertEqual((app.gui.text_state, app.gui.bg_state, app.gui.fg_state, app.gui.class_state),
                         (('Karte: Rottenburg (Hosting)', 'Spieler: ?/?', 'Zeit auf der Karte: 0:00', '0:00 verstrichen'),
                          ('bg_modes/mvm', 77, 172), 'fg_maps/mvm_rottenburg', 'classes/medic'))
        self.assertEqual(app.gui.bottom_text_queue_state, "Warteschlange für MvM (Boot Camp)")

    def test_launcher(self):
        launcher.main(launch=False)

        try:
            raise Exception("test")
        except Exception:
            launcher.exc_already_reported(traceback.format_exc())


def fix_activity_dict(activity):
    try:
        activity['timestamps']['start'] = int(activity['timestamps']['start'] * 0)

        if 'Players:' in activity['state']:
            activity['state'] = 'Players: 0/0'

        if 'Players:' in activity['details']:
            activity['details'] = 'Players: 0/0'
    except KeyError:
        pass

    return activity


if __name__ == '__main__':
    print("Started tests via __main__")
    print(f"Files in {os.getcwd()}: {os.listdir(os.getcwd())}")
    unittest.main(verbosity=2)
