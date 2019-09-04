# Copyright (C) 2019  Kataiser
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import hashlib
import os
import random
import socket
import subprocess
import sys
import time
import traceback
from operator import itemgetter
from typing import Union, List, BinaryIO

import raven
from raven import breadcrumbs

import launcher
import settings


class Log:
    def __init__(self):
        # find user's pc and account name
        user_identifier: str = os.getlogin()
        if socket.gethostname().find('.') >= 0:
            user_pc_name: str = socket.gethostname()
        else:
            user_pc_name: str = socket.gethostbyaddr(socket.gethostname())[0]

        # setup
        self.last_log_time = None
        self.filename: Union[bytes, str] = os.path.join('logs', f'{user_pc_name}_{user_identifier}_{"{tf2rpvnum}"}_{generate_hash()}.log')
        self.console_log_path: Union[str, None] = None
        self.to_stderr: bool = False
        self.sentry_level: str = settings.get('sentry_level')
        self.enabled: bool = settings.get('log_level') != 'Off'
        self.log_levels: list = ['Debug', 'Info', 'Error', 'Critical', 'Off']
        self.log_level: str = settings.get('log_level')
        self.unsaved_lines = 0

        if self.enabled:
            if not os.path.isdir('logs'):
                os.mkdir('logs')

            self.log_levels_allowed = [level for level in self.log_levels if self.log_levels.index(level) >= self.log_levels.index(self.log_level)]
            self.log_file = open(self.filename, 'a', encoding='utf-8')
        else:
            self.log_levels_allowed = self.log_levels

        for old_filename in os.listdir('logs'):
            old_filename = os.path.join('logs', old_filename)

            if old_filename != self.filename and 'gzip' not in old_filename:
                if self.enabled:
                    self.log_file.close()
                    self.log_file = open(self.filename, 'a', encoding='utf-8')

    # adds a line to the current log file
    def write_log(self, level: str, message_out: str):
        if self.enabled:
            current_time = time.perf_counter()

            if self.last_log_time:
                time_since_last: str = format(current_time - self.last_log_time, '.4f')  # the format() adds trailing zeroes
            else:
                time_since_last: str = '0.0000'

            full_line: str = f"[{int(time.time())} +{time_since_last}] {level}: {message_out}\n"

            # log breadcrumb to Sentry
            breadcrumbs.record(message=full_line, level=level.lower().replace('critical', 'fatal'))

            try:
                self.log_file.write(full_line)
            except UnicodeEncodeError as error:
                self.error(f"Couldn't write log due to UnicodeEncodeError: {error}")

            self.unsaved_lines += 1
            if (self.unsaved_lines >= 100 or level != 'DEBUG') and "Compact" not in message_out:
                try:
                    compacted_log = compact_file(self.filename)
                    if compacted_log:
                        self.debug(compacted_log)
                except Exception:
                    pass

                self.save_log()

            if self.to_stderr:
                print(full_line.rstrip('\n'), file=sys.stderr)

            self.last_log_time = current_time

    # a log with a level of INFO (not commonly used)
    def info(self, message_in):
        if 'Info' in self.log_levels_allowed:
            self.write_log('INFO', message_in)

    # a log with a level of DEBUG (most things)
    def debug(self, message_in):
        if 'Debug' in self.log_levels_allowed:
            self.write_log('DEBUG', message_in)

    # a log with a level of ERROR (caught, non-fatal errors)
    def error(self, message_in):
        if 'Error' in self.log_levels_allowed:
            self.write_log('ERROR', message_in)

        if self.sentry_level == 'All errors':
            self.report_to_sentry(f"Reporting non-critical ERROR: {message_in}")

    # a log with a level of CRITICAL (uncaught, fatal errors, probably sent to Sentry)
    def critical(self, message_in):
        if 'Critical' in self.log_levels_allowed:
            self.write_log('CRITICAL', message_in)

    # write unsaved log lines to file
    def save_log(self):
        self.log_file.close()
        self.log_file = open(self.filename, 'a', encoding='utf-8')
        self.unsaved_lines = 0

    # deletes older log files
    def cleanup(self, max_logs: int):
        all_logs = os.listdir('logs')
        all_logs_times = [(log_filename, os.stat(os.path.join('logs', log_filename)).st_mtime_ns) for log_filename in all_logs]  # yeah, an ugly one liner, sorry
        all_logs_sorted = [log_pair[0] for log_pair in sorted(all_logs_times, key=itemgetter(1))]
        overshoot: int = max_logs - len(all_logs_sorted)
        deleted: List[str] = []

        while overshoot < 0:
            log_to_delete: str = all_logs_sorted.pop(0)
            deleted.append(log_to_delete)

            try:
                os.remove(os.path.join('logs/', log_to_delete))
            except Exception:
                self.error(f"Couldn't delete log file {log_to_delete}: {traceback.format_exc()}")

            overshoot = max_logs - len(all_logs_sorted)

        self.debug(f"Deleted {len(deleted)} log(s): {deleted}")

    # uses raven (https://github.com/getsentry/raven-python) to report the current exception to Sentry (https://sentry.io/)
    def report_to_sentry(self, tb: str):
        already_reported = launcher.exc_already_reported(tb)

        if self.sentry_level != 'Never' and launcher.sentry_enabled and not already_reported:
            self.info(f"Reporting crash to Sentry from logger")

            try:
                if self.console_log_path:
                    console_log_to_report = read_truncated_file(self.console_log_path, limit=4000)
                else:
                    console_log_to_report = str(None)

                sentry_client = raven.Client(dsn=launcher.get_api_key('sentry'),
                                             release='{tf2rpvnum}',
                                             string_max_length=4100,
                                             processors=('raven.processors.SanitizePasswordsProcessor',))

                sentry_client.captureMessage(f'{self.filename}\n{tb}', level='fatal', extra={'console.log': console_log_to_report})
            except Exception as err:
                self.error(f"Couldn't report crash to Sentry: {err}")
        else:
            self.debug("Not reporting to Sentry, reason(s): {}".format({'sentry_level': self.sentry_level,
                                                                        'sentry_enabled': launcher.sentry_enabled,
                                                                        'already_reported': already_reported}))


# reads a text file, truncating it to the last 'limit' bytes (default: 200KB) if it's over that size
def read_truncated_file(path: str, limit: int = 200000) -> str:
    with open(path, 'r', errors='replace', encoding='utf-8') as file_to_truncate:
        file_size: int = os.stat(path).st_size
        if file_size > int(limit * 1.1):
            file_to_truncate.seek(file_size - limit)

        trunc_message = f'TRUNCATED "{path}" TO LAST {limit} BYTES'
        return f'{trunc_message}\n{file_to_truncate.read()}\n{trunc_message}'


# generates a short hash string from several source files
def generate_hash() -> str:
    files_to_hash: List[str] = ['main.py', 'configs.py', 'custom_maps.py', 'logger.py', 'updater.py', 'launcher.py', 'settings.py', 'detect_system_language.py', 'maps.json',
                                'localization.json', 'APIs']
    files_to_hash_text: List = []
    build_folder = [item for item in os.listdir('.') if item.startswith('TF2 Rich Presence v') and os.path.isdir(item)]

    for file_to_hash in files_to_hash:
        if build_folder:
            file_to_hash = f'{build_folder[0]}\\resources\\{file_to_hash}'

        try:
            file: BinaryIO = open(os.path.join('resources', file_to_hash), 'rb')
        except FileNotFoundError:
            file: BinaryIO = open(file_to_hash, 'rb')

        file_read = file.read()

        if 'launcher' in file_to_hash:
            file_read = file_read.replace(b'sentry_enabled: bool = True', b'').replace(b'sentry_enabled: bool = False', b'')

        files_to_hash_text.append(file_read)
        file.close()

    hasher = hashlib.md5()
    hasher.update(b'\n'.join(files_to_hash_text))
    main_hash: str = hasher.hexdigest()
    return main_hash[:8]


# runs Windows' "compact" command on a file.
def compact_file(target_file_path: str, guarantee: bool = False) -> str:
    if guarantee or random.random() < 0.25:
        before_compact_time = time.perf_counter()
        compact_out: str = subprocess.run(f'compact /c /f /i "{target_file_path}"', stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
        return "Compacted file {} (took {} seconds): {}".format(target_file_path, round(time.perf_counter() - before_compact_time, 4), " ".join(compact_out.split()))
    else:
        return None


if __name__ == '__main__':
    log = Log()
    # log.debug(f"Current log: {log.filename}")
