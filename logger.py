import hashlib
import os
import sys
import time


def write_log(level, message_out):
    current_time = str(time.strftime('%c'))
    time_since_start = format(time.perf_counter() - start_time, '.4f')  # the format() adds trailing zeroes
    log_file = open(filename, 'a')
    full_line = "[{} +{}] {}: {}\n".format(current_time, time_since_start, level, message_out)
    log_file.write(full_line)
    log_file.close()
    if to_stderr:
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
    all_logs = sorted(os.listdir('logs'))
    overshoot = max_logs - len(all_logs)
    deleted = []
    while overshoot < 0:
        log_to_delete = all_logs.pop(0)
        deleted.append(log_to_delete)
        os.remove(os.path.join('logs/', log_to_delete))
        overshoot = max_logs - len(all_logs)
    debug("Deleted {} log(s): {}".format(len(deleted), deleted))


def current_log():
    debug(f"Current log: '{filename}'")


try:
    main_file = open(os.path.join('resources', 'main.py'), 'rb')
except FileNotFoundError:
    main_file = open('main.py', 'rb')
hasher = hashlib.md5()
hasher.update(main_file.read())
main_hash = hasher.hexdigest()

start_time = time.perf_counter()
user_identifier = os.getlogin()
filename = str(os.path.join('logs', '{}-{}-{}.log'.format(user_identifier, '{tf2rpvnum}', main_hash[:8])))
to_stderr = False
enable_debug = True

try:
    open(filename, 'x')
except FileExistsError:
    pass
