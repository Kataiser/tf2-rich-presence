# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import ctypes
import locale
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
        language_codes = {'en': 'English', 'de': 'German', 'fr': 'French', 'es': 'Spanish', 'pt': 'Portuguese', 'it': 'Italian', 'nl': 'Dutch', 'pl': 'Polish', 'ru': 'Russian',
                          'ko': 'Korean', 'zh': 'Chinese', 'ja': 'Japanese'}

        system_locale: str = locale.windows_locale[ctypes.windll.kernel32.GetUserDefaultUILanguage()]
        system_language_code: str = system_locale.split('_')[0]
        is_brazilian_port: bool = system_locale == 'pt_BR'

        if system_language_code in language_codes or is_brazilian_port:
            system_language: str = language_codes[system_language_code]
            can_localize: bool = True
        else:
            log.error(f"System locale {system_locale} is not localizable")
            can_localize = False

        if can_localize and settings.get('language') != system_language:
            log.info(f"System language ({system_locale}, {system_language}) != settings language ({settings.get('language')}), asking to change")

            db['has_asked_language'] = True
            utils.access_db(db)

            root = tk.Tk()
            root.overrideredirect(1)
            root.withdraw()
            root.lift()
            root.attributes('-topmost', True)
            settings.set_window_icon(log, root, False)

            system_language_display: str = 'Português Brasileiro' if is_brazilian_port else system_language
            changed_language: str = messagebox.askquestion(f"TF2 Rich Presence {launcher.VERSION}", f"Change language to your system's default ({system_language_display})?")
            log.debug(f"Changed language: {changed_language}")

            if changed_language == 'yes':
                temp_settings: dict = settings.access_registry()
                temp_settings['language'] = system_language
                settings.access_registry(save_dict=temp_settings)
                settings.get.cache_clear()


if __name__ == '__main__':
    log = logger.Log()
    detect(log)
