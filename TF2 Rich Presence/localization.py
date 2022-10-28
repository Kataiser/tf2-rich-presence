# Copyright (C) 2018-2022 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import ctypes
import functools
import locale
import os
import zlib
from tkinter import messagebox
from typing import Dict, Optional, Tuple, Union
from typing import List

import ujson

import launcher
import logger
import settings
import utils


class Localizer:
    def __init__(self, log: Optional[logger.Log] = None, language: Optional[str] = None, appending: bool = False, persist_missing: bool = True):
        self.log: Optional[logger.Log] = log
        self.language: str = language if language else settings.get('language')
        self.appending: bool = appending  # if extending localization files
        self.text.cache_clear()
        self.missing_lines: List[str] = utils.access_db()['missing_localization'] if persist_missing else []

    def __repr__(self) -> str:
        return f"localization.Localizer ({self.language}, appending={self.appending}, {len(self.missing_lines)} missing lines)"

    @functools.cache
    def text(self, english_text: str) -> str:
        # TODO: use manual language keys instead of text hashes (maybe)
        english_text_adler32: str = hash_text(english_text)

        if self.appending:  # only used for development
            access_localization_data(append=(english_text_adler32, english_text))
            return english_text

        if english_text_adler32 not in access_localization_data()[self.language]:
            if english_text not in self.missing_lines:
                self.missing_lines.append(english_text)

                db: Dict[str, Union[bool, list, str]] = utils.access_db()
                db['missing_localization'].append(english_text)
                utils.access_db(db)
                if self.log:
                    self.log.error(f"\"{english_text}\" not in {self.language} localization", reportable=False)

            # no available translation, so must default to the English text
            return english_text

        if self.language == 'English':
            # returns what was passed to this function, NOT what's in English.json
            # this means that that file is only used for helping with translating
            return english_text
        else:
            try:
                return access_localization_data()[self.language][english_text_adler32]
            except KeyError as error:
                raise KeyError(f"{error}, ({english_text_adler32}, {self.language})")


@functools.cache
def access_localization_data(append: Optional[tuple] = None) -> Optional[dict]:
    localization_data: dict = read_localization_files()

    if not append:
        return localization_data
    else:
        append_hash, append_text = append

        if append_hash not in localization_data['English']:
            localization_data['English'][append_hash] = append_text
            print(f"Hash: {append_hash}, {len(localization_data['English']) - 4} keys")
            localization_data['English'] = dict(sorted(localization_data['English'].items(), key=lambda kv: (kv[1], kv[0])))  # sort lexographically using English text

            for lang in langs:
                localization_data_out: dict = {'name_localized': localization_data[lang]['name_localized'], 'code': localization_data[lang]['code'],
                                               'credits': localization_data[lang]['credits'], 'notes': localization_data[lang]['notes']}

                for key in localization_data['English']:
                    if key in localization_data[lang]:
                        localization_data_out[key] = localization_data[lang][key]
                    else:
                        localization_data_out[key] = ""

                with open(os.path.join('locales', f'{lang}.json'), 'w', encoding='UTF8') as localization_file:
                    ujson.dump(localization_data_out, localization_file, indent=4, ensure_ascii=False, escape_forward_slashes=False)
        else:
            print(f"Already exists with hash {append_hash}")


@functools.cache
def read_localization_files() -> dict:
    locale_datas: dict = {}

    for file in os.listdir('locales'):
        file_split: Tuple[str, str] = os.path.splitext(file)
        file_path: str = os.path.join('locales', file)

        if os.path.isfile(file_path) and file_split[1] == '.json':
            lang_name: str = file_split[0]

            with open(file_path, 'r', encoding='UTF8') as localization_file:
                locale_datas[lang_name] = ujson.load(localization_file)

    return locale_datas


def hash_text(text: str) -> str:
    return str(zlib.adler32(text.replace(launcher.VERSION, '').encode('UTF8'))).ljust(10, '0')  # shoulda just used hash() from the start


# if the system (OS) language doesn't match the current settings, ask to change language (but only once)
def detect_system_language(log: logger.Log):
    db: Dict[str, Union[bool, list, str]] = utils.access_db()

    if not db['has_asked_language']:
        language_codes: dict = {read_localization_files()[lang]['code']: lang for lang in langs[1:]}
        system_locale: str = locale.windows_locale[ctypes.windll.kernel32.GetUserDefaultUILanguage()]
        system_language_code: str = system_locale.split('_')[0]
        is_brazilian_port: bool = system_locale == 'pt_BR'

        if system_language_code in language_codes or is_brazilian_port:
            system_language: str = language_codes[system_language_code]
            can_localize: bool = True
        else:
            if system_language_code != 'en':
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


with open(os.path.join('locales', 'order.txt'), 'r') as order_file:
    langs: List[str] = order_file.read().splitlines()

langs_localized: List[str] = [read_localization_files()[lang]['name_localized'] for lang in langs]


if __name__ == '__main__':
    # manually add text
    manual_localizer = Localizer(language='English', appending=True)

    while True:
        manual_localizer.text(input(": ").replace('\\n', '\n'))
        manual_localizer.text.cache_clear()
