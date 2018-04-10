import shutil
import os

items_to_delete = ['tf2_rich_presence\\resources\\venv\\Lib\\site-packages\\beautifulsoup4-4.6.0.dist-info',
                   'tf2_rich_presence\\resources\\venv\\Lib\\site-packages\\bs4',
                   'tf2_rich_presence\\resources\\venv\\Lib\\site-packages\\lxml',
                   'tf2_rich_presence\\resources\\venv\\Lib\\site-packages\\lxml-4.2.1.dist-info',
                   'tf2_rich_presence\\resources\\venv\\Lib\\site-packages\\PIL',
                   'tf2_rich_presence\\resources\\venv\\Lib\\site-packages\\pip-9.0.1-py3.6.egg',
                   'tf2_rich_presence\\resources\\venv\\Scripts\\tk86t.dll',
                   'tf2_rich_presence\\resources\\venv\\Scripts\\tcl86t.dll',
                   'tf2_rich_presence\\resources\\venv\\Scripts\\sqlite3.dll',
                   'tf2_rich_presence\\resources\\venv\Lib\\site-packages\\psutil\\tests',
                   'tf2_rich_presence\\resources\\venv\\Lib\\site-packages\\setuptools-28.8.0-py3.6.egg']

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
