# Copyright (C) 2018-2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import datetime
import getpass
import gzip
import os
import socket
import sys
import time
import traceback
import zlib
from operator import itemgetter
from typing import Dict, List, Optional, TextIO, Tuple, Union

import sentry_sdk

import launcher
import settings
import utils


# TODO: replace this whole thing with a real logger
class Log:
    def __init__(self, path: Optional[str] = None):
        if not os.path.isdir('logs'):
            os.mkdir('logs')
            time.sleep(0.1)  # ensure it gets created
            created_logs_dir: bool = True
        else:
            created_logs_dir = False

        # find user's pc and account name
        user_pc_name: str = socket.gethostname()
        try:
            user_identifier: str = getpass.getuser()
        except ModuleNotFoundError:
            user_identifier = user_pc_name

        if path:
            self.filename: str = path
        else:
            existing_logs: List[str] = sorted(os.listdir('logs'))
            log_index: int = 0

            while True:
                filename: str = f'TF2RP_{user_pc_name}_{user_identifier}_{launcher.VERSION}_{log_index}.log'
                log_index += 1

                if filename not in existing_logs and f'{filename}.gz' not in existing_logs:
                    break

            self.filename = os.path.join('logs', filename)

        # setup
        self.filename_errors: str = os.path.join('logs', f'TF2RP_{user_pc_name}_{user_identifier}_{launcher.VERSION}.errors.log')
        self.last_log_time: float = time.perf_counter()
        self.console_log_path: Optional[str] = None
        self.to_stderr: bool = launcher.DEBUG
        self.force_disabled: bool = False
        self.log_levels: List[str] = ['Debug', 'Info', 'Error', 'Critical', 'Off']
        self.local_error_hashes: List[int] = []  # just in case DB.json breaks

        if self.enabled():
            self.log_file: TextIO = open(self.filename, 'a', encoding='UTF8')

            if created_logs_dir:
                self.debug("Created logs folder")

        db_path: str = 'DB.json' if launcher.DEBUG else os.path.join('resources', 'DB.json')
        if not os.access(db_path, os.W_OK):
            self.error("DB.json can't be written to. This could cause crashes")

        self.debug(f"Created {repr(self)}")

    def __repr__(self) -> str:
        return f"logger.Log at {self.filename} (enabled={bool(self)}, level={settings.get('log_level')}, stderr={self.to_stderr})"

    # this should be run whenever the program closes
    def __del__(self):
        if not self.log_file.closed:
            self.debug(f"Closing log file ({self.filename}) via destructor")
            self.log_file.close()

    def enabled(self) -> bool:
        return settings.get('log_level') != 'Off' and not self.force_disabled

    # list of log levels that are higher priority than the log_level setting
    def log_levels_allowed(self) -> List[str]:
        return [level for level in self.log_levels if self.log_levels.index(level) >= self.log_levels.index(settings.get('log_level'))]

    # adds a line to the current log file
    def write_log(self, level: str, message_out: str, use_errors_file: bool = False):
        if self.enabled():
            if self.last_log_time:
                time_since_last: str = f'+{format(time.perf_counter() - self.last_log_time, ".4f")}'  # the format() adds trailing zeroes
            else:
                time_since_last = '+0.0000'

            full_line: str = f"[{datetime.datetime.now().strftime('%c')[4:-5]} {time_since_last}] {level}: {message_out}\n"

            if settings.get('sentry_level') != "Never":
                # log breadcrumb to Sentry
                sentry_sdk.add_breadcrumb(message=full_line[-512:], level=level.lower().replace('critical', 'fatal'))

            try:
                self.log_file.write(full_line)
                self.log_file.flush()

                if use_errors_file and not launcher.DEBUG:
                    with open(self.filename_errors, 'a', encoding='UTF8') as errors_log:
                        errors_log.write(full_line)
            except UnicodeEncodeError as error:
                self.error(f"Couldn't write log due to UnicodeEncodeError: {error}")
            except PermissionError as error:
                self.error(f"Couldn't write log due to PermissionError: {error}")
            except OSError as error:
                if str(error) == 'No space left on device':
                    # not my problem
                    pass
                else:
                    raise

            if self.to_stderr:
                print(full_line[:-1], file=sys.stderr)

            self.last_log_time = time.perf_counter()

    # a log with a level of INFO (not commonly used)
    def info(self, message_in: str):
        if 'Info' in self.log_levels_allowed():
            self.write_log('INFO', message_in)

    # a log with a level of DEBUG (most things)
    def debug(self, message_in: str):
        if 'Debug' in self.log_levels_allowed():
            self.write_log('DEBUG', message_in)

    # a log with a level of ERROR (caught, non-fatal errors)
    def error(self, message_in: str, reportable: bool = True):
        if 'Error' in self.log_levels_allowed():
            self.write_log('ERROR', message_in, use_errors_file=reportable)

        if reportable and settings.get('sentry_level') == 'All errors':
            db: Dict[str, Union[bool, list, str]] = utils.access_db()
            message_hash: int = zlib.adler32(message_in.encode('UTF8'))

            if message_hash not in db['error_hashes'] and message_hash not in self.local_error_hashes:
                self.local_error_hashes.append(message_hash)
                sentry_sdk.capture_message(message_in[-512:])
                db['error_hashes'].append(message_hash)
                utils.access_db(write=db)
            else:
                self.debug("Not reporting the error (has already been reported)")

    # a log with a level of CRITICAL (uncaught, fatal errors, probably (hopefully) sent to Sentry)
    def critical(self, message_in: str):
        if 'Critical' in self.log_levels_allowed():
            self.write_log('CRITICAL', message_in, use_errors_file=True)

    # deletes older log files and compresses the rest
    def cleanup(self, max_logs: int):
        all_logs: List[str] = [os.path.join('logs', log) for log in os.listdir('logs') if not log.endswith('.errors.log')]
        all_logs_times: List[Tuple[str, int]] = [(log_filename, os.stat(log_filename).st_mtime_ns) for log_filename in all_logs]
        all_logs_sorted: List[str] = [log_pair[0] for log_pair in sorted(all_logs_times, key=itemgetter(1))]
        overshoot: int = max_logs - len(all_logs_sorted)
        deleted_logs: List[str] = []
        compressed_logs: List[Tuple[str, float, float]] = []

        while overshoot < 0:
            log_to_delete: str = all_logs_sorted.pop(0)
            deleted_logs.append(log_to_delete)

            try:
                os.remove(log_to_delete)
            except Exception:
                self.error(f"Couldn't delete old log file {log_to_delete}: {traceback.format_exc()}")

            overshoot = max_logs - len(all_logs_sorted)

        self.debug(f"Deleted {len(deleted_logs)} log(s): {deleted_logs}")

        for old_log in [log for log in all_logs if not log.endswith('.gz') and os.path.isfile(log) and log != self.filename]:
            with open(old_log, 'rb') as old_log_r:
                data_in: bytes = old_log_r.read()
                data_out: bytes = gzip.compress(data_in)

                with open(f'{old_log}.gz', 'wb') as old_log_w:
                    old_log_w.write(data_out)

            try:
                os.remove(old_log)
            except Exception:
                self.error(f"Couldn't replace log file {old_log}: {traceback.format_exc()}")

            compressed_logs.append((old_log, round(len(data_in) / 1024, 1), round(len(data_out) / 1024, 1)))

        self.debug(f"Compressed {len(compressed_logs)} log(s): {compressed_logs}")


if __name__ == '__main__':
    log = Log()
    log.info(f"Current log: {log.filename}")
