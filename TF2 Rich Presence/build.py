import datetime
import json
import os
import shutil
import subprocess
import sys
import time

import requests

import logger


def main(version_num):
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
        print("Copied", shutil.copy('updater.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('settings.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('map list generator.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('thumb formatter.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('changelog generator.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('Changelogs.html', f'{github_repo_path}\\'))
        print("Copied", shutil.copy('Changelogs_source.html', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy('maps.json', f'{github_repo_path}\\TF2 Rich Presence'))
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
        print("Copied", shutil.copy('README-source.MD', github_repo_path))
        print("Copied", shutil.copy('.travis.yml', github_repo_path))

        # copies test resources
        test_resources_source = os.path.abspath('test_resources')
        test_resources_target = os.path.abspath(f'{github_repo_path}\\TF2 Rich Presence\\test_resources')
        shutil.rmtree(test_resources_target)
        print(f"Copying from {test_resources_source} to {test_resources_target}: ", end='')
        subprocess.run(f'xcopy \"{test_resources_source}\" \"{test_resources_target}\\\" /E /Q')

        # copies build tools
        build_tools_source = os.path.abspath('build_tools')
        build_tools_target = os.path.abspath(f'{github_repo_path}\\TF2 Rich Presence\\build_tools')
        shutil.rmtree(build_tools_target)
        print(f"Copying from {build_tools_source} to {build_tools_target}: ", end='')
        subprocess.run(f'xcopy \"{build_tools_source}\" \"{build_tools_target}\\\" /E /Q')

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
                os.remove(file)
                print(f"Removed old package: {file}")

    # creates folders again
    time.sleep(0.25)  # because windows is slow sometimes
    new_build_folder_name = f'TF2 Rich Presence {version_num}'
    os.mkdir(new_build_folder_name)
    os.mkdir(f'{new_build_folder_name}\\resources')
    os.mkdir(f'{new_build_folder_name}\\logs')
    print(f"Created new build folder: {new_build_folder_name}")

    files_to_copy = [('maps.json', f'{new_build_folder_name}\\resources\\'),
                     ('custom_maps.json', f'{new_build_folder_name}\\resources\\'),
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
                     ('settings.py', f'{new_build_folder_name}\\resources\\'),
                     ('tf2_logo_blurple.ico', f'{new_build_folder_name}\\resources\\'),
                     ('tf2_logo_blurple_wrench.ico', f'{new_build_folder_name}\\resources\\'),
                     ('APIs', f'{new_build_folder_name}\\resources\\'),
                     ('Changelogs.html', f'{new_build_folder_name}\\')]

    # copies files, adding any version numbers
    for file_dest_pair in files_to_copy:
        try:
            with open(file_dest_pair[0], 'r') as file_source:
                with open(f'{file_dest_pair[1]}{file_dest_pair[0]}', 'w') as file_target:
                    modified_file = file_source.read().replace('{tf2rpvnum}', version_num)

                    if file_dest_pair[0] == 'main.py':
                        modified_file = modified_file.replace('log.cleanup(20)', 'log.cleanup(5)')
                        modified_file = modified_file.replace('to_stderr = True', 'to_stderr = False')
                    if file_dest_pair[0] == 'launcher.py':
                        modified_file = modified_file.replace('sentry_enabled: bool = False', 'sentry_enabled: bool = True')
                    if file_dest_pair[0] == 'logger.py':
                        modified_file = modified_file.replace('to_stderr: bool = True', 'to_stderr: bool = False')

                    file_target.write(modified_file)
                    print(f"Copied (and possibly modified) {file_dest_pair[0]}")
        except UnicodeDecodeError:
            print("Copied", shutil.copy(*file_dest_pair))

    # creates build_info.txt
    try:
        commits_info = json.loads(requests.get('https://api.github.com/repos/Kataiser/tf2-rich-presence/commits', timeout=5).text)
        latest_commit_message = commits_info[0]['commit']['message'].split('\n')[0]
        latest_commit = f"\"{latest_commit_message}\" @ {commits_info[0]['html_url']}"
    except Exception as error:
        latest_commit = f"Couldn't get latest commit: {error}"
    with open(f'{new_build_folder_name}\\resources\\build_info.txt', 'w') as info_file:
        version_hashes = {'v1.7.4': 'a56ec211'}
        this_hash = logger.generate_hash()

        info_file.write(f"TF2 Rich Presence by Kataiser"
                        "\nhttps://github.com/Kataiser/tf2-rich-presence"
                        f"\n\nVersion: {version_num}"
                        f"\nBuilt: {datetime.datetime.utcnow().strftime('%c')} UTC"
                        f"\nHash: {this_hash}"
                        f"\nVersion hashes: {version_hashes}"
                        f"\nLatest commit: {latest_commit}")

    # clears custom map cache
    with open(f'{new_build_folder_name}\\resources\\custom_maps.json', 'w') as maps_db:
        json.dump({}, maps_db, indent=4)

    # copies the python interpreter
    python_source = os.path.abspath('python-3.7.1-embed-win32')
    python_target = os.path.abspath(f'{new_build_folder_name}\\resources\\python')
    print(f"Copying from {python_source} to {python_target}: ", end='')
    subprocess.run(f'xcopy \"{python_source}\" \"{python_target}\\\" /E /Q')

    print('Deleting unnecessary files from python...')
    pycaches_deleted = 0
    tests_deleted = 0

    # looks at every file and folder in python
    for root, dirs, files in os.walk(f'{new_build_folder_name}\\resources\\python'):
        # deletes cache files (will get regenerated anyway)
        if '__pycache__' in root:
            shutil.rmtree(root)
            pycaches_deleted += 1

        # deletes tests (not used during runtime hopefully)
        if 'test' in root:
            shutil.rmtree(root)
            tests_deleted += 1

    print(f"pycaches deleted: {pycaches_deleted}")
    print(f"tests deleted: {tests_deleted}")

    time.sleep(0.2)  # just to make sure everything is updated
    convert_bat_to_exe(os.path.abspath(f'{new_build_folder_name}\\Launch TF2 with Rich Presence.bat'), version_num, 'tf2_logo_blurple.ico')
    convert_bat_to_exe(os.path.abspath(f'{new_build_folder_name}\\Launch Rich Presence alongside TF2.bat'), version_num, 'tf2_logo_blurple.ico')
    convert_bat_to_exe(os.path.abspath(f'{new_build_folder_name}\\Change settings.bat'), version_num, 'tf2_logo_blurple_wrench.ico')

    # generates zip package and an "installer" (a self extracting .7z as an exe), both with 7zip
    exe_path = f'tf2_rich_presence_{version_num}_self_extracting.exe'
    zip_path = f'tf2_rich_presence_{version_num}.zip'
    package7zip_command_exe_1 = f'build_tools\\7za.exe a {exe_path} "{new_build_folder_name}\\"'
    package7zip_command_exe_2 = f'-sfx7z.sfx -ssw -mx=9 -myx=9 -mmt=2 -m0=LZMA2:d=8m'
    package7zip_command_zip = f'build_tools\\7za.exe a {zip_path} "{new_build_folder_name}\\" -ssw -mx=9 -m0=LZMA:d=8m -mmt=2'
    print(f"Creating tf2_rich_presence_{version_num}_self_extracting.exe...")
    subprocess.run(f'{package7zip_command_exe_1} {package7zip_command_exe_2}', stdout=subprocess.DEVNULL)
    print(f"Creating tf2_rich_presence_{version_num}.zip...")
    subprocess.run(package7zip_command_zip, stdout=subprocess.DEVNULL)

    # creates README.md from README-source.md
    exe_size_mb = round(os.stat(exe_path).st_size / 1048576, 1)  # 1048576 is 1024^2
    zip_size_mb = round(os.stat(zip_path).st_size / 1048576, 1)
    with open('README-source.md', 'r') as readme_md_source:
        modified_readme_md = readme_md_source.read().replace('{tf2rpvnum}', version_num).replace('{installer_size}', str(exe_size_mb)).replace('{zip_size}', str(zip_size_mb))
    with open('README.md', 'w') as readme_md_target:
        readme_md_target.write(modified_readme_md)
    print("Created README.md from modified README-source.md")
    if github_repo_path != 'n':
        print("Copied", shutil.copy('README.MD', github_repo_path))

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
    print(f"\nFinished building TF2 Rich Presence {version_num} (took {int(time.perf_counter() - build_start_time)} seconds{time_since_last_build_text})")
    if '@' not in latest_commit:
        time.sleep(0.1)
        print(latest_commit, file=sys.stderr)
    if version_num not in version_hashes.keys():
        time.sleep(0.1)
        print(f"version_hashes doesn't include this version, add ('{version_num}': '{this_hash}')", file=sys.stderr)


# converts a batch file to an exe with Bat To Exe Converter (http://www.f2ko.de/en/b2e.php)
def convert_bat_to_exe(batch_location: str, vnum: str, icon_path: str):
    exe_location = batch_location.replace('.bat', '.exe')
    icon_location = os.path.abspath(icon_path)
    version_num_windows = vnum[1:].replace('.', ',') + ',0' * (3 - vnum.count('.'))
    bat2exe_command_1 = f'build_tools\\Bat_To_Exe_Converter.exe -bat "{batch_location}" -save "{exe_location}" -icon "{icon_location}" -x64 -fileversion "{version_num_windows}"'
    bat2exe_command_2 = f'-productversion "{version_num_windows}" -company "Kataiser" -productname "TF2 Rich Presence" -description "Discord Rich Presence for Team Fortress 2"'
    print(f"Creating {exe_location}...")
    subprocess.run(f'{bat2exe_command_1} {bat2exe_command_2}')
    os.remove(batch_location)
    print(f"Deleted {batch_location}")


if __name__ == '__main__':
    main('v1.7.5')
