# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import ctypes
import locale
import os
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Union

import launcher
import logger
import settings
import utils


# if the system (OS) language doesn't match the current settings, ask to change language (only once)
def detect(log: logger.Log):
    db: Dict[str, Union[dict, bool, list]] = utils.access_db()

    if not db['has_asked_language']:
        # language_codes = {'en': 'English', 'de': 'German', 'fr': 'French', 'es': 'Spanish', 'pt': 'Portuguese', 'it': 'Italian', 'nl': 'Dutch', 'pl': 'Polish', 'ru': 'Russian',
        #                   'ko': 'Korean', 'zh': 'Chinese', 'ja': 'Japanese'}
        language_codes: Dict[str, str] = {'en': 'English', 'de': 'German', 'fr': 'French', 'es': 'Spanish', 'pt': 'Portuguese', 'it': 'Italian', 'nl': 'Dutch', 'pl': 'Polish'}

        system_locale: str = locale.windows_locale[ctypes.windll.kernel32.GetUserDefaultUILanguage()]
        system_language_code: str = system_locale.split('_')[0]

        try:
            system_language: str = language_codes[system_language_code]
        except KeyError:
            log.error(f"System language code {system_language_code} is not a localized language, defaulting to English")
            system_language: str = 'English'

        if settings.get('language') != system_language:
            log.info(f"System language ({system_locale}, {system_language}) != settings language ({settings.get('language')}), asking to change")

            db['has_asked_language'] = True
            utils.access_db(db)

            root = tk.Tk()
            root.overrideredirect(1)
            root.withdraw()
            root.lift()
            root.attributes('-topmost', True)
            try:
                root.iconbitmap(default='tf2_logo_blurple_wrench.ico')
            except tk.TclError:
                root.iconbitmap(default=os.path.join('resources', 'tf2_logo_blurple_wrench.ico'))

            changed_language: str = messagebox.askquestion(f"TF2 Rich Presence {launcher.VERSION}", f"Change language to your system's default ({system_language})?")
            log.debug(f"Changed language: {changed_language}")

            if changed_language == 'yes':
                temp_settings: dict = settings.access_registry()
                temp_settings['language'] = system_language
                settings.access_registry(save_dict=temp_settings)
                raise SystemExit


if __name__ == '__main__':
    log = logger.Log()
    detect(log)
