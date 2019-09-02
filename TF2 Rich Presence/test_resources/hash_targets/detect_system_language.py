import ctypes
import json
import locale
import os
import tkinter as tk
from tkinter import messagebox

import logger
import settings


# if the system (OS) language doesn't match the current settings, ask to change language (only once)
def main():
    log = logger.Log()

    db_path = os.path.join('resources', 'DB.json') if os.path.isdir('resources') else 'DB.json'
    with open(db_path, 'r') as db_json_r:
        db_data = json.load(db_json_r)

    if not db_data['has_asked_language']:
        # language_codes = {'en': 'English', 'de': 'German', 'fr': 'French', 'es': 'Spanish', 'pt': 'Portuguese', 'it': 'Italian', 'nl': 'Dutch', 'pl': 'Polish', 'ru': 'Russian',
        #                   'ko': 'Korean', 'zh': 'Chinese', 'ja': 'Japanese'}
        language_codes = {'en': 'English', 'de': 'German', 'fr': 'French', 'es': 'Spanish', 'pt': 'Portuguese', 'it': 'Italian', 'nl': 'Dutch', 'pl': 'Polish'}

        system_locale = locale.windows_locale[ctypes.windll.kernel32.GetUserDefaultUILanguage()]
        system_language_code = system_locale.split('_')[0]
        system_language = language_codes[system_language_code]

        if settings.get('language') != system_language:
            log.info(f"System language ({system_locale}, {system_language}) != settings language ({settings.get('language')}), asking to change")

            with open(db_path, 'r+') as db_json_w:
                db_data['has_asked_language'] = True
                db_json_w.seek(0)
                db_json_w.truncate(0)
                json.dump(db_data, db_json_w, indent=4)

            root = tk.Tk()
            root.overrideredirect(1)
            root.withdraw()
            root.lift()
            root.attributes('-topmost', True)
            try:
                root.iconbitmap(default='tf2_logo_blurple_wrench.ico')
            except tk.TclError:
                root.iconbitmap(default=os.path.join('resources', 'tf2_logo_blurple_wrench.ico'))

            changed_language = messagebox.askquestion("TF2 Rich Presence {tf2rpvnum}", f"Change language to your system's default ({system_language})?")
            log.debug(f"Changed language: {changed_language}")

            if changed_language == 'yes':
                temp_settings = settings.access_settings_file()
                temp_settings['language'] = system_language
                settings.access_settings_file(save_dict=temp_settings)
                raise SystemExit


if __name__ == '__main__':
    main()
