import os
import unittest

import configs
import custom_maps
import logger as log
import main


class TestTF2RichPresense(unittest.TestCase):
    def setUp(self):
        log.enabled = False
        log.to_stderr = False
        log.sentry_enabled = False

        if not os.path.exists('main.py'):
            os.chdir(os.path.abspath('TF2 Rich Presence'))

        self.console_lines = 10000

    def test_console_log_in_menus(self):
        self.assertEqual(main.interpret_console_log('test_resources\\console_in_menus.log', ['Kataiser'], self.console_lines), ('In menus', 'Not queued'))

    def test_console_queued_casual(self):
        self.assertEqual(main.interpret_console_log('test_resources\\console_queued_casual.log', ['Kataiser'], self.console_lines), ('In menus', 'Queued for Casual'))

    def test_console_badwater(self):
        self.assertEqual(main.interpret_console_log('test_resources\\console_badwater.log', ['Kataiser'], self.console_lines), ('pl_badwater', 'Pyro'))

    def test_console_custom_map(self):
        self.assertEqual(main.interpret_console_log('test_resources\\console_custom_map.log', ['Kataiser'], self.console_lines), ('cp_catwalk_a5c', 'Soldier'))

    def test_steam_config_file(self):
        self.assertEqual(configs.steam_config_file('test_resources\\'), ['Kataiser'])

    def test_find_custom_map_gamemode(self):
        self.assertEqual(custom_maps.find_custom_map_gamemode('cp_catwalk_a5c'), ['control-point', 'Control Point'])
        self.assertEqual(custom_maps.find_custom_map_gamemode('koth_wubwubwub_remix_vip'), ['koth', 'King of the Hill'])
        self.assertEqual(custom_maps.find_custom_map_gamemode('surf_air_arena_v4'), ['surfing', 'Surfing'])

    def test_logger(self):
        log.enabled = True
        log.filename = 'test_resources\\test_log.log'
        log.info("Test.")

        with open(log.filename, 'r') as current_log_file:
            self.assertTrue(current_log_file.read().endswith('] INFO: Test.\n'))

        os.remove(log.filename)
        log.enabled = False

    def test_read_truncated_file(self):
        with open('test_resources\\correct_file_ending.txt', 'r') as correct_file_ending_file:
            correct_file_ending_text = correct_file_ending_file.read()

        self.assertTrue(log.read_truncated_file('test_resources\\console_queued_casual.log', limit=1000) == correct_file_ending_text)


if __name__ == '__main__':
    unittest.main()
