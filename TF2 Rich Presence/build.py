# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import argparse
import compileall
import datetime
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

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

    parser = argparse.ArgumentParser()
    parser.add_argument('--n', action='store_true', help="Skip copying to an repo location")
    cli_skip_repo = parser.parse_args().n

    if cli_skip_repo:
        github_repo_path = 'n'
    else:
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
        print("Copied", shutil.copy('main.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('launcher.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('build.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('tests.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('ci_test_runner.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('logger.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('configs.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('custom_maps.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('processes.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('updater.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('settings.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('localization.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('welcomer.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('detect_system_language.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('map list generator.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('thumb formatter.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('changelog_generator.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('Changelogs_source.html', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('maps.json', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('localization.json', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('DB_default.json', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('APIs', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('main menu.png', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('casual.png', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('comp.png', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('mvm_queued.png', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('preview.png', github_repo_path))
        print("Copied", shutil.copy('Tf2-logo.png', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('unknown_map.png', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('Readme.txt', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('requirements.txt', github_repo_path))
        print("Copied", shutil.copy('tf2_logo_blurple.ico', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('tf2_logo_blurple_wrench.ico', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('Launch TF2 with Rich Presence.bat', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('Launch Rich Presence alongside TF2.bat', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('Change settings.bat', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('README-source.MD', github_repo_path))
        print("Copied", shutil.copy('requirements.txt', github_repo_path))
        print("Copied", shutil.copy('pycs_to_delete.txt', github_repo_path))
        print("Copied", shutil.copy('python-3.7.5-embed-win32.zip', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copyfile(Path(f'{github_repo_path}/TF2 Rich Presence/DB_default.json'), Path(f'{github_repo_path}/TF2 Rich Presence/DB.json')))

        copy_dir_to_git('test_resources', Path(f'{github_repo_path}/TF2 Rich Presence/test_resources'))
        copy_dir_to_git('build_tools', Path(f'{github_repo_path}/TF2 Rich Presence/build_tools'))

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
        print("Copied", shutil.copy('Changelogs.html', Path(f'{github_repo_path}/')))

    # starts from scratch each time
    old_build_folders = [f.path for f in os.scandir('.') if f.is_dir() and 'TF2 Rich Presence ' in f.path]
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
    os.mkdir(Path(f'{new_build_folder_name}/resources'))
    os.mkdir(Path(f'{new_build_folder_name}/logs'))
    print(f"Created new build folder: {new_build_folder_name}")

    missing_files = []
    files_to_copy = [('maps.json', Path(f'{new_build_folder_name}/resources/')),
                     ('localization.json', Path(f'{new_build_folder_name}/resources/')),
                     ('DB_default.json', Path(f'{new_build_folder_name}/resources/')),
                     ('LICENSE', Path(f'{new_build_folder_name}/resources/')),
                     ('main.py', Path(f'{new_build_folder_name}/resources/')),
                     ('launcher.py', Path(f'{new_build_folder_name}/resources/')),
                     ('Readme.txt', Path(f'{new_build_folder_name}/')),
                     ('Launch TF2 with Rich Presence.bat', Path(f'{new_build_folder_name}/')),
                     ('Launch Rich Presence alongside TF2.bat', Path(f'{new_build_folder_name}/')),
                     ('Change settings.bat', Path(f'{new_build_folder_name}/')),
                     ('logger.py', Path(f'{new_build_folder_name}/resources/')),
                     ('updater.py', Path(f'{new_build_folder_name}/resources/')),
                     ('configs.py', Path(f'{new_build_folder_name}/resources/')),
                     ('custom_maps.py', Path(f'{new_build_folder_name}/resources/')),
                     ('processes.py', Path(f'{new_build_folder_name}/resources/')),
                     ('settings.py', Path(f'{new_build_folder_name}/resources/')),
                     ('localization.py', Path(f'{new_build_folder_name}/resources/')),
                     ('welcomer.py', Path(f'{new_build_folder_name}/resources/')),
                     ('detect_system_language.py', Path(f'{new_build_folder_name}/resources/')),
                     ('tf2_logo_blurple.ico', Path(f'{new_build_folder_name}/resources/')),
                     ('tf2_logo_blurple_wrench.ico', Path(f'{new_build_folder_name}/resources/')),
                     ('APIs', Path(f'{new_build_folder_name}/resources/')),
                     ('Changelogs.html', Path(f'{new_build_folder_name}/'))]

    # copies files, adding any version numbers
    for file_dest_pair in files_to_copy:
        if not os.path.exists(file_dest_pair[0]):
            missing_files.append(file_dest_pair[0])
            continue

        try:
            with open(file_dest_pair[0], 'r', encoding='utf-8') as file_source:
                with open(Path(f'{file_dest_pair[1]}/{file_dest_pair[0]}'), 'w', encoding='utf-8') as file_target:
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

    os.rename(Path(f'{new_build_folder_name}/resources/DB_default.json'), Path(f'{new_build_folder_name}/resources/DB.json'))

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
        print("Copied", shutil.copy('build_version.json', Path(f'{github_repo_path}/TF2 Rich Presence')))

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
    with open(Path(f'{new_build_folder_name}/resources/build_info.txt'), 'w') as info_file:
        info_file.write(f"TF2 Rich Presence by Kataiser"
                        "\nhttps://github.com/Kataiser/tf2-rich-presence"
                        f"\n\nVersion: {version_num}"
                        f"\nBuilt: {datetime.datetime.utcnow().strftime('%c')} UTC"
                        f"\nHash: {this_hash}"
                        f"\nVersion hashes: {build_version_data['version_hashes']}"
                        f"\nLatest commit: {latest_commit}")

    # copies the python interpreter
    python_source = os.path.abspath('python-3.7.5-embed-win32')
    python_target = os.path.abspath(Path(f'{new_build_folder_name}/resources/python'))
    print(f"Copying from {python_source}\n\tto {python_target}: ", end='')
    assert os.path.isdir(python_source) and not os.path.isdir(python_target)
    if sys.platform == 'win32':
        subprocess.run(f'xcopy \"{python_source}\" \"{python_target}\\\" /E /Q')
    else:
        raise SyntaxError("Whatever the Linux/MacOS equivalent of xcopy is")

    print("Compiling PYCs")
    compileall.compile_dir(Path(f'{new_build_folder_name}/resources'), optimize=2, quiet=True)
    with open('pycs_to_delete.txt', 'r') as pycs_to_delete_txt:
        pycs_to_delete = [pyc_path.rstrip('\n') for pyc_path in pycs_to_delete_txt.readlines()]
    print(f"Deleting {len(pycs_to_delete)} unused PYCs")
    missing_pycs = []
    for pyc_to_delete in pycs_to_delete:
        if sys.platform != 'win32':
            pyc_to_delete = pyc_to_delete.replace('\\', os.path.sep)
        try:
            os.remove(Path(f'{new_build_folder_name}/resources/{pyc_to_delete}'))
        except FileNotFoundError:
            missing_pycs.append(str(Path(f'{new_build_folder_name}/resources/{pyc_to_delete}')))

    time.sleep(0.2)  # just to make sure everything is updated
    convert_bat_to_exe(os.path.abspath(Path(f'{new_build_folder_name}/Launch TF2 with Rich Presence.bat')), version_num, 'tf2_logo_blurple.ico')
    convert_bat_to_exe(os.path.abspath(Path(f'{new_build_folder_name}/Launch Rich Presence alongside TF2.bat')), version_num, 'tf2_logo_blurple.ico')
    convert_bat_to_exe(os.path.abspath(Path(f'{new_build_folder_name}/Change settings.bat')), version_num, 'tf2_logo_blurple_wrench.ico')

    # generates zip package and an "installer" (a self extracting .7z as an exe), both with 7zip
    exe_path = f'tf2_rich_presence_{version_num}_self_extracting.exe'
    zip_path = f'tf2_rich_presence_{version_num}.zip'
    package7zip_command_exe_1 = f'build_tools{os.path.sep}7za.exe u {exe_path} -up1q0r2x1y2z1w2 "{new_build_folder_name}{os.path.sep}"'
    package7zip_command_exe_2 = '-sfx7z.sfx -ssw -mx=9 -myx=9 -mmt=2 -m0=LZMA2:d=8m'
    package7zip_command_zip = f'build_tools{os.path.sep}7za.exe u {zip_path} -up1q0r2x1y2z1w2 "{new_build_folder_name}{os.path.sep}" -ssw -mx=9 -m0=Deflate64 -mmt=2'
    print(f"Creating {exe_path}...")
    assert len(version_num) <= 10 and 'v' in version_num and '.' in version_num
    subprocess.run(f'{package7zip_command_exe_1} {package7zip_command_exe_2}', stdout=subprocess.DEVNULL)
    subprocess.run(f'{package7zip_command_exe_1} {package7zip_command_exe_2}', stdout=subprocess.DEVNULL)
    print(f"Creating {zip_path}...")
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
    with open(Path(f'{new_build_folder_name}/resources/launcher.py'), 'r') as launcher_py_read:
        old_data = launcher_py_read.read()
    with open(Path(f'{new_build_folder_name}/resources/launcher.py'), 'w') as launcher_py_write:
        new_data = old_data.replace(f"release='{version_num}'", f"release='{version_num}-dev'")
        launcher_py_write.write(new_data)
    print(f"Set Sentry version to {version_num}-dev")

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
    if ratelimit_remaining <= 15:
        print(f"Github requests remaining for changelog: {ratelimit_remaining} (uses 3 per run)", file=sys.stderr)
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
    bat2exe_command_1 = f'build_tools{os.path.sep}Bat_To_Exe_Converter.exe -bat "{batch_location}" -save "{exe_location}" -icon "{icon_location}" -fileversion "{version_num_windows}"'
    bat2exe_command_2 = f'-productversion "{version_num_windows}" -company "Kataiser" -productname "TF2 Rich Presence" -description "Discord Rich Presence for Team Fortress 2"'
    print(f"Creating {exe_location}...")
    assert os.path.isfile(batch_location) and os.path.isfile(icon_path) and os.path.isfile(Path('build_tools/Bat_To_Exe_Converter.exe'))
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
    if sys.platform == 'win32':
        subprocess.run(f'xcopy \"{source}\" \"{target}{os.path.sep}\" /E /Q')
    else:
        raise SyntaxError("Whatever the Linux/MacOS equivalent of xcopy is")


if __name__ == '__main__':
    main()
