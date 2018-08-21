import hashlib
import os
import socket
import sys
import time
import traceback
from operator import itemgetter
from typing import Union, List, BinaryIO

from pbwrap import Pastebin

import launcher


# adds a line to the current log file
def write_log(level: str, message_out: str):
    if enabled:
        current_time: str = str(time.strftime('%c'))
        time_since_start: str = format(time.perf_counter() - start_time, '.4f')  # the format() adds trailing zeroes

        with open(filename, 'a') as log_file:
            full_line: str = f"[{current_time} +{time_since_start}] {level}: {message_out}\n"
            log_file.write(full_line)

            if to_stderr:
                print(full_line.rstrip('\n'), file=sys.stderr)


# a log with a level of INFO (rarely used)
def info(message_in):
    write_log('INFO', message_in)


# a log with a level of DEBUG (most things)
def debug(message_in):
    write_log('DEBUG', message_in)


# a log with a level of ERROR (caught, non-fatal errors)
def error(message_in):
    write_log('ERROR', message_in)


# a log with a level of CRITICAL (uncaught, fatal errors, probably sent to Sentry)
def critical(message_in):
    write_log('CRITICAL', message_in)


# deletes older log files
def cleanup(max_logs: int):
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
            error(f"Couldn't delete log file {log_to_delete}: {traceback.format_exc()}")

        overshoot = max_logs - len(all_logs_sorted)

    debug(f"Deleted {len(deleted)} log(s): {deleted}")


# uses raven (https://github.com/getsentry/raven-python) to report the current log and hopefully some of the current console.log to Sentry (https://sentry.io/)
def report_log(reason: str):
    if sentry_enabled:
        info(f"Reporting {filename} ({os.stat(filename).st_size} bytes) to Sentry")

        if not console_log_path:
            paste_text = f"{filename}\n{read_truncated_file(filename)}"
        else:
            paste_text = f"{filename}\n{read_truncated_file(filename)}\n{read_truncated_file(console_log_path)}"

        paste_url: str = pastebin(paste_text)
        launcher.sentry_client.captureMessage(f'{reason}\n{filename}\n{paste_url}')


# reads a text file, truncating it to the last 'limit' bytes if it's over that size
def read_truncated_file(path: str, limit: int = 400000) -> str:
    with open(path, 'r', errors='replace') as file_to_truncate:
        file_size: int = os.stat(path).st_size
        if file_size > int(limit * 1.1):
            file_to_truncate.seek(file_size - limit)

        trunc_message = f'TRUNCATED "{path}" TO LAST {limit} BYTES'
        return f'{trunc_message}\n{file_to_truncate.read()}\n{trunc_message}'


# sends log contents (or any other text) to pastebin and returns the paste's URL
def pastebin(text: str) -> str:
    pb: Pastebin = Pastebin('909483860965ed941bff77e61c962ac2')
    return pb.create_paste(text, api_paste_private=1, api_paste_name=filename, api_paste_expire_date='1M')


# generates a short hash string from several source files
def generate_hash() -> str:
    files_to_hash: List[str] = ['main.py', 'configs.py', 'custom_maps.py', 'logger.py', 'updater.py', 'launcher.py']
    files_to_hash_text: List = []

    for file_to_hash in files_to_hash:
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


# find user's pc and account name
user_identifier: str = os.getlogin()
if socket.gethostname().find('.') >= 0:
    user_pc_name: str = socket.gethostname()
else:
    user_pc_name: str = socket.gethostbyaddr(socket.gethostname())[0]

# setup
start_time: float = time.perf_counter()
filename: Union[bytes, str] = os.path.join('logs', f'{user_pc_name}_{user_identifier}_{"{tf2rpvnum}"}_{generate_hash()}.log')
console_log_path: Union[str, None] = None
to_stderr: bool = True
enabled: bool = True
sentry_enabled: bool = False


