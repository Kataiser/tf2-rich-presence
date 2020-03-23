# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import getpass
import gzip
import os
import socket
import sys
import time
import traceback
from operator import itemgetter
from typing import List, TextIO, Union

import sentry_sdk

import launcher
import settings


# TODO: replace this whole thing with a real logger
class Log:
    def __init__(self, path: str = None):
        # find user's pc and account name
        user_identifier: str = getpass.getuser()
        user_pc_name: str = socket.gethostname()

        if path:
            self.filename: str = path
        else:
            days_since_epoch_local = int((time.time() + time.localtime().tm_gmtoff) / 86400)  # 86400 seconds in a day
            self.filename = os.path.join('logs', f'TF2RP_{user_pc_name}_{user_identifier}_{launcher.VERSION}_{days_since_epoch_local}.log')

        # setup
        self.last_log_time: float = time.perf_counter()
        self.console_log_path: Union[str, None] = None
        self.to_stderr: bool = launcher.DEBUG
        self.sentry_level: str = settings.get('sentry_level')
        self.enabled: bool = settings.get('log_level') != 'Off'
        self.log_levels: list = ['Debug', 'Info', 'Error', 'Critical', 'Off']
        self.log_level: str = settings.get('log_level')
        self.reported_error_hashes: List[int] = []

        # set the user in Sentry, since log filename is no longer sent
        with sentry_sdk.configure_scope() as scope:
            scope.user = {'username': f'{user_pc_name}_{user_identifier}'}

        if self.enabled:
            if not os.path.isdir('logs'):
                os.mkdir('logs')

            self.log_levels_allowed: list = [level for level in self.log_levels if self.log_levels.index(level) >= self.log_levels.index(self.log_level)]
            self.log_file: TextIO = open(self.filename, 'a', encoding='utf-8')
        else:
            self.log_levels_allowed = self.log_levels

        for old_filename in os.listdir('logs'):
            old_filename: str = os.path.join('logs', old_filename)

            if old_filename != self.filename and 'gzip' not in old_filename:
                if self.enabled:
                    self.log_file.close()
                    self.log_file = open(self.filename, 'a', encoding='utf-8')

        db_path: str = os.path.join('resources', 'DB.json') if os.path.isdir('resources') else 'DB.json'
        if not os.access(db_path, os.W_OK):
            self.error("DB.json can't be written to. This could cause crashes")

    def __repr__(self) -> str:
        return f"logger.Log at {self.filename} (enabled={self.enabled} level={self.log_level}, stderr={self.to_stderr})"

    def __del__(self):
        if not self.log_file.closed:
            self.debug("Closing log file via destructor")
            self.log_file.close()

    # adds a line to the current log file
    def write_log(self, level: str, message_out: str):
        if self.enabled:
            current_time: float = time.perf_counter()

            if self.last_log_time:
                time_since_last: str = f'+{format(current_time - self.last_log_time, ".4f")}'  # the format() adds trailing zeroes
            else:
                time_since_last = '+0.0000'

            full_line: str = f"[{int(time.time())} {time_since_last}] {level}: {message_out}\n"

            # log breadcrumb to Sentry
            sentry_sdk.add_breadcrumb(message=full_line, level=level.lower().replace('critical', 'fatal'))

            try:
                self.log_file.write(full_line)
                self.log_file.flush()
            except UnicodeEncodeError as error:
                self.error(f"Couldn't write log due to UnicodeEncodeError: {error}")

            if self.to_stderr:
                print(full_line.rstrip('\n'), file=sys.stderr)

            self.last_log_time = current_time

    # a log with a level of INFO (not commonly used)
    def info(self, message_in: str):
        if 'Info' in self.log_levels_allowed:
            self.write_log('INFO', message_in)

    # a log with a level of DEBUG (most things)
    def debug(self, message_in: str):
        if 'Debug' in self.log_levels_allowed:
            self.write_log('DEBUG', message_in)

    # a log with a level of ERROR (caught, non-fatal errors)
    def error(self, message_in: str, reportable: bool = True):
        if 'Error' in self.log_levels_allowed:
            self.write_log('ERROR', message_in)

        if reportable and self.sentry_level == 'All errors':
            if hash(message_in) not in self.reported_error_hashes:
                sentry_sdk.capture_message(f"Reporting non-critical ERROR: {message_in}")
                self.reported_error_hashes.append(hash(message_in))
            else:
                self.debug("Not reporting the error (has already been reported)")

    # a log with a level of CRITICAL (uncaught, fatal errors, probably sent to Sentry)
    def critical(self, message_in: str):
        if 'Critical' in self.log_levels_allowed:
            self.write_log('CRITICAL', message_in)

    # deletes older log files and compresses the rest
    def cleanup(self, max_logs: int):
        all_logs: list = [os.path.join('logs', log) for log in os.listdir('logs')]
        all_logs_times: list = [(log_filename, os.stat(log_filename).st_mtime_ns) for log_filename in all_logs]
        all_logs_sorted: list = [log_pair[0] for log_pair in sorted(all_logs_times, key=itemgetter(1))]
        overshoot: int = max_logs - len(all_logs_sorted)
        deleted_log: list = []
        compressed_log: list = []

        while overshoot < 0:
            log_to_delete: str = all_logs_sorted.pop(0)
            deleted_log.append(log_to_delete)

            try:
                os.remove(log_to_delete)
            except Exception:
                self.error(f"Couldn't delete log file {log_to_delete}: {traceback.format_exc()}")

            overshoot = max_logs - len(all_logs_sorted)

        self.debug(f"Deleted {len(deleted_log)} log(s): {deleted_log}")

        for old_log in [log for log in all_logs if not log.endswith('.gz') and os.path.isfile(log) and log != self.filename]:
            with open(old_log, 'rb') as old_log_r:
                data_in: bytes = old_log_r.read()
                data_out: bytes = gzip.compress(data_in)

                with open(f'{old_log}.gz', 'wb') as old_log_w:
                    old_log_w.write(data_out)

            os.remove(old_log)
            comp_ratio = round(len(data_out) / len(data_in), 3) if data_in else None  # fixes a ZeroDivisionError
            compressed_log.append((old_log, comp_ratio))

        self.debug(f"Compressed {len(compressed_log)} log(s): {compressed_log}")


if __name__ == '__main__':
    log = Log()
    log.info(f"Current log: {log.filename}")
