import shutil
import os

items_to_delete = ['tf2_rich_presence\\resources\\venv\\Scripts\\tk86t.dll',
                   'tf2_rich_presence\\resources\\venv\\Scripts\\tcl86t.dll',
                   'tf2_rich_presence\\resources\\venv\\Scripts\\sqlite3.dll',
                   'tf2_rich_presence\\resources\\venv\Lib\\site-packages\\psutil\\tests']
requirements_to_keep = ['discoIPC', 'discoIPC-1.0.0.dist-info', 'psutil', 'psutil-5.4.3.dist-info', 'easy-install.pth']

print("Copied", shutil.copy2('main.py', 'tf2_rich_presence\\resources\\'))
print("Copied", shutil.copy2('run.bat', 'tf2_rich_presence\\'))

shutil.rmtree('tf2_rich_presence\\resources\\venv')
print("Cleared venv")

print("Copied", shutil.copytree('venv', 'tf2_rich_presence\\resources\\venv'))

for delete_this in items_to_delete:
    try:
        shutil.rmtree(delete_this)
    except NotADirectoryError:
        os.remove(delete_this)

    print("Deleted {}".format(delete_this))

for site_package_item in os.listdir('tf2_rich_presence\\resources\\venv\Lib\\site-packages'):
    if site_package_item not in requirements_to_keep:
        delete_location = 'tf2_rich_presence\\resources\\venv\Lib\\site-packages\\' + site_package_item

        try:
            shutil.rmtree(delete_location)
        except NotADirectoryError:
            os.remove(delete_location)

        print("Deleted {}".format(delete_location))

for subdirectory in os.walk('tf2_rich_presence\\resources\\venv'):
    subdirectory_top = subdirectory[0]
    if '__pycache__' in subdirectory_top:
        shutil.rmtree(subdirectory_top)
        print("Deleted", subdirectory_top)

try:
    os.remove('tf2_rich_presence.zip')
    print("Deleted old archive")
except FileNotFoundError:
    pass

shutil.make_archive('tf2_rich_presence', 'zip', 'tf2_rich_presence')
print("Created new archive")
