import hashlib
import os
import socket
import sys
import time
from typing import Union, TextIO, List, BinaryIO

from pbwrap import Pastebin
from raven import Client


def write_log(level, message_out):
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


def cleanup(max_logs):  # deletes older logs
    all_logs: List[str] = sorted(os.listdir('logs'))
    overshoot: int = max_logs - len(all_logs)
    deleted: List[str] = []
    while overshoot < 0:
        log_to_delete: str = all_logs.pop(0)
        deleted.append(log_to_delete)
        os.remove(os.path.join('logs/', log_to_delete))
        overshoot = max_logs - len(all_logs)
    debug("Deleted {} log(s): {}".format(len(deleted), deleted))


def current_log():
    debug(f"Current log: '{filename}'")


def report_log(reason):
    info(f"Reporting {filename} ({os.stat(filename).st_size} bytes) to Sentry")
    if not dev:
        if not console_log_path:
            paste_text = f"{filename}\n{read_truncated_file(filename)}"
        else:
            paste_text = f"{filename}\n{read_truncated_file(filename)}\n{read_truncated_file(console_log_path)}"

        paste_url: str = pastebin(paste_text)
        client.captureMessage(f'{reason}\n{filename}\n{paste_url}')


def read_truncated_file(path):
    file: TextIO
    with open(path, 'r', errors='replace') as file:
        file_size: int = os.stat(path).st_size
        if file_size > 410000:
            file.seek(file_size - 400000)
        return file.read()


def pastebin(text):
    pb: Pastebin = Pastebin('909483860965ed941bff77e61c962ac2')
    return pb.create_paste(text, api_paste_private=1, api_paste_name=filename, api_paste_expire_date='1M')


try:
    main_file: BinaryIO = open(os.path.join('resources', 'main.py'), 'rb')
except FileNotFoundError:
    main_file: BinaryIO = open('main.py', 'rb')
hasher = hashlib.md5()
hasher.update(main_file.read())
main_hash: str = hasher.hexdigest()

start_time: float = time.perf_counter()
user_identifier: str = os.getlogin()
if socket.gethostname().find('.') >= 0:
    user_pc_name: str = socket.gethostname()
else:
    user_pc_name: str = socket.gethostbyaddr(socket.gethostname())[0]
filename: Union[bytes, str] = os.path.join('logs', '{}_{}_{}_{}.log'.format(user_pc_name, user_identifier, '{tf2rpvnum}', main_hash[:8]))
dev: bool = True
console_log_path: Union[str, None] = None

# sentry.io, for error reporting
client: Client = Client(dsn='https://de781ce2454f458eafab1992630bc100:ce637f5993b14663a0840cd9f98a714a@sentry.io/1245944',
                        release='{tf2rpvnum}',
                        string_max_length=512,
                        processors=('raven.processors.SanitizePasswordsProcessor',))

try:
    open(filename, 'x')
except FileExistsError:
    pass
