import json
import os
import shutil
import time

items_to_delete = []
requirements_to_keep = ['discoIPC', 'discoIPC-1.0.0.dist-info', 'psutil', 'psutil-5.4.3.dist-info']

try:
    shutil.rmtree('tf2_rich_presence')
    print("Removed old build folder")
except FileNotFoundError:
    print("No old build folder found")

time.sleep(0.25)
os.mkdir('tf2_rich_presence')
os.mkdir('tf2_rich_presence\\resources')
print("Created new build folder")

print("Copied", shutil.copy2('main.py', 'tf2_rich_presence\\resources\\'))
print("Copied", shutil.copy2('maps.json', 'tf2_rich_presence\\resources\\'))
print("Copied", shutil.copy2('custom_maps.json', 'tf2_rich_presence\\resources\\'))
print("Copied", shutil.copy2('TF2 rich presence.bat', 'tf2_rich_presence\\'))
print("Copied", shutil.copy2('LICENSE', 'tf2_rich_presence\\resources\\'))
print("Copied", shutil.copy2('readme.txt', 'tf2_rich_presence\\'))

with open('tf2_rich_presence\\resources\\custom_maps.json', 'w') as maps_db:
    json.dump({}, maps_db, indent=4)

print("Copied", shutil.copytree('python', 'tf2_rich_presence\\resources\\python'))

for delete_this in items_to_delete:
    try:
        shutil.rmtree(delete_this)
    except NotADirectoryError:
        os.remove(delete_this)

    print("Deleted {}".format(delete_this))

for root, dirs, files in os.walk('tf2_rich_presence\\resources\\python'):
    if '__pycache__' in root:
        shutil.rmtree(root)
        print("Deleted", root)

    if 'test' in root:
        shutil.rmtree(root)
        print("Deleted", root)

    for file in files:
        if file.endswith(".pdb"):
            pdb_path = os.path.join(root, file)
            os.remove(pdb_path)
            print("Deleted {}".format(pdb_path))
