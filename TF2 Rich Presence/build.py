# Copyright (C) 2019  Kataiser
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import compileall
import datetime
import json
import os
import shutil
import subprocess
import sys
import time

import requests

import changelog_generator
import logger


def main(version_num=None):
    # get build version info
    with open('build_version.json', 'r') as build_version_json:
        build_version_data = json.load(build_version_json)
    if not version_num:
        version_num = build_version_data['this_version']

    print(f"Building TF2 Rich Presence {version_num}")

    if os.path.exists('last_repo_path.txt'):
        with open('last_repo_path.txt', 'r') as last_repo_path_file:
            last_repo_path = last_repo_path_file.read()

        github_repo_path = input(f"Github repo path ('n' to skip, 'h' to use \"{last_repo_path}\"): ")

        if github_repo_path == 'h':
            github_repo_path = last_repo_path
    else:
        github_repo_path = input("Github repo path ('n' to skip): ")

    if github_repo_path != 'n':
        with open('last_repo_path.txt', 'w') as last_repo_path_file:
            last_repo_path_file.write(github_repo_path)

    build_start_time = time.perf_counter()
    print()

    # copies stuff to the Github repo
    if github_repo_path != 'n':
        print("Copied", shutil.copy('main.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('launcher.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('build.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('tests.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('ci_test_runner.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('logger.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('configs.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('custom_maps.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('processes.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('updater.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('settings.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('localization.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('welcomer.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('detect_system_language.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('map list generator.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('thumb formatter.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('changelog_generator.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('Changelogs_source.html', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('maps.json', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('localization.json', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('DB_default.json', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('APIs', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('main menu.png', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('casual.png', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('comp.png', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('mvm_queued.png', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('preview.png', github_repo_path))
        print("Copied", shutil.copy('Tf2-logo.png', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('unknown_map.png', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('Readme.txt', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('requirements.txt', github_repo_path))
        print("Copied", shutil.copy('tf2_logo_blurple.ico', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('tf2_logo_blurple_wrench.ico', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('Launch TF2 with Rich Presence.bat', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('Launch Rich Presence alongside TF2.bat', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('Change settings.bat', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('README-source.MD', github_repo_path))
        print("Copied", shutil.copy('.travis.yml', github_repo_path))
        print("Copied", shutil.copy('requirements.txt', github_repo_path))
        print("Copied", shutil.copy('python-3.7.4-embed-win32.zip', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copyfile(f'{github_repo_path}\\TF2 Rich Presence\\DB_default.json', f'{github_repo_path}\\TF2 Rich Presence\\DB.json'))

        copy_dir_to_git('test_resources', f'{github_repo_path}\\TF2 Rich Presence\\test_resources')
        copy_dir_to_git('build_tools', f'{github_repo_path}\\TF2 Rich Presence\\build_tools')

    print("Generating Changelogs.html")
    ratelimit_remaining = 100
    try:
        ratelimit_remaining = changelog_generator.main(silent=True)
        print(f"Github requests remaining: {ratelimit_remaining}")
        generated_changelogs = True
    except Exception as error:
        changelog_generation_error = error
        generated_changelogs = False
    if github_repo_path != 'n':
        print("Copied", shutil.copy('Changelogs.html', f'{github_repo_path}\\'))

    # starts from scratch each time
    old_build_folders = [f.path for f in os.scandir('.') if f.is_dir() if f.path.startswith('.\\TF2 Rich Presence ')]
    if old_build_folders:
        for folder in old_build_folders:
            try:
                shutil.rmtree(folder)
            except (OSError, PermissionError):
                time.sleep(0.2)
                shutil.rmtree(folder)  # beautiful

            print(f"Removed old build folder: {folder}")
    else:
        print("No old build folder found")

    files_in_cwd = os.listdir('.')
    last_build_time = None
    for file in files_in_cwd:
        if file.startswith('tf2_rich_presence_'):
            if file.endswith('_self_extracting.exe') or file.endswith('.zip'):
                last_build_time = os.stat(file).st_mtime
                print(f"Found old package: {file}")

    # creates folders again
    time.sleep(0.25)  # because windows is slow sometimes
    new_build_folder_name = f'TF2 Rich Presence {version_num}'
    os.mkdir(new_build_folder_name)
    os.mkdir(f'{new_build_folder_name}\\resources')
    os.mkdir(f'{new_build_folder_name}\\logs')
    print(f"Created new build folder: {new_build_folder_name}")

    missing_files = []
    files_to_copy = [('maps.json', f'{new_build_folder_name}\\resources\\'),
                     ('localization.json', f'{new_build_folder_name}\\resources\\'),
                     ('DB_default.json', f'{new_build_folder_name}\\resources\\'),
                     ('LICENSE', f'{new_build_folder_name}\\resources\\'),
                     ('main.py', f'{new_build_folder_name}\\resources\\'),
                     ('launcher.py', f'{new_build_folder_name}\\resources\\'),
                     ('Readme.txt', f'{new_build_folder_name}\\'),
                     ('Launch TF2 with Rich Presence.bat', f'{new_build_folder_name}\\'),
                     ('Launch Rich Presence alongside TF2.bat', f'{new_build_folder_name}\\'),
                     ('Change settings.bat', f'{new_build_folder_name}\\'),
                     ('logger.py', f'{new_build_folder_name}\\resources\\'),
                     ('updater.py', f'{new_build_folder_name}\\resources\\'),
                     ('configs.py', f'{new_build_folder_name}\\resources\\'),
                     ('custom_maps.py', f'{new_build_folder_name}\\resources\\'),
                     ('processes.py', f'{new_build_folder_name}\\resources\\'),
                     ('settings.py', f'{new_build_folder_name}\\resources\\'),
                     ('localization.py', f'{new_build_folder_name}\\resources\\'),
                     ('welcomer.py', f'{new_build_folder_name}\\resources\\'),
                     ('detect_system_language.py', f'{new_build_folder_name}\\resources\\'),
                     ('tf2_logo_blurple.ico', f'{new_build_folder_name}\\resources\\'),
                     ('tf2_logo_blurple_wrench.ico', f'{new_build_folder_name}\\resources\\'),
                     ('APIs', f'{new_build_folder_name}\\resources\\'),
                     ('Changelogs.html', f'{new_build_folder_name}\\')]

    # copies files, adding any version numbers
    for file_dest_pair in files_to_copy:
        if not os.path.exists(file_dest_pair[0]):
            missing_files.append(file_dest_pair[0])
            continue

        try:
            with open(file_dest_pair[0], 'r', encoding='utf-8') as file_source:
                with open(f'{file_dest_pair[1]}{file_dest_pair[0]}', 'w', encoding='utf-8') as file_target:
                    modified_file = file_source.read().replace('{tf2rpvnum}', version_num)

                    if file_dest_pair[0] == 'main.py':
                        modified_file = modified_file.replace('log.cleanup(20)', 'log.cleanup(5)')
                        modified_file = modified_file.replace('to_stderr = True', 'to_stderr = False')
                    if file_dest_pair[0] == 'launcher.py':
                        modified_file = modified_file.replace('sentry_enabled: bool = False', 'sentry_enabled: bool = True')
                    if file_dest_pair[0] == 'logger.py':
                        modified_file = modified_file.replace('to_stderr: bool = True', 'to_stderr: bool = False')
                    if file_dest_pair[0] == 'Readme.txt':
                        modified_file = modified_file.replace('{built}', f"{datetime.datetime.utcnow().strftime('%c')} UTC")

                    file_target.write(modified_file)
                    print(f"Copied (and possibly modified) {file_dest_pair[0]}")
        except UnicodeDecodeError:
            print("Copied", shutil.copy(*file_dest_pair))

    os.rename(f'{new_build_folder_name}\\resources\\DB_default.json', f'{new_build_folder_name}\\resources\\DB.json')

    # modify build_version.json, if need be
    this_hash = logger.generate_hash()
    if this_hash not in build_version_data['version_hashes']:
        build_version_data['version_hashes'][version_num] = this_hash
        with open('build_version.json', 'w') as build_version_json_write:
            json.dump(build_version_data, build_version_json_write, indent=4)
    elif build_version_data['version_hashes'][version_num] != this_hash:
        build_version_data['version_hashes'][version_num] = this_hash
        with open('build_version.json', 'w') as build_version_json_write:
            json.dump(build_version_data, build_version_json_write, indent=4)
    if github_repo_path != 'n':
        print("Copied", shutil.copy('build_version.json', f'{github_repo_path}\\TF2 Rich Presence'))

    # creates build_info.txt
    try:
        commits_info = json.loads(requests.get('https://api.github.com/repos/Kataiser/tf2-rich-presence/commits', timeout=5).text)
        latest_commit_message = commits_info[0]['commit']['message'].split('\n')[0]
        latest_commit = f"\"{latest_commit_message}\" @\n\t{commits_info[0]['html_url'][:60]}"
        got_latest_commit = True
    except Exception as error:
        got_latest_commit = False
        get_latest_commit_error = error
        latest_commit = ''
    with open(f'{new_build_folder_name}\\resources\\build_info.txt', 'w') as info_file:
        info_file.write(f"TF2 Rich Presence by Kataiser"
                        "\nhttps://github.com/Kataiser/tf2-rich-presence"
                        f"\n\nVersion: {version_num}"
                        f"\nBuilt: {datetime.datetime.utcnow().strftime('%c')} UTC"
                        f"\nHash: {this_hash}"
                        f"\nVersion hashes: {build_version_data['version_hashes']}"
                        f"\nLatest commit: {latest_commit}")

    # copies the python interpreter
    python_source = os.path.abspath('python-3.7.4-embed-win32')
    python_target = os.path.abspath(f'{new_build_folder_name}\\resources\\python')
    print(f"Copying from {python_source}\n\tto {python_target}: ", end='')
    assert os.path.isdir(python_source) and not os.path.isdir(python_target)
    subprocess.run(f'xcopy \"{python_source}\" \"{python_target}\\\" /E /Q')

    print("Compiling PYCs")
    compileall.compile_dir(f'{new_build_folder_name}\\resources', optimize=2, quiet=True)
    pycs_to_delete = [r'python\packages\certifi\__pycache__\core.cpython-37.pyc', r'python\packages\certifi\__pycache__\__init__.cpython-37.pyc', r'python\packages\certifi\__pycache__\__main__.cpython-37.opt-2.pyc', r'python\packages\certifi\__pycache__\__main__.cpython-37.pyc', r'python\packages\chardet\cli\__pycache__\chardetect.cpython-37.opt-2.pyc', r'python\packages\chardet\cli\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\chardet\__pycache__\langhungarianmodel.cpython-37.opt-2.pyc', r'python\packages\idna\__pycache__\codec.cpython-37.opt-2.pyc', r'python\packages\idna\__pycache__\compat.cpython-37.opt-2.pyc', r'python\packages\idna\__pycache__\uts46data.cpython-37.opt-2.pyc', r'python\packages\psutil\__pycache__\_psaix.cpython-37.opt-2.pyc', r'python\packages\psutil\__pycache__\_psbsd.cpython-37.opt-2.pyc', r'python\packages\psutil\__pycache__\_pslinux.cpython-37.opt-2.pyc', r'python\packages\psutil\__pycache__\_psosx.cpython-37.opt-2.pyc', r'python\packages\psutil\__pycache__\_psposix.cpython-37.opt-2.pyc', r'python\packages\psutil\__pycache__\_pssunos.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\awslambda\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\bottle\__pycache__\utils.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\bottle\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\celery\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\celery\__pycache__\models.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\celery\__pycache__\tasks.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\celery\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\management\commands\__pycache__\raven.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\management\commands\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\management\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\middleware\__pycache__\wsgi.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\middleware\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\raven_compat\management\commands\__pycache__\raven.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\raven_compat\management\commands\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\raven_compat\management\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\raven_compat\middleware\__pycache__\wsgi.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\raven_compat\middleware\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\raven_compat\templatetags\__pycache__\raven.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\raven_compat\templatetags\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\raven_compat\__pycache__\handlers.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\raven_compat\__pycache__\models.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\raven_compat\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\templatetags\__pycache__\raven.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\templatetags\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\__pycache__\apps.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\__pycache__\client.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\__pycache__\handlers.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\__pycache__\logging.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\__pycache__\models.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\__pycache__\resolver.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\__pycache__\serializers.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\__pycache__\urls.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\__pycache__\utils.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\__pycache__\views.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\django\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\pylons\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\tornado\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\webpy\__pycache__\utils.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\webpy\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\zconfig\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\zerorpc\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\zope\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\__pycache__\async.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\__pycache__\flask.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\__pycache__\paste.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\__pycache__\sanic.cpython-37.opt-2.pyc', r'python\packages\raven\contrib\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\handlers\__pycache__\logbook.cpython-37.opt-2.pyc', r'python\packages\raven\handlers\__pycache__\logging.cpython-37.opt-2.pyc', r'python\packages\raven\handlers\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\scripts\__pycache__\runner.cpython-37.opt-2.pyc', r'python\packages\raven\scripts\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\raven\utils\__pycache__\conf.cpython-37.opt-2.pyc', r'python\packages\raven\utils\__pycache__\imports.cpython-37.opt-2.pyc', r'python\packages\raven\utils\__pycache__\testutils.cpython-37.opt-2.pyc', r'python\packages\raven\utils\__pycache__\wsgi.cpython-37.opt-2.pyc', r'python\packages\raven\__pycache__\middleware.cpython-37.opt-2.pyc', r'python\packages\raven\__pycache__\processors.cpython-37.opt-2.pyc', r'python\packages\raven\__pycache__\_compat.cpython-37.opt-2.pyc', r'python\packages\requests\__pycache__\help.cpython-37.opt-2.pyc', r'python\packages\urllib3\contrib\_securetransport\__pycache__\bindings.cpython-37.opt-2.pyc', r'python\packages\urllib3\contrib\_securetransport\__pycache__\bindings.cpython-37.pyc', r'python\packages\urllib3\contrib\_securetransport\__pycache__\low_level.cpython-37.opt-2.pyc', r'python\packages\urllib3\contrib\_securetransport\__pycache__\low_level.cpython-37.pyc', r'python\packages\urllib3\contrib\_securetransport\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\urllib3\contrib\_securetransport\__pycache__\__init__.cpython-37.pyc', r'python\packages\urllib3\contrib\__pycache__\appengine.cpython-37.opt-2.pyc', r'python\packages\urllib3\contrib\__pycache__\appengine.cpython-37.pyc', r'python\packages\urllib3\contrib\__pycache__\ntlmpool.cpython-37.opt-2.pyc', r'python\packages\urllib3\contrib\__pycache__\ntlmpool.cpython-37.pyc', r'python\packages\urllib3\contrib\__pycache__\pyopenssl.cpython-37.pyc', r'python\packages\urllib3\contrib\__pycache__\securetransport.cpython-37.opt-2.pyc', r'python\packages\urllib3\contrib\__pycache__\securetransport.cpython-37.pyc', r'python\packages\urllib3\contrib\__pycache__\socks.cpython-37.pyc', r'python\packages\urllib3\contrib\__pycache__\_appengine_environ.cpython-37.pyc', r'python\packages\urllib3\contrib\__pycache__\__init__.cpython-37.pyc', r'python\packages\urllib3\packages\backports\__pycache__\makefile.cpython-37.opt-2.pyc', r'python\packages\urllib3\packages\backports\__pycache__\makefile.cpython-37.pyc', r'python\packages\urllib3\packages\backports\__pycache__\__init__.cpython-37.opt-2.pyc', r'python\packages\urllib3\packages\backports\__pycache__\__init__.cpython-37.pyc', r'python\packages\urllib3\packages\ssl_match_hostname\__pycache__\_implementation.cpython-37.opt-2.pyc', r'python\packages\urllib3\packages\ssl_match_hostname\__pycache__\_implementation.cpython-37.pyc', r'python\packages\urllib3\packages\ssl_match_hostname\__pycache__\__init__.cpython-37.pyc', r'python\packages\urllib3\packages\__pycache__\six.cpython-37.pyc', r'python\packages\urllib3\packages\__pycache__\__init__.cpython-37.pyc', r'python\packages\urllib3\util\__pycache__\connection.cpython-37.pyc', r'python\packages\urllib3\util\__pycache__\queue.cpython-37.pyc', r'python\packages\urllib3\util\__pycache__\request.cpython-37.pyc', r'python\packages\urllib3\util\__pycache__\response.cpython-37.pyc', r'python\packages\urllib3\util\__pycache__\retry.cpython-37.pyc', r'python\packages\urllib3\util\__pycache__\ssl_.cpython-37.pyc', r'python\packages\urllib3\util\__pycache__\timeout.cpython-37.pyc', r'python\packages\urllib3\util\__pycache__\url.cpython-37.pyc', r'python\packages\urllib3\util\__pycache__\wait.cpython-37.pyc', r'python\packages\urllib3\util\__pycache__\__init__.cpython-37.pyc', r'python\packages\urllib3\__pycache__\connection.cpython-37.pyc', r'python\packages\urllib3\__pycache__\connectionpool.cpython-37.pyc', r'python\packages\urllib3\__pycache__\exceptions.cpython-37.pyc', r'python\packages\urllib3\__pycache__\fields.cpython-37.pyc', r'python\packages\urllib3\__pycache__\filepost.cpython-37.pyc', r'python\packages\urllib3\__pycache__\poolmanager.cpython-37.pyc', r'python\packages\urllib3\__pycache__\request.cpython-37.pyc', r'python\packages\urllib3\__pycache__\response.cpython-37.pyc', r'python\packages\urllib3\__pycache__\_collections.cpython-37.pyc', r'python\packages\urllib3\__pycache__\__init__.cpython-37.pyc', r'python\tkinter\__pycache__\colorchooser.cpython-37.opt-2.pyc', r'python\tkinter\__pycache__\dialog.cpython-37.opt-2.pyc', r'python\tkinter\__pycache__\dnd.cpython-37.opt-2.pyc', r'python\tkinter\__pycache__\filedialog.cpython-37.opt-2.pyc', r'python\tkinter\__pycache__\font.cpython-37.opt-2.pyc', r'python\tkinter\__pycache__\scrolledtext.cpython-37.opt-2.pyc', r'python\tkinter\__pycache__\tix.cpython-37.opt-2.pyc', r'python\tkinter\__pycache__\__main__.cpython-37.opt-2.pyc', r'__pycache__\welcomer.cpython-37.opt-2.pyc']
    print(f"Deleting {len(pycs_to_delete)} unused PYCs")
    missing_pycs = []
    for pyc_to_delete in pycs_to_delete:
        try:
            os.remove(f'{new_build_folder_name}\\resources\\{pyc_to_delete}')
        except FileNotFoundError:
            missing_pycs.append(f'{new_build_folder_name}\\resources\\{pyc_to_delete}')

    time.sleep(0.2)  # just to make sure everything is updated
    convert_bat_to_exe(os.path.abspath(f'{new_build_folder_name}\\Launch TF2 with Rich Presence.bat'), version_num, 'tf2_logo_blurple.ico')
    convert_bat_to_exe(os.path.abspath(f'{new_build_folder_name}\\Launch Rich Presence alongside TF2.bat'), version_num, 'tf2_logo_blurple.ico')
    convert_bat_to_exe(os.path.abspath(f'{new_build_folder_name}\\Change settings.bat'), version_num, 'tf2_logo_blurple_wrench.ico')

    # generates zip package and an "installer" (a self extracting .7z as an exe), both with 7zip
    exe_path = f'tf2_rich_presence_{version_num}_self_extracting.exe'
    zip_path = f'tf2_rich_presence_{version_num}.zip'
    package7zip_command_exe_1 = f'build_tools\\7za.exe u {exe_path} -up1q0r2x1y2z1w2 "{new_build_folder_name}\\"'
    package7zip_command_exe_2 = '-sfx7z.sfx -ssw -mx=9 -myx=9 -mmt=2 -m0=LZMA2:d=8m'
    package7zip_command_zip = f'build_tools\\7za.exe u {zip_path} -up1q0r2x1y2z1w2 "{new_build_folder_name}\\" -ssw -mx=9 -m0=Deflate64 -mmt=2'
    print(f"Creating tf2_rich_presence_{version_num}_self_extracting.exe...")
    assert len(version_num) <= 10 and 'v' in version_num and '.' in version_num
    subprocess.run(f'{package7zip_command_exe_1} {package7zip_command_exe_2}', stdout=subprocess.DEVNULL)
    print(f"Creating tf2_rich_presence_{version_num}.zip...")
    subprocess.run(package7zip_command_zip, stdout=subprocess.DEVNULL)

    # creates README.md from README-source.md
    if os.path.exists('README-source.md'):
        readme_source_exists = True
        with open('README.md', 'r') as old_readme_md:
            old_readme_has_this_version = version_num in old_readme_md.read()
        if old_readme_has_this_version:
            print("Old README.md is not outdated, skipping modifying it")
        else:
            exe_size_mb = round(os.stat(exe_path).st_size / 1048576, 1)  # 1048576 is 1024^2
            zip_size_mb = round(os.stat(zip_path).st_size / 1048576, 1)
            with open('README-source.md', 'r') as readme_md_source:
                modified_readme_md = readme_md_source.read().replace('{tf2rpvnum}', version_num).replace('{installer_size}', str(exe_size_mb)).replace('{zip_size}', str(zip_size_mb))
            with open('README.md', 'w') as readme_md_target:
                readme_md_target.write(modified_readme_md)
            print("Created README.md from modified README-source.md")
            if github_repo_path != 'n':
                print("Copied", shutil.copy('README.MD', github_repo_path))
    else:
        readme_source_exists = False

    # disables Sentry, for testing
    with open(f'{new_build_folder_name}\\resources\\launcher.py', 'r') as launcher_py_read:
        old_data = launcher_py_read.read()
    with open(f'{new_build_folder_name}\\resources\\launcher.py', 'w') as launcher_py_write:
        new_data = old_data.replace('sentry_enabled: bool = True', 'sentry_enabled: bool = False')
        launcher_py_write.write(new_data)
    print("Disabled Sentry in launcher")

    # prepares display of time since last build
    if last_build_time:
        last_build_time = round(time.time() - last_build_time)

        if last_build_time > 86400:
            last_build_time_text = f"{round(last_build_time / 86400, 1)} days"
        elif last_build_time > 3600:
            last_build_time_text = f"{round(last_build_time / 3600, 1)} hours"
        elif last_build_time > 60:
            last_build_time_text = f"{round(last_build_time / 60, 1)} minutes"
        else:
            last_build_time_text = f"{last_build_time} seconds"

        time_since_last_build_text = f", {last_build_time_text} since last finished build"
    else:
        time_since_last_build_text = ""

    # finishing output
    print(f"\n{datetime.datetime.now().strftime('%c')}")
    print(f"Finished building TF2 Rich Presence {version_num} (took {int(time.perf_counter() - build_start_time)} seconds{time_since_last_build_text})")
    time.sleep(0.1)

    # warnings from here on out
    if '@' not in latest_commit:
        print(latest_commit, file=sys.stderr)
    if not generated_changelogs:
        print(f"Couldn't generate Changelogs.html: {changelog_generation_error}", file=sys.stderr)
    if not got_latest_commit:
        print(f"Couldn't get latest commit: {get_latest_commit_error}", file=sys.stderr)
    if ratelimit_remaining <= 10:
        print(f"Github requests remaining for changelog: {ratelimit_remaining}", file=sys.stderr)
    if missing_files:
        print(f"Missing files: {missing_files}", file=sys.stderr)
    if not readme_source_exists:
        print("README-source doesn't exist, didn't build README.md", file=sys.stderr)
    if missing_pycs:
        print(f"PYCs that couldn't be deleted: {missing_pycs}", file=sys.stderr)

    with open('Changelogs.html') as changelogs_html:
        if version_num not in changelogs_html.read():
            print(f"'{version_num}' not in Changelogs.html", file=sys.stderr)


# converts a batch file to an exe with Bat To Exe Converter (https://web.archive.org/web/20190513133413/http://www.f2ko.de/en/b2e.php)
def convert_bat_to_exe(batch_location: str, vnum: str, icon_path: str):
    exe_location = batch_location.replace('.bat', '.exe')
    icon_location = os.path.abspath(icon_path)
    version_num_windows = vnum[1:].replace('.', ',') + ',0' * (3 - vnum.count('.'))
    bat2exe_command_1 = f'build_tools\\Bat_To_Exe_Converter.exe -bat "{batch_location}" -save "{exe_location}" -icon "{icon_location}" -fileversion "{version_num_windows}"'
    bat2exe_command_2 = f'-productversion "{version_num_windows}" -company "Kataiser" -productname "TF2 Rich Presence" -description "Discord Rich Presence for Team Fortress 2"'
    print(f"Creating {exe_location}...")
    assert os.path.isfile(batch_location) and os.path.isfile(icon_path) and os.path.isfile('build_tools\\Bat_To_Exe_Converter.exe')
    subprocess.run(f'{bat2exe_command_1} {bat2exe_command_2}')
    os.remove(batch_location)
    print(f"Deleted {batch_location}")


# copy a directory to the git repo
def copy_dir_to_git(source, target):
    try:
        shutil.rmtree(target)
    except FileNotFoundError:
        pass

    print(f"Copying from {source} to {target}: ", end='')
    subprocess.run(f'xcopy \"{source}\" \"{target}\\\" /E /Q')


if __name__ == '__main__':
    main()
