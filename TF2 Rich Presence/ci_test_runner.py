# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import os
import unittest

if 'TF2 Rich Presence' not in os.getcwd():
    os.chdir('TF2 Rich Presence')
print(os.listdir(os.getcwd()))

import tests

# for https://travis-ci.org/Kataiser/tf2-rich-presence
if __name__ == '__main__':
    f_tests = tests.TestTF2RichPresense
    ci_tests = [f_tests.test_interpret_console_log, f_tests.test_steam_config_file, f_tests.test_find_custom_map_gamemode, f_tests.test_logger, f_tests.test_log_cleanup,
                f_tests.test_generate_hash, f_tests.test_access_github_api, f_tests.test_settings_check_int, f_tests.test_settings_access, f_tests.test_get_api_key, f_tests.test_discoipc,
                f_tests.test_compact_file, f_tests.test_generate_delta, f_tests.test_process_scanning, f_tests.test_settings_gui, f_tests.test_localization, f_tests.test_main_simple]

    for ci_test in ci_tests:
        # this is probably broken in some way
        f_test_runner = tests.TestTF2RichPresense()

        try:
            f_tests.setUp(f_test_runner)
            ci_test(f_test_runner)
            f_tests.tearDown(f_test_runner)
        except unittest.SkipTest as skipped_test:
            print(skipped_test)
            pass
