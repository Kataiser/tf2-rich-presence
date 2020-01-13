# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import io
import os
import shutil
import time
import tkinter as tk
import unittest

import requests
from discoIPC import ipc

import configs
import custom_maps
import init
import launcher
import localization
import logger
import main
import processes
import settings
import updater


class TestTF2RichPresense(unittest.TestCase):
    def setUp(self):
        self.old_settings = settings.access_registry()
        if self.old_settings != settings.get_setting_default(return_all=True):
            settings.access_registry(save_dict=settings.get_setting_default(return_all=True))

        self.dir = os.getcwd()
        self.log = logger.Log()
        self.log.enabled = False
        self.log.to_stderr = False
        self.log.sentry_enabled = False
        self.log.log_levels_allowed = self.log.log_levels

    def tearDown(self):
        os.chdir(self.dir)
        del self.log
        settings.access_registry(save_dict=self.old_settings)

    def test_interpret_console_log(self):
        app = main.TF2RichPresense(self.log)
        self.assertEqual(app.interpret_console_log('test_resources\\console_in_menus.log', ['Kataiser'], float('inf'), True), ('In menus', 'Not queued'))
        self.assertEqual(app.interpret_console_log('test_resources\\console_in_menus.log', ['Kataiser'], 4, True), ('In menus', 'Not queued'))
        self.assertEqual(app.interpret_console_log('test_resources\\console_queued_casual.log', ['Kataiser'], float('inf'), True), ('In menus', 'Queued for Casual'))
        self.assertEqual(app.interpret_console_log('test_resources\\console_badwater.log', ['Kataiser'], float('inf'), True), ('pl_badwater', 'Pyro'))
        self.assertEqual(app.interpret_console_log('test_resources\\console_custom_map.log', ['Kataiser'], float('inf'), True), ('cp_catwalk_a5c', 'Soldier'))
        self.assertEqual(app.interpret_console_log('test_resources\\console_empty.log', ['Kataiser'], float('inf'), True), ('', ''))

    def test_steam_config_file(self):
        self.assertEqual(configs.steam_config_file(self.log, 'test_resources\\'), ['Kataiser'])

    def test_find_custom_map_gamemode(self):
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'cp_catwalk_a5c', False, 5)), ('control-point', 'Control Point'))
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'koth_wubwubwub_remix_vip', False, 5)), ('koth', 'King of the Hill'))
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'surf_air_arena_v4', False, 5)), ('surfing', 'Surfing'))
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'ytsb8eitybw', False, 5)), ('unknown_map', 'Unknown gamemode'))

        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'cp_catwalk_a5c', True, 5)), ('control-point', 'Control Point'))
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'koth_wubwubwub_remix_vip', True, 5)), ('koth', 'King of the Hill'))
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'surf_air_arena_v4', True, 5)), ('surfing', 'Surfing'))
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode(self.log, 'ytsb8eitybw', True, 5)), ('unknown_map', 'Unknown gamemode'))

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
        self.log.info("Test 饏Ӟ򒚦R៣񘺏1ࠞͳⴺۋ")
        self.assertEqual(repr(self.log), r'logger.Log at test_resources\test_self.log (enabled=True level=Debug, stderr=False)')
        self.log.log_file.close()

        with open(self.log.filename, 'r', encoding='UTF8') as current_log_file:
            self.assertTrue(' +0.0000] INFO: Test 饏Ӟ򒚦R៣񘺏1ࠞͳⴺۋ\n' in current_log_file.read())

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

    def test_generate_hash(self):
        old_dir = os.getcwd()
        os.chdir(os.path.abspath('test_resources\\hash_targets'))

        self.assertEqual(logger.generate_hash(), 'e3572e41')

        os.chdir(old_dir)

    def test_access_github_api(self):
        newest_version, downloads_url, changelog = updater.access_github_api(10)
        self.assertTrue(newest_version.startswith('v') and '.' in newest_version)
        self.assertTrue(downloads_url.startswith('https://github.com/Kataiser/tf2-rich-presence/releases/tag/v'))
        self.assertTrue(len(changelog) > 0)

        with self.assertRaises(requests.exceptions.Timeout):
            updater.access_github_api(0.01)

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

    def test_get_api_key(self):
        self.assertEqual(len(launcher.get_api_key('discord')), 18)
        self.assertEqual(len(launcher.get_api_key('teamwork')), 32)
        self.assertEqual(len(launcher.get_api_key('pastebin')), 32)
        self.assertEqual(len(launcher.get_api_key('sentry')), 91)

    def test_discoipc(self):
        # this test fails if Discord isn't running
        test_process_scanner = processes.ProcessScanner(self.log)
        if not test_process_scanner.scan()['Discord']['running']:
            self.skipTest("Discord needs to be running")

        activity = {'details': 'In menus',
                    'timestamps': {'start': int(time.time())},
                    'assets': {'small_image': 'tf2_icon_small', 'small_text': 'Team Fortress 2', 'large_image': 'main_menu',
                               'large_text': 'In menus'},
                    'state': ''}

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
        app = main.TF2RichPresense(self.log)

        self.assertEqual(app.generate_delta(time.time() - 1), ' (+1 second)')
        self.assertEqual(app.generate_delta(time.time() - 10), ' (+10 seconds)')
        self.assertEqual(app.generate_delta(time.time() - 100), ' (+1.7 minutes)')
        self.assertEqual(app.generate_delta(time.time() - 1000), ' (+16.7 minutes)')
        self.assertEqual(app.generate_delta(time.time() - 10000), ' (+2.8 hours)')
        self.assertEqual(app.generate_delta(time.time() - 100000), ' (+1.2 days)')

    def test_process_scanning(self):
        process_scanner = processes.ProcessScanner(self.log)

        self.assertEqual(len(process_scanner.scan()), 3)
        p_info = process_scanner.get_info_from_pid(os.getpid(), ('path', 'time'))

        self.assertEqual(p_info['running'], False)
        self.assertTrue('python' in p_info['path'].lower())  # hope your Python installation is sane
        self.assertTrue(isinstance(p_info['time'], int))

    def test_settings_gui(self):
        root = tk.Tk()
        settings_gui = settings.GUI(root, self.log)
        dimensions = settings_gui.window_dimensions

        self.assertGreaterEqual(dimensions[0], 200)
        self.assertGreaterEqual(dimensions[1], 200)

    def test_localization(self):
        all_keys = localization.access_localization_file().keys()
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
                line_localized = localizer.text(line_english)
                self.assertNotEqual(line_localized, "")
                self.assertEqual(line_localized.count('{0}'), line_english.count('{0}'))
                self.assertEqual(line_localized.count('{1}'), line_english.count('{1}'))

                if line_localized == line_english:
                    num_equal_lines += 1

            if language == 'English':
                self.assertEqual(num_equal_lines, num_lines_total)
            else:
                self.assertLess(num_equal_lines, num_lines_total / 2)

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

    def test_init(self):
        init.launch(0)


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
