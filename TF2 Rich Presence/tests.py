# Copyright (C) 2018-2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import gc
import io
import os
import shutil
import time
import tkinter as tk
import unittest

import psutil
import requests
from discoIPC import ipc

import configs
import game_state
import gamemodes
import gui
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
        self.log = logger.Log()
        self.log.force_disabled = True
        self.log.to_stderr = False
        self.log.sentry_enabled = False

        gc.enable()  # because main may have disabled it

    def tearDown(self):
        os.chdir(self.dir)
        del self.log

        # fix a failed test_missing_files
        for file in os.listdir():
            if file.startswith('.') and os.path.isfile(file):
                if os.path.isfile(file[1:]):
                    os.remove(file[1:])
                os.rename(file, file[1:])

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

    def test_steam_config_file(self):
        app = main.TF2RichPresense(self.log, set_process_priority=False)
        self.assertEqual(configs.steam_config_file(app, 'test_resources\\'), {'Kataiser'})

    def test_get_match_info(self):
        test_game_state = game_state.GameState()
        test_addresses = ('162.254.194.158:27048',  # valve
                          'us2.uncledane.com:27015',
                          '51.81.49.25:27015',  # creators.tf
                          '192.223.26.238:27015',  # lazypurple
                          '45.35.1.186:27065')  # blackwonder

        for test_address in test_addresses:
            try:
                server_data = test_game_state.get_match_data(test_address, ['Player count', 'Kills'])
                self.assertTrue(server_data['player_count'].startswith("Players: "))
                self.assertIn(server_data['player_count'].split('/')[1], ('24', '30', '32'))
                self.assertEqual(server_data['kills'], "Kills: 0")
            except AssertionError as error:
                raise AssertionError(f'{test_address}, {error}')

        test_game_state.last_server_request_time -= settings.get('server_rate_limit')
        self.assertEqual(test_game_state.get_match_data('', 'Player count'), {'player_count': 'Players: ?/?'})

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
        self.log.log_file.close()

        with open(self.log.filename, 'r', encoding='UTF8') as current_log_file:
            current_log_file_read = current_log_file.readlines()
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
        p_info = process_scanner.get_info_from_pid(os.getpid(), ('path', 'time'))

        self.assertEqual(p_info['running'], True)
        self.assertTrue('python' in p_info['path'].lower())  # hope your Python installation is sane
        self.assertGreater(p_info['time'], 1228305600)  # Python 3 release date lol

        self.assertFalse(process_scanner.hl2_exe_is_tf2(os.getpid()))

    def test_settings_gui(self):
        root = tk.Tk()
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

        for key in all_keys:
            test_key = localization.hash_text(localization.access_localization_file()[key]['English'])

            if key != test_key:
                incorrect_hashes.append((key, test_key, localization.access_localization_file()[key]['English']))

        self.assertEqual(incorrect_hashes, [])

        for language in ['English', 'German', 'French', 'Spanish', 'Portuguese', 'Italian', 'Dutch', 'Polish', 'Russian', 'Korean', 'Chinese', 'Japanese']:
            localizer = localization.Localizer(language=language)
            self.assertEqual(repr(localizer), f'localization.Localizer ({language}, appending=False, 0 missing lines)')

            num_equal_lines = 0
            for line_english in english_lines:
                try:
                    line_localized = localizer.text(line_english)
                except KeyError:
                    if localization.hash_text(line_english) in ('1040127901', '9411019900', '1004668653', '2473140856'):
                        continue
                    else:
                        raise

                self.assertNotEqual(line_localized, "")
                self.assertEqual(line_localized.count('{0}'), line_english.count('{0}'))
                self.assertEqual(line_localized.count('{1}'), line_english.count('{1}'))

                if line_localized == line_english:
                    num_equal_lines += 1

            if language == 'English':
                self.assertEqual(num_equal_lines, num_lines_total)
            else:
                self.assertLess(num_equal_lines, num_lines_total / 4)

    def test_main_simple(self):
        log = logger.Log()
        app = main.TF2RichPresense(log)
        self.assertEqual(repr(app), 'main.TF2RichPresense (state=init)')
        self.assertEqual(fix_activity_dict(app.game_state.activity()),
                         {'details': 'In menus',
                          'state': 'Not queued',
                          'timestamps': {'start': 0},
                          'assets': {'large_image': 'main_menu',
                                     'large_text': 'In menus - TF2 Rich Presence {tf2rpvnum}',
                                     'small_image': 'tf2_logo',
                                     'small_text': 'Team Fortress 2'}})
        app.loop_body()
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

    def test_game_state(self):
        game_state_test = game_state.GameState()
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
        game_state_test.set_bulk((False, 'pl_snowycoast', 'Pyro', '162.254.194.158:27048', 'Not queued', False))
        self.assertTrue(game_state_test.update_rpc)
        game_state_test.update_server_data(['Player count'], {'Kataiser'})
        self.assertEqual(str(game_state_test), 'Pyro on Snowycoast, gamemode=payload, hosting=False, queued="Not queued", server=162.254.194.158:27048')
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

        game_state_test.set_bulk((False, 'ctf_sawmill', 'Engineer', '', 'Not queued', True))
        self.assertTrue(game_state_test.update_rpc)
        self.assertEqual(str(game_state_test), 'Engineer on Sawmill (CTF), gamemode=ctf, hosting=True, queued="Not queued", server=')
        self.assertEqual(fix_activity_dict(game_state_test.activity()),
                         {'details': 'Map: Sawmill (CTF) (hosting)',
                          'state': 'Time on map: 0:00',
                          'timestamps': {'start': 0},
                          'assets': {'large_image': 'z_koth_sawmill',
                                     'large_text': 'Sawmill (CTF) - TF2 Rich Presence {tf2rpvnum}',
                                     'small_image': 'engineer',
                                     'small_text': 'Engineer'}})
        self.assertTrue(game_state_test.update_rpc)

    def test_gui(self):
        gui_test = gui.GUI(self.log)
        gui_test.set_clean_console_log_button_state(True)

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
        gui_test.holiday(silent=True)
        gui_test.menu_open_settings()
        gui_test.menu_about(silent=True)

        fg_image = gui_test.fg_image_load('tf2_logo', 120)
        self.assertEqual((fg_image.width(), fg_image.height()), (120, 120))
        gui_test.scale = 2
        gui_test.fg_image_load.cache_clear()
        fg_image = gui_test.fg_image_load('tf2_logo', 120)
        self.assertEqual((fg_image.width(), fg_image.height()), (240, 240))

        gui_test.menu_exit()

    def test_set_gui_from_game_state(self):
        app = main.TF2RichPresense(self.log, set_process_priority=False)
        app.game_state.force_zero_map_time = True

        app.game_state.set_bulk((False, 'plr_hightower', 'Heavy', '', 'Not queued', True))
        app.game_state.update_server_data(['Player count'], set())
        app.set_gui_from_game_state()
        self.assertEqual((app.gui.text_state, app.gui.bg_state, app.gui.fg_state, app.gui.class_state),
                         (('Map: Hightower (hosting)', 'Players: ?/?', 'Time on map: 0:00', '0:00 elapsed'),('bg_modes/payload-race', 77, 172), 'fg_maps/plr_hightower', 'classes/heavy'))

        app.game_state.set_bulk((False, 'cp_5gorge', 'Scout', '', 'Queued for Casual', True))
        app.set_gui_from_game_state()
        self.assertEqual((app.gui.text_state, app.gui.bg_state, app.gui.fg_state, app.gui.class_state),
                         (('Map: 5Gorge (5CP) (hosting)', 'Players: ?/?', 'Time on map: 0:00', '0:00 elapsed'), ('bg_modes/control-point', 77, 172), 'fg_maps/cp_gorge', 'classes/scout'))
        self.assertEqual(app.gui.bottom_text_state, {'discord': False, 'kataiser': False, 'queued': True})

        app.game_state.set_bulk((False, 'cp_steel', 'Medic', '162.254.194.158:27048', 'Not queued', False))
        app.game_state.update_server_data(['Player count'], set())
        app.set_gui_from_game_state()
        state = [list(app.gui.text_state), app.gui.bg_state, app.gui.fg_state, app.gui.class_state]
        state[0][1] = 'Players: 0/24' if 'Players: ' in state[0][1] and '/24' in state[0][1] else state[0][1]
        self.assertEqual(state, [['Map: Steel', 'Players: 0/24', 'Time on map: 0:00', '0:00 elapsed'], ('bg_modes/attack-defend', 77, 172), 'fg_maps/cp_steel', 'classes/medic'])
        self.assertEqual(app.gui.bottom_text_state, {'discord': False, 'kataiser': False, 'queued': False})

        app.game_state.set_bulk((False, 'plr_highertower', 'Engineer', '', 'Not queued', True))
        app.game_state.update_server_data(['Player count'], set())
        app.set_gui_from_game_state()
        state = [list(app.gui.text_state), app.gui.bg_state, app.gui.fg_state, app.gui.class_state]
        state[0][1] = 'Players: 0/24' if 'Players: ' in state[0][1] and '/24' in state[0][1] else state[0][1]
        self.assertEqual((app.gui.text_state, app.gui.bg_state, app.gui.fg_state, app.gui.class_state),
                         (('Map: plr_highertower (hosting)', 'Players: ?/?', 'Time on map: 0:00', '0:00 elapsed'),
                          ('bg_modes/payload-race', 77, 172), 'fg_modes/payload-race', 'classes/engineer'))


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
