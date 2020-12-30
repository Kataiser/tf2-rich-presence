# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import functools
import json
import os
import zlib
from typing import List, Union

import launcher
import utils


class Localizer:
    def __init__(self, log=None, language: Union[str, None] = None, appending: bool = False):
        self.log = log
        self.language: Union[str, None] = language
        self.missing_lines: List[str] = []
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

    @functools.lru_cache(maxsize=None)
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

                db: dict = utils.access_db()
                db['missing_localization'].append(english_text)
                utils.access_db(db)
                if self.log:
                    self.log.debug(f"\"{english_text}\" not in localization (language is {self.language})")

            # no available translation, so must default to the English text
            return english_text

        if self.language == 'English':
            return english_text
        else:
            try:
                return access_localization_file(self.loc_file_path)[english_text_adler32][self.language]
            except KeyError as error:
                raise KeyError(f"{error}, ({self.loc_file_path}, {english_text_adler32}, {self.language})")


@functools.lru_cache(maxsize=1)
def access_localization_file(path: str = 'localization.json', append: Union[tuple, None] = None) -> dict:
    with open(path, 'r', encoding='UTF8') as localization_file:
        localization_data: dict = json.load(localization_file)

    if not append:
        return localization_data
    else:
        append_hash, append_text = append

        if append_hash not in localization_data:
            localization_data[append_hash] = {}
            localization_data[append_hash]['English'] = append_text
            print(f"Hash: {append_hash}, element {len(localization_data)}")

            for language in ('German', 'French', 'Spanish', 'Portuguese', 'Italian', 'Dutch', 'Polish', 'Russian', 'Korean', 'Chinese', 'Japanese'):
                localization_data[append_hash][language] = ""

            localization_data_sorted: dict = dict(sorted(localization_data.items(), key=lambda kv: (kv[1]['English'], kv[0])))  # sort lexographically using English text

            with open(path, 'w', encoding='UTF8') as localization_file:
                json.dump(localization_data_sorted, localization_file, indent=4, ensure_ascii=False)
        else:
            print(f"Already exists with hash {append_hash}")


def hash_text(text: str) -> str:
    return str(zlib.adler32(text.replace(launcher.VERSION, '').encode('UTF8'))).ljust(10, '0')  # shoulda just used hash() from the start


if __name__ == '__main__':
    # manually add text
    manual_localizer = Localizer(language='English', appending=True)

    while True:
        manual_localizer.text(input(": "))
        manual_localizer.text.cache_clear()
