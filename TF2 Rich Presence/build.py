# Copyright (C) 2018-2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import argparse
import compileall
import datetime
import getpass
import json
import os
import shutil
import site
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import requests

import changelog_generator
import cython_compile


# TODO: don't do this separate locations nonsense, convert to using a repo properly
def main(version_num='v2.1'):
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', action='store_true', help="Skip copying to an repo location", default=False)
    parser.add_argument('--ide', action='store_true', help="Use IDE-based build.log handling", default=False)
    parser.add_argument('--release', action='store_true', help="Release build, invalidates all caches", default=False)
    parser.add_argument('--nocython', action='store_true', help="Don't compile modules with Cython", default=False)
    parser.add_argument('--noinstall', action='store_true', help="Don't automatically run the installer after finishing", default=False)
    cli_skip_repo = parser.parse_args().n
    ide_build_log_handling = parser.parse_args().ide
    release_build = parser.parse_args().release
    nocython = parser.parse_args().nocython
    noinstall = parser.parse_args().noinstall

    if not ide_build_log_handling:
        if os.path.isfile('build.log'):
            os.remove('build.log')
            time.sleep(0.1)
        sys.stdout = Logger()

    assert len(version_num) <= 10 and 'v' in version_num and '.' in version_num
    print(f"Building TF2 Rich Presence {version_num}{' for release' if release_build else ''}")

    if cli_skip_repo:
        github_repo_path = 'n'
    else:
        if os.path.isfile('last_repo_path.txt'):
            with open('last_repo_path.txt', 'r') as last_repo_path_file:
                last_repo_path = last_repo_path_file.read()

            print(f"Github repo path ('n' to skip, 'h' to use \"{last_repo_path}\"): ")
            github_repo_path = input()

            if github_repo_path == 'h':
                github_repo_path = last_repo_path
        else:
            print("Github repo path ('n' to skip): ")
            github_repo_path = input()

        if github_repo_path != 'n' and os.path.isdir(github_repo_path):
            with open('last_repo_path.txt', 'w') as last_repo_path_file:
                last_repo_path_file.write(github_repo_path)

            assert version_num in open(Path(f'{github_repo_path}/.github/workflows/Tests.CD.yml'), 'r').read()

    interpreter_name = 'python-3.9.4-embed-win32'
    build_start_time = time.perf_counter()
    print()

    # copies stuff to the Github repo
    if github_repo_path != 'n':
        print("Copied", shutil.copy('main.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('gui.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('launcher.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('build.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('cython_compile.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('tests.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('game_state.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('console_log.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('logger.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('configs.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('gamemodes.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('processes.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('updater.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('settings.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('settings_gui.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('localization.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('custom.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('utils.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('server.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('generate_map_pics.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('map list generator.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('format_gamemode_images.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('generate_deleted_pycs.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('webp_converter.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('changelog_generator.py', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('Changelogs_source.html', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('maps.json', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('localization.json', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('main menu.png', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('casual.png', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('comp.png', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('mvm_queued.png', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('preview.png', github_repo_path))
        print("Copied", shutil.copy('gui preview.webp', github_repo_path))
        print("Copied", shutil.copy('Tf2-logo.png', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('unknown_map.png', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('Readme.txt', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('tf2_logo_blurple.ico', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('tf2_logo_blurple_wrench.ico', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('TF2 Rich Presence.bat', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('README-source.MD', github_repo_path))
        print("Copied", shutil.copy('requirements.txt', github_repo_path))
        print("Copied", shutil.copy('pycs_to_delete.txt', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy('TF2RP.iss', Path(f'{github_repo_path}/TF2 Rich Presence')))
        print("Copied", shutil.copy(f'{interpreter_name}.zip', Path(f'{github_repo_path}/TF2 Rich Presence')))

        copy_dir_to_git('gui_images', Path(f'{github_repo_path}/TF2 Rich Presence/gui_images'))
        copy_dir_to_git('test_resources', Path(f'{github_repo_path}/TF2 Rich Presence/test_resources'))

    # clear caches if releasing
    if release_build:
        if os.path.isdir('cython_build'):
            shutil.rmtree('cython_build')
            print("Deleted cython_build")
        if os.path.isfile('README.md'):
            os.remove('README.md')
            print("Deleted README.md")
        if os.path.isfile('Changelogs.html'):
            os.remove('Changelogs.html')
            print("Deleted Changelogs.html")

    # starts from scratch each time
    new_build_folder_name = f'TF2 Rich Presence {version_num}'
    update_changelogs = True
    if os.path.isdir(new_build_folder_name):
        # prep for trying to avoid a pointless API request
        if os.path.isfile(Path(f'{new_build_folder_name}/Changelogs.html')):
            with open(Path(f'{new_build_folder_name}/Changelogs.html'), 'r') as old_changelogs:
                update_changelogs = version_num not in old_changelogs.read()
        try:
            shutil.rmtree(new_build_folder_name)
        except (OSError, PermissionError):
            time.sleep(0.2)
            shutil.rmtree(new_build_folder_name)  # beautiful
        print(f"Deleted old build folder: {new_build_folder_name}")
    else:
        print("No old build folder found")

    if (github_repo_path != 'n' and update_changelogs) or release_build:
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
    else:
        print("No need to update Changelogs.html")
        generated_changelogs = True
        ratelimit_remaining = 100

    last_build_time = None
    for file in os.listdir():
        if file.startswith('tf2_rich_presence_'):
            if file.endswith('_self_extracting.exe') or file.endswith('.zip'):
                last_build_time = os.stat(file).st_mtime
                print(f"Found old package: {file}")

    # creates folders again
    time.sleep(0.25)  # because windows is slow sometimes
    os.mkdir(new_build_folder_name)
    os.mkdir(Path(f'{new_build_folder_name}/resources'))
    os.mkdir(Path(f'{new_build_folder_name}/resources/gui_images'))
    os.mkdir(Path(f'{new_build_folder_name}/logs'))
    print(f"Created new build folder: {new_build_folder_name}")

    missing_files = []
    files_to_copy = [('launcher.py', Path(f'{new_build_folder_name}/resources/')),
                     ('custom.py', Path(f'{new_build_folder_name}/resources/')),
                     ('maps.json', Path(f'{new_build_folder_name}/resources/')),
                     ('localization.json', Path(f'{new_build_folder_name}/resources/')),
                     ('LICENSE', new_build_folder_name),
                     ('Readme.txt', Path(f'{new_build_folder_name}/')),
                     ('TF2 Rich Presence.bat', Path(f'{new_build_folder_name}/')),
                     ('tf2_logo_blurple.ico', Path(f'{new_build_folder_name}/resources/')),
                     ('tf2_logo_blurple_wrench.ico', Path(f'{new_build_folder_name}/resources/')),
                     ('Changelogs.html', Path(f'{new_build_folder_name}/'))]

    # copies files, adding any version numbers
    for file_dest_pair in files_to_copy:
        if not os.path.isfile(file_dest_pair[0]):
            missing_files.append(file_dest_pair[0])
            continue

        try:
            with open(file_dest_pair[0], 'r', encoding='UTF8') as file_source:
                modified_file = file_source.read()
        except UnicodeDecodeError:
            print("Copied", shutil.copy(*file_dest_pair))
        else:
            with open(Path(f'{file_dest_pair[1]}/{file_dest_pair[0]}'), 'w', encoding='UTF8') as file_target:
                modified = False

                if file_dest_pair[0] in ('launcher.py', 'Readme.txt') or file_dest_pair[0].endswith('.bat'):
                    modified_file = modified_file.replace('{tf2rpvnum}', version_num)
                    modified_file = modified_file.replace('{built}', f"{datetime.datetime.now().strftime('%c')} CST")
                    modified = True
                if file_dest_pair[0] == 'launcher.py':
                    modified_file = modified_file.replace('DEBUG = True', 'DEBUG = False')
                    modified = True

                file_target.write(modified_file)
                print(f"Copied{' (and modified)' if modified else ''} {file_dest_pair[0]}")

    os.rename(Path(f'{new_build_folder_name}/LICENSE'), Path(f'{new_build_folder_name}/License.txt'))

    # copy in GUI images
    print(f"Copying GUI images: ", end='')
    gui_images_target = Path(f'{new_build_folder_name}/resources/gui_images/')
    if sys.platform == 'win32':
        subprocess.run(f'xcopy \"gui_images\" \"{gui_images_target}\" /E /Q')
    else:
        raise SyntaxError("Whatever the Linux/MacOS equivalent of xcopy is")

    # build PYDs using Cython and copy them in
    if not nocython:
        compile_command = f'{sys.executable} cython_compile.py build_ext --inplace'
        if ide_build_log_handling:
            subprocess.run(compile_command)
        else:
            print(subprocess.run(compile_command, capture_output=True).stdout.decode('UTF8').replace('\r\n', '\n')[:-1])
        pyds = [Path(f'cython_build/{file}') for file in os.listdir('cython_build') if file.endswith('.pyd')]
        print(f"Compiled {len(pyds)} PYDs")
        for pyd in pyds:
            print("Copied", shutil.copy(pyd, Path(f'{new_build_folder_name}/resources/')))
    else:
        print("Not compiling modules with Cython")
        for module in cython_compile.targets:
            print("Copied", shutil.copy(f'{module}.py', Path(f'{new_build_folder_name}/resources/')))

    # creates build_info.txt
    if github_repo_path != 'n':
        try:
            commits_info = json.loads(requests.get('https://api.github.com/repos/Kataiser/tf2-rich-presence/commits', timeout=5).text)
            latest_commit_message = commits_info[0]['commit']['message'].split('\n')[0]
            latest_commit = f"\"{latest_commit_message}\" @\n\t{commits_info[0]['html_url'][:60]}"
            got_latest_commit = True
        except Exception as error:
            got_latest_commit = False
            get_latest_commit_error = error
            latest_commit = ''
    else:
        got_latest_commit = True
        latest_commit = ''
    git_username = subprocess.run('git config user.name', capture_output=True).stdout.decode('UTF8')[:-1]
    build_info_path = Path(f'{new_build_folder_name}/resources/build_info.txt')
    with open('requirements.txt', 'r') as requirements_file:
        requirements_versions = ', '.join([r.replace('==', ' ').rstrip('\n') for r in requirements_file.readlines()])
    with open(build_info_path, 'w') as build_info_txt:
        build_info_txt.write(f"TF2 Rich Presence by Kataiser"
                             "\nhttps://github.com/Kataiser/tf2-rich-presence"
                             f"\n\nVersion: {version_num}"
                             f"\nBuilt at: {datetime.datetime.now().strftime('%c')} CST"
                             f"\nBuilt by: https://github.com/{git_username}"
                             f"\nLatest commit: {latest_commit}"
                             f"\nRequirements versions: {requirements_versions}")
    print(f"Created {build_info_path}")

    # copies the python interpreter
    python_source = os.path.abspath(interpreter_name)
    python_source_zip = os.path.abspath(f'{interpreter_name}.zip')
    if os.path.isdir(python_source):
        python_target = os.path.abspath(Path(f'{new_build_folder_name}/resources/{interpreter_name}'))
        print(f"Copying from {python_source}\n\tto {python_target}: ", end='')
        assert os.path.isdir(python_source) and not os.path.isdir(python_target)
        if sys.platform == 'win32':
            subprocess.run(f'xcopy \"{python_source}\" \"{python_target}\\\" /E /Q')
        else:
            raise SyntaxError("Whatever the Linux/MacOS equivalent of xcopy is")
    elif os.path.isfile(python_source_zip):
        python_target = os.path.abspath(Path(f'{new_build_folder_name}/resources'))
        print(f"Extracting from {python_source_zip}\n\tto {python_target}")
        with zipfile.ZipFile(python_source_zip, 'r') as interpreter_zip:
            assert interpreter_zip.testzip() is None
            interpreter_zip.extractall(path=python_target)
    else:
        raise SystemError("Python interpreter missing")

    # copies the requirement packages (no longer part of the interpreter folder or zip)
    new_packages_dir = Path(f'{new_build_folder_name}/resources/packages')
    os.mkdir(new_packages_dir)
    venv_packages_dir = site.getsitepackages()[1]
    assert 'site-packages' in venv_packages_dir.lower()
    needed_packages = ['PIL', 'Pillow', 'a2s', 'certifi', 'charset_normalizer', 'idna', 'psutil', 'python-a2s', 'requests', 'requests_futures', 'sentry_sdk', 'urllib3', 'vdf', 'discoIPC']
    for site_package in os.listdir(venv_packages_dir):
        for needed_package in needed_packages:
            if needed_package in site_package and 'requests_cache' not in site_package:
                site_package_path = Path(f'{venv_packages_dir}/{site_package}')
                new_package_dir = Path(f'{new_packages_dir}/{site_package}')
                shutil.copytree(site_package_path, new_package_dir)
                break
    print(f"Copied {len(needed_packages)} packages from {venv_packages_dir} to {new_packages_dir}")
    shutil.rmtree(Path(f'{new_packages_dir}/psutil/tests'))
    print("Deleted psutil tests")

    # compile PYCs, for faster initial load times
    # TODO: if it's not too slow, determine which ones need to be deleted at build time (maybe cache somehow?)
    print("Compiling PYCs")
    compileall.compile_dir(Path(f'{new_build_folder_name}/resources'), quiet=True)
    with open('pycs_to_delete.txt', 'r') as pycs_to_delete_txt:
        pycs_to_delete = [pyc_path.rstrip('\n') for pyc_path in pycs_to_delete_txt.readlines()]
    missing_pycs = []
    for pyc_to_delete in pycs_to_delete:
        if sys.platform != 'win32':
            pyc_to_delete = pyc_to_delete.replace('\\', os.path.sep)
        try:
            os.remove(Path(f'{new_build_folder_name}/resources/{pyc_to_delete}'))
        except FileNotFoundError:
            missing_pycs.append(str(Path(f'{new_build_folder_name}/resources/{pyc_to_delete}')))
    print(f"Deleted {len(pycs_to_delete) - len(missing_pycs)} unused PYCs")

    # ensure everything exists that needs to
    assert os.listdir(Path(f'{new_build_folder_name}/logs')) == []
    assert os.listdir(Path(f'{new_build_folder_name}/resources/__pycache__')) != []
    assert os.listdir(Path(f'{new_build_folder_name}/resources/{interpreter_name}')) != []
    assert len(os.listdir(Path(f'{new_build_folder_name}/resources/packages'))) == 24
    assert len(os.listdir(Path(f'{new_build_folder_name}/resources/gui_images'))) == 13
    assert os.path.isfile(Path(f'{new_build_folder_name}/TF2 Rich Presence.bat'))
    assert os.path.isfile(Path(f'{new_build_folder_name}/Changelogs.html'))
    assert os.path.isfile(Path(f'{new_build_folder_name}/License.txt'))
    assert os.path.isfile(Path(f'{new_build_folder_name}/Readme.txt'))
    assert os.path.isfile(Path(f'{new_build_folder_name}/resources/{interpreter_name}/python.exe'))
    assert os.path.isfile(Path(f'{new_build_folder_name}/resources/tf2_logo_blurple.ico'))
    assert os.path.isfile(Path(f'{new_build_folder_name}/resources/tf2_logo_blurple_wrench.ico'))
    assert os.path.isfile(Path(f'{new_build_folder_name}/resources/custom.py'))
    assert os.path.isfile(Path(f'{new_build_folder_name}/resources/launcher.py'))
    assert os.path.isfile(Path(f'{new_build_folder_name}/resources/build_info.txt'))
    with open(Path(f'{new_build_folder_name}/resources/localization.json'), 'r', encoding='UTF8') as assertjson_loc:
        assert json.load(assertjson_loc) != {}
    with open(Path(f'{new_build_folder_name}/resources/maps.json'), 'r') as assertjson_maps:
        assert json.load(assertjson_maps) != {}
    for file in cython_compile.targets:
        pyd_extension = 'cp39-win_amd64.pyd' if sys.maxsize.bit_length() > 32 else 'cp39-win32.pyd'
        assert os.stat(f'{file}.py').st_mtime < os.stat(Path(f'cython_build/{file}.{pyd_extension}')).st_mtime or nocython
    try:
        assertions_enabled = False
        assert False
    except AssertionError:
        print("Final assertions passed")
        assertions_enabled = True

    # append build.log to build_info.txt
    if not ide_build_log_handling:
        sys.stdout.finish()
    time.sleep(0.1)
    build_log_exists = os.path.isfile('build.log')
    if build_log_exists:
        # just to make sure it's actually up-to-date
        build_log_exists = time.time() - os.stat('build.log').st_mtime < 10
    if build_log_exists:
        print("Appending build.log to build_info.txt")
        with open('build.log', 'r') as build_log_file:
            build_log = build_log_file.read().replace(getpass.getuser(), 'USER')
        with open(build_info_path, 'a') as build_info_txt:
            build_info_txt.write(f"\n\nBuild log{' (IDE handled)' if ide_build_log_handling else ''}:\n{build_log}")

    # compile installer
    installer_name = f'TF2RichPresence_{version_num}_setup.exe'
    if os.path.isfile('TF2RP.iss'):
        print("Compiling installer...")
        time.sleep(0.2)  # just to make sure everything is updated
        assert b"Successful compile" in subprocess.check_output('ISCC.exe TF2RP.iss')
        assert installer_name in os.listdir()
    else:
        print("Skipping compiling installer")

    # creates README.md from README-source.md
    if os.path.isfile('README-source.md'):
        readme_source_exists = True
        if os.path.isfile('README.md'):
            with open('README.md', 'r') as old_readme_md:
                old_readme_has_this_version = version_num in old_readme_md.read()
        else:
            old_readme_has_this_version = False
        if old_readme_has_this_version:
            print("Old README.md is not outdated, skipping modifying it")
        else:
            installer_size_mb = round(os.stat(installer_name).st_size / 1048576, 1)  # 1048576 is 1024^2
            with open('README-source.md', 'r') as readme_md_source:
                modified_readme_md = readme_md_source.read().replace('{tf2rpvnum}', version_num).replace('{installer_size}', str(installer_size_mb))
            with open('README.md', 'w') as readme_md_target:
                readme_md_target.write(modified_readme_md)
            print("Created README.md from modified README-source.md")
            if github_repo_path != 'n':
                print("Copied", shutil.copy('README.MD', github_repo_path))
    else:
        readme_source_exists = False

    # automatically install too, why not
    warn_no_installer_log = False
    if not noinstall:
        print("Running installer...")
        subprocess.run(f"{installer_name} /VERYSILENT /CURRENTUSER /MERGETASKS=\"!desktopicon\" /LOG=\"{os.path.abspath('installer.log')}\"")
        if os.path.isfile('installer.log'):
            with open('installer.log', 'rb') as installer_log:
                assert b'Installation process succeeded.' in installer_log.read()
        else:
            warn_no_installer_log = True

    # HyperBubs
    if os.path.isfile('custom_kataiser.py'):
        shutil.copy('custom_kataiser.py', Path(f'{new_build_folder_name}/resources/custom.py'))
        shutil.copy('custom_kataiser.py', Path(f"{os.getenv('LOCALAPPDATA')}/Programs/TF2 Rich Presence/resources/custom.py"))

    # prepares display of time since last build
    if last_build_time:
        last_build_time = round(time.time() - last_build_time)

        if last_build_time > 86400:
            last_build_time_text = f"{round(last_build_time / 86400)} days"
        elif last_build_time > 3600:
            last_build_time_text = f"{round(last_build_time / 3600)} hours"
        elif last_build_time > 60:
            last_build_time_text = f"{round(last_build_time / 60)} minutes"
        else:
            last_build_time_text = f"{last_build_time} seconds"

        time_since_last_build_text = f", {last_build_time_text} since last finished build"
    else:
        time_since_last_build_text = ""

    # finishing output
    print(f"\n{datetime.datetime.now().strftime('%c')}")
    print(f"Finished building TF2 Rich Presence {version_num}{' for release' if release_build else ''} (took {int(time.perf_counter() - build_start_time)} seconds{time_since_last_build_text})")
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
        print(f"Couldn't delete {len(missing_pycs)}/{len(pycs_to_delete)} PYCs: {missing_pycs}", file=sys.stderr)
    if not build_log_exists:
        print("build.log doesn't exist (or is old), consider setting up your IDE to save the console to a file or just not using --ide", file=sys.stderr)
    if not assertions_enabled:
        print("Assertions are disabled, build is probably fine but please run without -O or -OO)", file=sys.stderr)
    if warn_no_installer_log:
        print("Installer didn't create an installer.log", file=sys.stderr)
    if git_username and git_username != 'Kataiser':
        print(f"Please note that your git username ({git_username}) has been included in {build_info_path}")

    with open('Changelogs.html') as changelogs_html:
        if version_num not in changelogs_html.read():
            print(f"'{version_num}' not in Changelogs.html", file=sys.stderr)


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


# log all prints to a file
class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open('build.log', 'a')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass

    def finish(self):
        self.log.close()
        sys.stdout = sys.__stdout__


if __name__ == '__main__':
    main()
