# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
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
import custom_maps
import init
import localization
import logger
import main
import processes
import settings
import updater
import utils


class TestTF2RichPresense(unittest.TestCase):
    def setUp(self):
        self.old_settings = settings.access_registry()
        target_settings = settings.get_setting_default(return_all=True)
        if self.old_settings != target_settings:
            settings.access_registry(target_settings)

        self.dir = os.getcwd()
        self.log = logger.Log()
        self.log.enabled = False
        self.log.to_stderr = False
        self.log.sentry_enabled = False
        self.log.log_levels_allowed = self.log.log_levels

        gc.enable()  # because init, main, or settings may have disabled it

    def tearDown(self):
        os.chdir(self.dir)
        del self.log
        settings.access_registry(save_dict=self.old_settings)

    def test_interpret_console_log(self):
        recent_time = int(time.time()) - 10
        app = main.TF2RichPresense(self.log, set_process_priority=False)

        self.assertEqual(app.interpret_console_log('test_resources\\console_in_menus.log', ['not Kataiser'], float('inf'), True), ('In menus', 'Not queued'))
        self.assertEqual(app.interpret_console_log('test_resources\\console_in_menus.log', ['not Kataiser'], 4, True), ('In menus', 'Not queued'))
        self.assertEqual(app.interpret_console_log('test_resources\\console_queued_casual.log', ['not Kataiser'], float('inf'), True), ('In menus', 'Queued for Casual'))
        self.assertEqual(app.interpret_console_log('test_resources\\console_badwater.log', ['not Kataiser'], float('inf'), True), ('pl_badwater (hosting)', 'Pyro'))
        self.assertEqual(app.interpret_console_log('test_resources\\console_badwater.log', ['not Kataiser'], float('inf'), True, recent_time), ('In menus', 'Not queued'))
        self.assertEqual(app.interpret_console_log('test_resources\\console_badwater.log', ['not Kataiser'], 0.2, True), ('In menus', 'Not queued'))
        self.assertEqual(app.interpret_console_log('test_resources\\console_custom_map.log', ['not Kataiser'], float('inf'), True), ('cp_catwalk_a5c (hosting)', 'Soldier'))
        self.assertEqual(app.interpret_console_log('test_resources\\console_soundemitter.log', ['not Kataiser'], float('inf'), True), ('In menus', 'Not queued'))
        self.assertEqual(app.interpret_console_log('test_resources\\console_queued_in_game.log', ['not Kataiser'], float('inf'), True), ('itemtest (hosting)', 'Queued for Casual'))
        self.assertEqual(app.interpret_console_log('test_resources\\console_empty.log', ['not Kataiser'], float('inf'), True), ('In menus', 'Not queued'))

        # tests trimming
        trimtest_small = 'test_resources\\console_badwater.log'
        trimtest_big = 'test_resources\\console_badwater_big.log'
        shutil.copy(trimtest_small, trimtest_big)
        with open(trimtest_big, 'rb+') as console_badwater_sacrifice:
            console_badwater_sacrifice.write(console_badwater_sacrifice.read())
        initial_size = os.stat(trimtest_big).st_size
        self.assertEqual(app.interpret_console_log(trimtest_big, ['not Kataiser']), ('pl_badwater (hosting)', 'Pyro'))
        trimmed_size = os.stat(trimtest_big).st_size
        self.assertLess(trimmed_size, initial_size)
        self.assertEqual(trimmed_size, (1024 ** 2) * 2)
        os.remove(trimtest_big)

        # tests removing empty lines
        emptytest_big = 'test_resources\\console_in_menus.log'
        emptytest_small = 'test_resources\\console_in_menus_small.log'
        shutil.copy(emptytest_big, emptytest_small)
        initial_size = os.stat(emptytest_small).st_size
        app.interpret_console_log(emptytest_small, ['not Kataiser'], float('inf'))
        cleaned_size = os.stat(emptytest_small).st_size
        print(initial_size, cleaned_size)
        self.assertLess(cleaned_size, initial_size)
        self.assertEqual(app.interpret_console_log(emptytest_small, ['not Kataiser'], float('inf')), ('In menus', 'Not queued'))
        os.remove(emptytest_small)

    def test_steam_config_file(self):
        app = main.TF2RichPresense(self.log, set_process_priority=False)
        self.assertEqual(configs.steam_config_file(app, 'test_resources\\'), {'Kataiser'})

    def test_find_custom_map_gamemode(self):
        try:
            requests.get(f'https://teamwork.tf/api/v1/quickplay?key={utils.get_api_key("teamwork")}', timeout=5)
        except (requests.ConnectTimeout, requests.ReadTimeout):
            self.skipTest("Teamwork.tf's API seems to be down")

        custom_maps.access_custom_maps_cache({})  # flush cache

        # test a couple common maps (in maps.json)
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'minecraftworld_a7', False, 5)), ('trading', 'Trading'))
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'mge_training_v8_beta4b', False, 5)), ('training', 'Training'))

        # don't use cache, force using the API (5 second timeout)
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'cp_catwalk_a5c', True, 5)), ('control-point', 'Control Point'))
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'cp_orange_x3', True, 5)), ('cp-orange', 'Orange'))
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'surf_air_arena_v4', True, 5)), ('surfing', 'Surfing'))
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'ytsb8eitybw', True, 5)), ('unknown_map', 'Unknown gamemode'))

        # cache allowed now
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'cp_catwalk_a5c', False, 5)), ('control-point', 'Control Point'))
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'cp_orange_x3', False, 5)), ('cp-orange', 'Orange'))
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'surf_air_arena_v4', False, 5)), ('surfing', 'Surfing'))
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'ytsb8eitybw', False, 5)), ('unknown_map', 'Unknown gamemode'))

    def test_logger(self):
        self.log.log_file.close()
        try:
            os.remove(self.log.filename)
        except (FileNotFoundError, PermissionError):
            pass

        self.log.enabled = True
        self.log.filename = 'test_resources\\test_self.log'

        try:
            os.remove(self.log.filename)
        except (FileNotFoundError, PermissionError):
            pass

        self.log.log_file = open(self.log.filename, 'a', encoding='UTF8')
        self.log.info("Test1 饏Ӟ򒚦R៣񘺏1ࠞͳⴺۋ")
        self.log.error(SystemError("Test2"), reportable=False)
        self.assertEqual(repr(self.log), r'logger.Log at test_resources\test_self.log (enabled=True level=Debug, stderr=False)')
        self.log.log_file.close()

        with open(self.log.filename, 'r', encoding='UTF8') as current_log_file:
            current_log_file_read = current_log_file.readlines()
            self.assertTrue(current_log_file_read[0].endswith("] INFO: Test1 饏Ӟ򒚦R៣񘺏1ࠞͳⴺۋ\n"))
            self.assertTrue(current_log_file_read[1].endswith("] ERROR: Test2\n"))

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
                updater.access_github_api(0.01)

    def test_format_changelog(self):
        unformatted = "## Changes" \
                      "\n- This is a change or addition of some sort" \
                      "\n- This is a second change" \
                      "\n## Fixes" \
                      "\n- This is a bug fix" \
                      "\n- This is another bug fix" \
                      "\n" \
                      "\nThis is some extra text"

        formatted = "  Changes" \
                    "\n   - This is a change or addition of some sort" \
                    "\n   - This is a second change" \
                    "\n  Fixes" \
                    "\n   - This is a bug fix" \
                    "\n   - This is another bug fix" \
                    "\n  " \
                    "\n  This is some extra text"

        self.assertEqual(updater.format_changelog(unformatted), formatted)

    def test_settings_check_int(self):
        self.assertTrue(settings.check_int('', 1000))
        self.assertTrue(settings.check_int('1', 1000))
        self.assertTrue(settings.check_int('1000', 1000))
        self.assertTrue(settings.check_int('60', 60))

        self.assertFalse(settings.check_int('1001', 1000))
        self.assertFalse(settings.check_int('61', 60))
        self.assertFalse(settings.check_int('a', 1000))
        self.assertFalse(settings.check_int('abc123qwe098', 1000))

    def test_settings_access(self):
        default_settings = settings.get_setting_default(return_all=True)

        for setting in default_settings:
            self.assertEqual(type(default_settings[setting]), type(settings.get(setting)))

    def test_fix_missing_settings(self):
        test_default = {'a': 1, 'b': '2', 'c': True}
        test_current = {'a': 1, 'c': True}
        test_missing = settings.fix_missing_settings(test_default, test_current)

        self.assertEqual(test_missing, {'b': '2'})

    def test_get_api_key(self):
        self.assertEqual(len(utils.get_api_key('discord')), 18)
        self.assertEqual(len(utils.get_api_key('teamwork')), 32)
        self.assertEqual(len(utils.get_api_key('pastebin')), 32)
        self.assertEqual(len(utils.get_api_key('sentry')), 91)

    def test_load_maps_db(self):
        maps_db = utils.load_maps_db()
        self.assertGreater(len(maps_db['official']), 20)
        self.assertGreater(len(maps_db['common_custom']), 10)
        self.assertGreater(len(maps_db['creators_tf']), 5)

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

    def test_generate_delta(self):
        localizer1 = localization.Localizer(language='English')
        localizer2 = localization.Localizer(language='Spanish')

        self.assertEqual(utils.generate_delta(localizer1, time.time() - 1), ' (+1 second)')
        self.assertEqual(utils.generate_delta(localizer1, time.time() - 10), ' (+10 seconds)')
        self.assertEqual(utils.generate_delta(localizer1, time.time() - 100), ' (+1.7 minutes)')
        self.assertEqual(utils.generate_delta(localizer1, time.time() - 1000), ' (+16.7 minutes)')
        self.assertEqual(utils.generate_delta(localizer1, time.time() - 10000), ' (+2.8 hours)')
        self.assertEqual(utils.generate_delta(localizer1, time.time() - 100000), ' (+1.2 days)')

        self.assertEqual(utils.generate_delta(localizer2, time.time() - 1), ' (+1 segundo)')
        self.assertEqual(utils.generate_delta(localizer2, time.time() - 10), ' (+10 segundos)')
        self.assertEqual(utils.generate_delta(localizer2, time.time() - 100), ' (+1.7 minutos)')
        self.assertEqual(utils.generate_delta(localizer2, time.time() - 1000), ' (+16.7 minutos)')
        self.assertEqual(utils.generate_delta(localizer2, time.time() - 10000), ' (+2.8 horas)')
        self.assertEqual(utils.generate_delta(localizer2, time.time() - 100000), ' (+1.2 días)')

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

    def test_settings_gui(self, skip=True):
        if skip:
            self.skipTest("Run by test_missing_files instead (try setting skip's default to False to see why)")

        root = tk.Tk()
        settings_gui = settings.GUI(root, self.log)
        settings_gui.show_font_message('한국어')
        settings_gui.update()
        dimensions = settings_gui.window_dimensions
        settings_gui.language.set('日本語')
        settings_gui.update_language('日本語')
        new_dimensions = settings_gui.window_dimensions
        settings_gui.destroy()

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
                    if localization.hash_text(line_english) in all_keys[-4:]:
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
        self.assertEqual(fix_activity_dict(app.activity),
                         {'details': 'In menus', 'timestamps': {'start': 0}, 'assets': {'small_image': 'tf2_icon_small', 'small_text': 'Team Fortress 2',
                                                                                        'large_image': 'main_menu', 'large_text': 'Main menu'}, 'state': ''})
        app.loop_body()
        self.assertEqual(repr(app), 'main.TF2RichPresense (state=no tf2)')
        self.assertEqual(fix_activity_dict(app.activity),
                         {'details': 'In menus', 'timestamps': {'start': 0}, 'assets': {'small_image': 'tf2_icon_small', 'small_text': 'Team Fortress 2',
                                                                                        'large_image': 'main_menu', 'large_text': 'Main menu'}, 'state': ''})

        self_process = psutil.Process()
        self_process.nice(psutil.NORMAL_PRIORITY_CLASS)
        self_process.ionice(psutil.IOPRIO_NORMAL)

    def test_init(self):
        try:
            init.launch(0)
        except updater.RateLimitError as error:
            self.skipTest(error)

    def test_missing_files(self):
        files_to_hide = ['tf2_logo_blurple.ico', 'tf2_logo_blurple_wrench.ico', 'DB.json', 'localization.json', 'maps.json', 'custom.py']

        for file in files_to_hide:
            os.rename(file, f'.{file}')

        self.test_main_simple()
        self.test_settings_gui(skip=False)

        for file in files_to_hide:
            if os.path.isfile(file):
                os.remove(file)

            os.rename(f'.{file}', file)


def fix_activity_dict(activity):
    try:
        activity['timestamps']['start'] = int(activity['timestamps']['start'] * 0)
    except KeyError:
        pass

    return activity


if __name__ == '__main__':
    print("Started tests via __main__")
    print(f"Files in {os.getcwd()}: {os.listdir(os.getcwd())}")
    unittest.main(verbosity=2)
