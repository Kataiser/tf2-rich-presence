import hashlib
import os
import socket
import subprocess
import sys
import time
import traceback
from operator import itemgetter
from typing import Union, List, BinaryIO

from pbwrap import Pastebin

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
        self.start_time: float = time.perf_counter()
        self.filename: Union[bytes, str] = os.path.join('logs', f'{user_pc_name}_{user_identifier}_{"{tf2rpvnum}"}_{generate_hash()}.log')
        self.console_log_path: Union[str, None] = None
        self.to_stderr: bool = False
        self.sentry_level: str = settings.get('sentry_level')
        self.enabled: bool = settings.get('log_level') != 'Off'
        self.log_levels: list = ['Debug', 'Info', 'Error', 'Critical', 'Off']
        self.log_level: str = settings.get('log_level')
        self.unsaved_lines = 0

        if self.enabled:
            self.log_levels_allowed = [level for level in self.log_levels if self.log_levels.index(level) >= self.log_levels.index(self.log_level)]
            self.log_file = open(self.filename, 'a')
        else:
            self.log_levels_allowed = self.log_levels

        for old_filename in os.listdir('logs'):
            old_filename = os.path.join('logs', old_filename)

            if old_filename != self.filename and 'gzip' not in old_filename:
                if self.enabled:
                    self.log_file.close()
                    self.log_file = open(self.filename, 'a')

    # adds a line to the current log file
    def write_log(self, level: str, message_out: str):
        if self.enabled:
            current_time: str = str(time.strftime('%c'))
            time_since_start: str = format(time.perf_counter() - self.start_time, '.4f')  # the format() adds trailing zeroes

            full_line: str = f"[{current_time} +{time_since_start}] {level}: {message_out}\n"

            try:
                self.log_file.write(full_line)
            except UnicodeEncodeError as error:
                self.error(f"Couldn't write log due to UnicodeEncodeError: {error}")

            self.unsaved_lines += 1
            if (self.unsaved_lines >= 100 or level in ['Error', 'Critical']) and (message_out != "Closing and re-opening log" and "Compact" not in message_out):
                try:
                    self.debug(compact_file(self.filename))
                    self.debug("Closing and re-opening log")
                except Exception:
                    pass

                self.save_log()

            if self.to_stderr:
                print(full_line.rstrip('\n'), file=sys.stderr)

    # a log with a level of INFO (rarely used)
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

        if self.sentry_level == 'Error':
            self.report_log(f'Reporting non-critical ERROR: {message_in}')

    # a log with a level of CRITICAL (uncaught, fatal errors, probably sent to Sentry)
    def critical(self, message_in):
        if 'Critical' in self.log_levels_allowed:
            self.write_log('CRITICAL', message_in)

    # write unsaved log lines to file
    def save_log(self):
        self.log_file.close()
        self.log_file = open(self.filename, 'a')
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

    # uses raven (https://github.com/getsentry/raven-python) to report the current log and hopefully some of the current console.log to Sentry (https://sentry.io/)
    def report_log(self, tb: str):
        if self.sentry_level != 'Never' and launcher.sentry_enabled:
            self.info(f"Reporting {self.filename} ({os.stat(self.filename).st_size} bytes) to Sentry")

            if not self.console_log_path:
                paste_text = f"{self.filename}\n{read_truncated_file(self.filename)}"
            else:
                paste_text = f"{self.filename}\n{read_truncated_file(self.filename)}\n{read_truncated_file(self.console_log_path)}"

            paste_url: str = self.pastebin(paste_text)

            try:
                launcher.sentry_client.captureMessage(f'{self.filename}\n{paste_url}\n{tb}')
            except Exception as err:
                self.error(f"Couldn't report crash to Sentry: {err}")

    # sends log contents (or any other text) to pastebin and returns the paste's URL
    def pastebin(self, text: str) -> str:
        self.save_log()

        try:
            pb: Pastebin = Pastebin(launcher.get_api_key('pastebin'))
            return pb.create_paste(text, api_paste_private=1, api_paste_name=self.filename, api_paste_expire_date='1M')
        except Exception as err:
            self.error(f"Couldn't create paste: {err}")
            return f"Couldn't create paste: {err}"


# reads a text file, truncating it to the last 'limit' bytes (default: 200KB) if it's over that size
def read_truncated_file(path: str, limit: int = 200000) -> str:
    with open(path, 'r', errors='replace') as file_to_truncate:
        file_size: int = os.stat(path).st_size
        if file_size > int(limit * 1.1):
            file_to_truncate.seek(file_size - limit)

        trunc_message = f'TRUNCATED "{path}" TO LAST {limit} BYTES'
        return f'{trunc_message}\n{file_to_truncate.read()}\n{trunc_message}'


# generates a short hash string from several source files
def generate_hash() -> str:
    files_to_hash: List[str] = ['main.py', 'configs.py', 'custom_maps.py', 'logger.py', 'updater.py', 'launcher.py', 'settings.py']
    files_to_hash_text: List = []

    build_folder = [item for item in os.listdir('.') if item.startswith('TF2 Rich Presence v') and os.path.isdir(item)]

    for file_to_hash in files_to_hash:
        if build_folder:
            file_to_hash = f'{build_folder[0]}\\resources\\{file_to_hash}'

        try:
            file: BinaryIO = open(os.path.join('resources', file_to_hash), 'rb')
        except FileNotFoundError:
            file: BinaryIO = open(file_to_hash, 'rb')

        files_to_hash_text.append(file.read())
        file.close()

    hasher = hashlib.md5()
    hasher.update(b'\n'.join(files_to_hash_text))
    main_hash: str = hasher.hexdigest()
    return main_hash[:8]


# runs Windows' "compact" command on a file.
def compact_file(target_file_path: str) -> str:
    before_compact_time = time.perf_counter()
    compact_out: str = subprocess.run(f'compact /c /f /i "{target_file_path}"', stdout=subprocess.PIPE).stdout.decode('utf-8')
    return "Compacted file {} (took {} seconds): {}".format(target_file_path, round(time.perf_counter() - before_compact_time, 4), " ".join(compact_out.split()))


if __name__ == '__main__':
    log = Log()
    # log.debug(f"Current log: {log.filename}")
    print(log.pastebin('test'))

