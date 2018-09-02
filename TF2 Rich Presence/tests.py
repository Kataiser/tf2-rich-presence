import os
import shutil
import unittest

import requests

import configs
import custom_maps
import logger as log
import main
import settings
import updater


class TestTF2RichPresense(unittest.TestCase):
    def setUp(self):
        log.enabled = False
        log.to_stderr = False
        log.sentry_enabled = False
        log.log_levels_allowed = log.log_levels

        self.console_lines = 200000

    def test_get_idle_duration(self):
        idle_duration = main.get_idle_duration()
        self.assertTrue(10.0 > idle_duration >= 0.0)

    def test_console_log_in_menus(self):
        self.assertEqual(main.interpret_console_log('test_resources\\console_in_menus.log', ['Kataiser'], self.console_lines), ('In menus', 'Not queued', ''))

    def test_console_queued_casual(self):
        self.assertEqual(main.interpret_console_log('test_resources\\console_queued_casual.log', ['Kataiser'], self.console_lines), ('In menus', 'Queued for Casual', ''))

    def test_console_badwater(self):
        self.assertEqual(main.interpret_console_log('test_resources\\console_badwater.log', ['Kataiser'], self.console_lines), ('pl_badwater', 'Pyro', ''))

    def test_console_custom_map(self):
        self.assertEqual(main.interpret_console_log('test_resources\\console_custom_map.log', ['Kataiser'], self.console_lines), ('cp_catwalk_a5c', 'Soldier', ''))

    def test_steam_config_file(self):
        self.assertEqual(configs.steam_config_file('test_resources\\'), ['Kataiser'])

    def test_find_custom_map_gamemode(self):
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode('cp_catwalk_a5c', 5)), ('control-point', 'Control Point'))
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode('koth_wubwubwub_remix_vip', 5)), ('koth', 'King of the Hill'))
        self.assertEqual(tuple(custom_maps.find_custom_map_gamemode('surf_air_arena_v4', 5)), ('surfing', 'Surfing'))

    def test_logger(self):
        log.enabled = True
        log.filename = 'test_resources\\test_log.log'

        try:
            os.remove(log.filename)
        except FileNotFoundError:
            pass

        log.info("Test.")
        with open(log.filename, 'r') as current_log_file:
            self.assertTrue(current_log_file.read().endswith('] INFO: Test.\n'))

        os.remove(log.filename)
        log.enabled = False

    def test_log_cleanup(self):
        old_dir = os.getcwd()
        os.chdir(os.path.abspath('test_resources'))

        try:
            shutil.rmtree('logs')
        except FileNotFoundError:
            pass

        shutil.copytree('empty_logs', 'logs')
        log.cleanup(4)
        self.assertEqual(os.listdir('logs'), ['267d4853.log', '46b087ff.log', '898ff621.log', 'da0d028a.log'])
        shutil.rmtree('logs')

        os.chdir(old_dir)

    def test_generate_hash(self):
        old_dir = os.getcwd()
        os.chdir(os.path.abspath('test_resources\\hash_targets'))

        self.assertEqual(log.generate_hash(), 'c9311b6e')

        os.chdir(old_dir)

    def test_read_truncated_file(self):
        with open('test_resources\\correct_file_ending.txt', 'r') as correct_file_ending_file:
            correct_file_ending_text = correct_file_ending_file.read()

        self.assertTrue(log.read_truncated_file('test_resources\\console_queued_casual.log', limit=1000) == correct_file_ending_text)

    def test_access_github_api(self):
        newest_version, downloads_url, changelog = updater.access_github_api(10)
        self.assertTrue(newest_version.startswith('v') and '.' in newest_version)
        self.assertTrue(downloads_url.startswith('https://github.com/Kataiser/tf2-rich-presence/releases/tag/v'))
        self.assertTrue(len(changelog) > 0)

        with self.assertRaises(requests.exceptions.Timeout):
            updater.access_github_api(0.01)

    def test_calculate_wait_time(self):
        afk_times = [0.0, 3.703, 10.783, 32.019, 19.366, 42.835, 3.424, 73.215, 3.578, 113.263, 73.688, 121.583]
        base_times = range(13)
        correct_results = [0, 0, 0.12, 3.3, 1.4, 4.93, 0, 9.48, 0, 15.49, 9.55, 16.74, 1, 1, 1, 4.0, 2.1, 5.63, 1, 10.18, 1, 16.19, 10.25, 17.44, 2, 2, 2, 4.7, 2.8, 6.33, 2, 10.88, 2, 16.89,
                           10.95, 18.14, 3, 3, 3, 5.4, 3.5, 7.03, 3, 11.58, 3, 17.59, 11.65, 18.84, 4, 4, 4, 6.1, 4.2, 7.73, 4, 12.28, 4, 18.29, 12.35, 19.54, 5, 5, 5, 6.8, 5, 8.43, 5, 12.98,
                           5, 18.99, 13.05, 20.24, 6, 6, 6, 7.5, 6, 9.13, 6, 13.68, 6, 19.69, 13.75, 20.94, 7, 7, 7, 8.2, 7, 9.83, 7, 14.38, 7, 20.39, 14.45, 21.64, 8, 8, 8, 8.9, 8, 10.53, 8,
                           15.08, 8, 21.09, 15.15, 22.34, 9, 9, 9, 9.6, 9, 11.23, 9, 15.78, 9, 21.79, 15.85, 23.04, 10, 10, 10, 10.3, 10, 11.93, 10, 16.48, 10, 22.49, 16.55, 23.74, 11, 11, 11,
                           11.0, 11, 12.63, 11, 17.18, 11, 23.19, 17.25, 24.44, 12, 12, 12, 12, 12, 13.33, 12, 17.88, 12, 23.89, 17.95, 25.14]
        results = []

        for base_time in base_times:
            for afk_time in afk_times:
                results.append(main.calculate_wait_time(base_time, afk_time))

        self.assertEqual(results, correct_results)

    def test_settings_check_int(self):
        self.assertTrue(settings.check_int('', 1000))
        self.assertTrue(settings.check_int('1', 1000))
        self.assertTrue(settings.check_int('1000', 1000))
        self.assertTrue(settings.check_int('60', 60))

        self.assertFalse(settings.check_int('1001', 1000))
        self.assertFalse(settings.check_int('61', 60))
        self.assertFalse(settings.check_int('a', 1000))
        self.assertFalse(settings.check_int('abc123qwe098', 1000))

    def test_find_provider_for_ip(self):
        self.assertEqual(main.find_provider_for_ip('104.243.38.50:27026'), 'Wonderland.TF')


if __name__ == '__main__':
    unittest.main()
