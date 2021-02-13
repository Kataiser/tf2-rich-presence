# Copyright (C) 2018-2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import ctypes
import functools
import json
import locale
import os
import zlib
from tkinter import messagebox
from typing import Dict, Optional, Union
from typing import List

import launcher
import logger
import settings
import utils


class Localizer:
    def __init__(self, log: Optional[logger.Log] = None, language: str = settings.get('language'), appending: bool = False):
        self.log: Optional[logger.Log] = log
        self.language: str = language
        self.missing_lines: List[str] = []  # TODO: ingest from DB.json maybe
        self.appending: bool = appending  # if extending localization.json

        if os.path.isdir('resources'):
            self.loc_file_path: str = os.path.join('resources', 'localization.json')
        else:
            self.loc_file_path = 'localization.json'

        self.loc_file_exists: bool = os.path.isfile(self.loc_file_path)
        if not self.loc_file_exists and self.log:
            self.log.error(f"localization.json doesn't exist (should be at {os.path.abspath(self.loc_file_path)})")

        self.text.cache_clear()

    def __repr__(self) -> str:
        return f"localization.Localizer ({self.language}, appending={self.appending}, {len(self.missing_lines)} missing lines)"

    @functools.cache
    def text(self, english_text: str) -> str:
        if not self.loc_file_exists:
            return english_text

        # TODO: use manual language keys instead of text hashes (maybe)
        english_text_adler32: str = hash_text(english_text)

        if self.appending:  # only used for development
            access_localization_file(self.loc_file_path, append=(english_text_adler32, english_text))
            return english_text

        if english_text_adler32 not in access_localization_file(self.loc_file_path):
            if english_text not in self.missing_lines:
                self.missing_lines.append(english_text)

                db: Dict[str, Union[bool, list, str]] = utils.access_db()
                db['missing_localization'].append(english_text)
                utils.access_db(db)
                if self.log:
                    self.log.debug(f"\"{english_text}\" not in localization (language is {self.language})")

            # no available translation, so must default to the English text
            return english_text

        if self.language == 'English':
            # returns what was passed to this function, NOT what's in localization.json
            # this means that that data is only used for helping with translating
            return english_text
        else:
            try:
                return access_localization_file(self.loc_file_path)[english_text_adler32][self.language]
            except KeyError as error:
                raise KeyError(f"{error}, ({self.loc_file_path}, {english_text_adler32}, {self.language})")


@functools.cache
def access_localization_file(path: str = 'localization.json', append: Optional[tuple] = None) -> Optional[dict]:
    with open(path, 'r', encoding='UTF8') as localization_file:
        localization_data: dict = json.load(localization_file)

    if not append:
        return localization_data
    else:
        append_hash, append_text = append

        if append_hash not in localization_data:
            localization_data[append_hash] = {}
            localization_data[append_hash]['English'] = append_text
            print(f"Hash: {append_hash}, {len(localization_data)} keys")

            for language in ('German', 'French', 'Spanish', 'Portuguese', 'Italian', 'Dutch', 'Polish', 'Russian', 'Korean', 'Chinese', 'Japanese'):
                localization_data[append_hash][language] = ""

            localization_data_sorted: dict = dict(sorted(localization_data.items(), key=lambda kv: (kv[1]['English'], kv[0])))  # sort lexographically using English text

            with open(path, 'w', encoding='UTF8') as localization_file:
                json.dump(localization_data_sorted, localization_file, indent=4, ensure_ascii=False)
        else:
            print(f"Already exists with hash {append_hash}")


def hash_text(text: str) -> str:
    return str(zlib.adler32(text.replace(launcher.VERSION, '').encode('UTF8'))).ljust(10, '0')  # shoulda just used hash() from the start


# if the system (OS) language doesn't match the current settings, ask to change language (but only once)
def detect_system_language(log: logger.Log):
    db: Dict[str, Union[bool, list, str]] = utils.access_db()

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
            system_language_display: str = 'Português Brasileiro' if is_brazilian_port else system_language
            # this is intentionally not localized
            changed_language: str = messagebox.askquestion(f"TF2 Rich Presence {launcher.VERSION}", f"Change language to your system's default ({system_language_display})?")
            log.debug(f"Changed language: {changed_language}")

            if changed_language == 'yes':
                settings.change('language', system_language)


if __name__ == '__main__':
    # manually add text
    manual_localizer = Localizer(language='English', appending=True)

    while True:
        manual_localizer.text(input(": "))
        manual_localizer.text.cache_clear()
