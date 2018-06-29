import json
import os
import shutil
import time


def main(version_num):
    github_repo_path = input("Github repo path: ")

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
        shutil.rmtree('tf2_rich_presence')
        print("Removed old build folder")
    except FileNotFoundError:
        print("No old build folder found")

    # creates folders again
    time.sleep(0.25)  # because windows is slow sometimes
    os.mkdir('tf2_rich_presence')
    os.mkdir('tf2_rich_presence\\resources')
    print("Created new build folder")

    # copies needed files
    print("Copied", shutil.copy2('maps.json', 'tf2_rich_presence\\resources\\'))
    print("Copied", shutil.copy2('custom_maps.json', 'tf2_rich_presence\\resources\\'))
    print("Copied", shutil.copy2('TF2 rich presence.bat', 'tf2_rich_presence\\'))
    print("Copied", shutil.copy2('LICENSE', 'tf2_rich_presence\\resources\\'))

    # copies and modifies main.py to have the above version number
    with open('main.py', 'r') as main_py_source:
        with open('tf2_rich_presence\\resources\\main.py', 'w') as main_py_target:
            modified_main = main_py_source.read().replace('{tf2rpvnum}', version_num)
            main_py_target.write(modified_main)
            print("Copied and modified main.py")

    # ditto but with readme.txt
    with open('readme.txt', 'r') as readme_source:
        with open('tf2_rich_presence\\readme.txt', 'w') as readme_target:
            modified_readme = readme_source.read().replace('{tf2rpvnum}', version_num)
            readme_target.write(modified_readme)
            print("Copied and modified readme.txt")

    # creates README.md from README-source.md
    with open('README-source.md', 'r') as readme_md_source:
        modified_readme_md = readme_md_source.read().replace('{tf2rpvnum}', version_num)
    with open('README.md', 'w') as readme_md_target:
        readme_md_target.write(modified_readme_md)
    print("Created README.md from modified README-source.md")

    # clears custom map cache
    with open('tf2_rich_presence\\resources\\custom_maps.json', 'w') as maps_db:
        json.dump({}, maps_db, indent=4)

    # copies the python installation (good luck running this yourself lol)
    print("Copied", shutil.copytree('python', 'tf2_rich_presence\\resources\\python'))

    # looks at every file and folder in python
    for root, dirs, files in os.walk('tf2_rich_presence\\resources\\python'):
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

    # copies stuff to the Github repo
    print("Copied", shutil.copy2('main.py', github_repo_path))
    print("Copied", shutil.copy2('build.py', github_repo_path))
    print("Copied", shutil.copy2('map list generator.py', github_repo_path))
    print("Copied", shutil.copy2('thumb formatter.py', github_repo_path))
    print("Copied", shutil.copy2('maps.json', github_repo_path))
    print("Copied", shutil.copy2('main menu.png', github_repo_path))
    print("Copied", shutil.copy2('preview.png', github_repo_path))
    print("Copied", shutil.copy2('Tf2-logo.png', github_repo_path))
    print("Copied", shutil.copy2('unknown_map.png', github_repo_path))
    print("Copied", shutil.copy2('readme.txt', github_repo_path))
    print("Copied", shutil.copy2('TF2 rich presence.bat', github_repo_path))
    print("Copied", shutil.copy2('README-source.MD', github_repo_path))
    if update_readme:
        print("Copied", shutil.copy2('README.MD', github_repo_path))


if __name__ == '__main__':
    main('v1.4.2')
