import hashlib
import os
import socket
import sys
import time
import traceback
from operator import itemgetter
from typing import Union, TextIO, List, BinaryIO

from pbwrap import Pastebin
from raven import Client


def write_log(level, message_out):
    if logging_enabled:
        current_time: str = str(time.strftime('%c'))
        time_since_start: str = format(time.perf_counter() - start_time, '.4f')  # the format() adds trailing zeroes
        log_file: TextIO = open(filename, 'a')
        full_line: str = "[{} +{}] {}: {}\n".format(current_time, time_since_start, level, message_out)
        log_file.write(full_line)
        log_file.close()
        if dev:
            print(full_line.rstrip('\n'), file=sys.stderr)


def info(message_in):
    write_log('INFO', message_in)


def debug(message_in):
    write_log('DEBUG', message_in)


def error(message_in):
    write_log('ERROR', message_in)


def critical(message_in):
    write_log('CRITICAL', message_in)


def cleanup(max_logs: int):  # deletes older logs
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

    debug("Deleted {} log(s): {}".format(len(deleted), deleted))


def current_log():
    debug(f"Current log: '{filename}'")


def report_log(reason: str):
    if not dev:
        info(f"Reporting {filename} ({os.stat(filename).st_size} bytes) to Sentry")

        if not console_log_path:
            paste_text = f"{filename}\n{read_truncated_file(filename)}"
        else:
            paste_text = f"{filename}\n{read_truncated_file(filename)}\n{read_truncated_file(console_log_path)}"

        paste_url: str = pastebin(paste_text)
        client.captureMessage(f'{reason}\n{filename}\n{paste_url}')


def read_truncated_file(path: str, limit: int = 400000) -> str:
    with open(path, 'r', errors='replace') as file_to_truncate:
        file_size: int = os.stat(path).st_size
        if file_size > int(limit * 1.1):
            file_to_truncate.seek(file_size - limit)
        return file_to_truncate.read()


def pastebin(text: str) -> str:
    pb: Pastebin = Pastebin('909483860965ed941bff77e61c962ac2')
    return pb.create_paste(text, api_paste_private=1, api_paste_name=filename, api_paste_expire_date='1M')


files_to_hash: List[str] = ['main.py', 'configs.py', 'custom_maps.py', 'logger.py', 'updater.py']
files_to_hash_text: List = []

for file_to_hash in files_to_hash:
    try:
        file: BinaryIO = open(os.path.join('resources', file_to_hash), 'rb')
    except FileNotFoundError:
        file: BinaryIO = open(file_to_hash, 'rb')

    files_to_hash_text.append(file.read())

hasher = hashlib.md5()
hasher.update(b'\n'.join(files_to_hash_text))
main_hash: str = hasher.hexdigest()

user_identifier: str = os.getlogin()
if socket.gethostname().find('.') >= 0:
    user_pc_name: str = socket.gethostname()
else:
    user_pc_name: str = socket.gethostbyaddr(socket.gethostname())[0]

start_time: float = time.perf_counter()
filename: Union[bytes, str] = os.path.join('logs', '{}_{}_{}_{}.log'.format(user_pc_name, user_identifier, '{tf2rpvnum}', main_hash[:8]))
dev: bool = True
console_log_path: Union[str, None] = None
logging_enabled = True

# sentry.io, for error reporting
client: Client = Client(dsn='https://de781ce2454f458eafab1992630bc100:ce637f5993b14663a0840cd9f98a714a@sentry.io/1245944',
                        release='{tf2rpvnum}',
                        string_max_length=512,
                        processors=('raven.processors.SanitizePasswordsProcessor',))

try:
    open(filename, 'x')
except FileExistsError:
    pass
