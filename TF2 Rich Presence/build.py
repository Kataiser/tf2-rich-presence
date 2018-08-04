import json
import os
import shutil
import subprocess
import time


def main(version_num):
    print(f"Building TF2 Rich Presence {version_num}")
    github_repo_path = input("Github repo path ('n' to skip): ")

    if github_repo_path != 'n':
        got_valid_input = False
        while not got_valid_input:
            update_readme_raw = input("Update README? (y/n) ")
            if update_readme_raw.lower() == 'y':
                update_readme = True
                got_valid_input = True
            elif update_readme_raw.lower() == 'n':
                update_readme = False
                got_valid_input = True
            else:
                print('Invalid input, must be "y" or "n".')

    # starts from scratch each time
    try:
        root_folders = [f.path for f in os.scandir('.') if f.is_dir()]
        for folder in root_folders:
            if folder.startswith('.\\tf2_rich_presence'):
                shutil.rmtree(folder)
                print(f"Removed old build folder: {folder}")
    except FileNotFoundError:
        print("No old build folder found")

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
                modified_file = file_source.read().replace('{tf2rpvnum}', version_num).replace('log.dev = True', 'log.dev = False')
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
        print("Copied", shutil.copy2('build.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('tests.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('logger.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('configs.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('custom_maps.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('updater.py', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('map list generator.py', github_repo_path))
        print("Copied", shutil.copy2('thumb formatter.py', github_repo_path))
        print("Copied", shutil.copy2('maps.json', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('main menu.png', github_repo_path))
        print("Copied", shutil.copy2('preview.png', github_repo_path))
        print("Copied", shutil.copy2('Tf2-logo.png', github_repo_path))
        print("Copied", shutil.copy2('unknown_map.png', github_repo_path))
        print("Copied", shutil.copy2('readme.txt', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('requirements.txt', github_repo_path))
        print("Copied", shutil.copy2('Launch TF2 with Rich Presence.bat', f'{github_repo_path}\\TF2 Rich Presence'))
        print("Copied", shutil.copy2('README-source.MD', github_repo_path))
        if update_readme:
            print("Copied", shutil.copy2('README.MD', github_repo_path))

        # copies test_resources
        test_resources_source = os.path.abspath('test_resources')
        test_resources_target = os.path.abspath(f'{github_repo_path}\\TF2 Rich Presence\\test_resources')
        shutil.rmtree(test_resources_target)
        print(f"Copying from {test_resources_source} to {test_resources_target}")
        subprocess.run(f'xcopy \"{test_resources_source}\" \"{test_resources_target}\\\" /E /Q')

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
                print("Deleted {}".format(pdb_path))

    print(f"\ntf2_rich_presence_{version_num}_installer.exe")
    print(f"tf2_rich_presence_{version_num}.zip")
    print("Remember to only package immediately after building")


if __name__ == '__main__':
    main('v1.5.6')
