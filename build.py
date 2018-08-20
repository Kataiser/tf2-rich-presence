import json
import os
import shutil
import subprocess
import tempfile
import time


def main(version_num):
    print(f"Building TF2 Rich Presence {version_num}")
    github_repo_path = input("Github repo path ('n' to skip): ")

    if not os.path.exists('main.py'):
        os.chdir(os.path.abspath('TF2 Rich Presence'))

    # starts from scratch each time
    try:
        root_folders = [f.path for f in os.scandir('.') if f.is_dir()]
        for folder in root_folders:
            if folder.startswith('.\\tf2_rich_presence'):
                shutil.rmtree(folder)
                print(f"Removed old build folder: {folder}")
    except FileNotFoundError:
        print("No old build folder found")

    files_in_cwd = os.listdir('.')
    for file in files_in_cwd:
        if file.startswith('tf2_rich_presence_'):
            if file.endswith('.exe') or file.endswith('.zip'):
                os.remove(file)
                print(f"Removed old package: {file}")

    # creates folders again
    time.sleep(0.25)  # because windows is slow sometimes
    new_build_folder_name = f'tf2_rich_presence_{version_num}'
    os.mkdir(new_build_folder_name)
    os.mkdir(f'{new_build_folder_name}\\resources')
    os.mkdir(f'{new_build_folder_name}\\logs')
    print(f"Created new build folder: {new_build_folder_name}")

    files_to_copy = [('maps.json', f'{new_build_folder_name}\\resources\\'),
                     ('custom_maps.json', f'{new_build_folder_name}\\resources\\'),
                     ('LICENSE', f'{new_build_folder_name}\\resources\\'),
                     ('main.py', f'{new_build_folder_name}\\resources\\'),
                     ('readme.txt', f'{new_build_folder_name}\\'),
                     ('Launch TF2 with Rich Presence.bat', f'{new_build_folder_name}\\'),
                     ('logger.py', f'{new_build_folder_name}\\resources\\'),
                     ('updater.py', f'{new_build_folder_name}\\resources\\'),
                     ('configs.py', f'{new_build_folder_name}\\resources\\'),
                     ('custom_maps.py', f'{new_build_folder_name}\\resources\\')]

    # copies files, adding any version numbers
    for file_dest_pair in files_to_copy:
        with open(file_dest_pair[0], 'r') as file_source:
            with open(f'{file_dest_pair[1]}{file_dest_pair[0]}', 'w') as file_target:
                modified_file = file_source.read().replace('{tf2rpvnum}', version_num)

                if file_dest_pair[0] == 'main.py':
                    modified_file = modified_file.replace('log.cleanup(20)', 'log.cleanup(5)')
                if file_dest_pair[0] == 'logger.py':
                    modified_file = modified_file.replace('to_stderr: bool = True', 'to_stderr: bool = False').replace('sentry_enabled: bool = False', 'sentry_enabled: bool = True')

                file_target.write(modified_file)
                print(f"Copied and modified {file_dest_pair[0]}")

    # creates README.md from README-source.md
    with open('README-source.md', 'r') as readme_md_source:
        modified_readme_md = readme_md_source.read().replace('{tf2rpvnum}', version_num)
    with open('README.md', 'w') as readme_md_target:
        readme_md_target.write(modified_readme_md)
    print("Created README.md from modified README-source.md")

    # copies stuff to the Github repo
    if github_repo_path != 'n':
        print("Copied", shutil.copy2('main.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('build.py', github_repo_path))
        print("Copied", shutil.copy2('tests.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('logger.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('configs.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('custom_maps.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('updater.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('map list generator.py', github_repo_path))
        print("Copied", shutil.copy2('thumb formatter.py', github_repo_path))
        print("Copied", shutil.copy2('maps.json', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('main menu.png', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('preview.png', github_repo_path))
        print("Copied", shutil.copy2('Tf2-logo.png', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('unknown_map.png', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('readme.txt', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('requirements.txt', github_repo_path))
        print("Copied", shutil.copy2('tf2_logo_blurple.ico', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('Launch TF2 with Rich Presence.bat', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('README-source.MD', github_repo_path))
        print("Copied", shutil.copy2('README.MD', github_repo_path))

        # copies test resources
        test_resources_source = os.path.abspath('test_resources')
        test_resources_target = os.path.abspath(f'{github_repo_path}\\TF2 Rich Presence\\test_resources')
        shutil.rmtree(test_resources_target)
        print(f"Copying from {test_resources_source} to {test_resources_target}")
        subprocess.run(f'xcopy \"{test_resources_source}\" \"{test_resources_target}\\\" /E /Q')

        # copies build tools
        build_tools_source = os.path.abspath('build_tools')
        build_tools_target = os.path.abspath(f'{github_repo_path}\\build_tools')
        shutil.rmtree(build_tools_target)
        print(f"Copying from {build_tools_source} to {build_tools_target}")
        subprocess.run(f'xcopy \"{build_tools_source}\" \"{build_tools_target}\\\" /E /Q')

    # clears custom map cache
    with open(f'{new_build_folder_name}\\resources\\custom_maps.json', 'w') as maps_db:
        json.dump({}, maps_db, indent=4)

    # copies the python interpreter
    python_source = os.path.abspath('python')
    python_target = os.path.abspath(f'{new_build_folder_name}\\resources\\python')
    print(f"Copying from {python_source} to {python_target}")
    subprocess.run(f'xcopy \"{python_source}\" \"{python_target}\\\" /E /Q')

    # looks at every file and folder in python
    for root, dirs, files in os.walk(f'{new_build_folder_name}\\resources\\python'):
        # deletes cache files (will get regenerated anyway)
        if '__pycache__' in root:
            shutil.rmtree(root)
            print("Deleted", root)

        # deletes tests (not used during runtime hopefully)
        if 'test' in root:
            shutil.rmtree(root)
            print("Deleted", root)

        # deletes .pdb files (debugger stuff I think, also not runtime)
        for file in files:
            if file.endswith(".pdb"):
                pdb_path = os.path.join(root, file)
                os.remove(pdb_path)
                print(f"Deleted {pdb_path}")

    batch_location = os.path.abspath(f'{new_build_folder_name}\\Launch TF2 with Rich Presence.bat')
    exe_location = os.path.abspath(f'{new_build_folder_name}\\Launch TF2 with Rich Presence.exe')
    icon_location = os.path.abspath('tf2_logo_blurple.ico')
    version_num_windows = version_num[1:].replace('.', ',') + ',0'
    bat2exe_command_1 = f'build_tools\\Bat_To_Exe_Converter.exe -bat "{batch_location}" -save "{exe_location}" -icon "{icon_location}" -x64 -fileversion "{version_num_windows}"'
    bat2exe_command_2 = f'-productversion "{version_num_windows}" -company "Kataiser" -productname "TF2 Rich Presence" -description "Discord Rich Presence for Team Fortress 2"'
    print(f"Creating {exe_location}...")
    subprocess.run(f'{bat2exe_command_1} {bat2exe_command_2}')
    os.remove(batch_location)
    print(f"Deleted {batch_location}")

    package7zip_command_exe_1 = f'build_tools\\7za.exe a tf2_rich_presence_{version_num}_installer.exe tf2_rich_presence_{version_num}\\'
    package7zip_command_exe_2 = f'-sfx build_tools\\7zCon.sfx -ssw -mx=9 -myx=9 -mmt=2 -m0=LZMA2:d=8m'
    package7zip_command_zip = f'build_tools\\7za.exe a tf2_rich_presence_{version_num}.zip tf2_rich_presence_{version_num}\\ -ssw -mx=9 -m0=LZMA:d=8m -mmt=2'
    with tempfile.TemporaryFile() as nowhere:
        print(f"Creating tf2_rich_presence_{version_num}_installer.exe...")
        subprocess.run(f'{package7zip_command_exe_1} {package7zip_command_exe_2}', stdout=nowhere)
        print(f"Creating tf2_rich_presence_{version_num}.zip...")
        subprocess.run(package7zip_command_zip, stdout=nowhere)


if __name__ == '__main__':
    main('v1.5.8')
