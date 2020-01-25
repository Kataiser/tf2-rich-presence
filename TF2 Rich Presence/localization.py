# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import functools
import json
import os
import zlib
from typing import Union

import utils


class Localizer:
    def __init__(self, log=None, language=None, appending=False):
        self.log = log
        self.language = language
        self.missing_lines = []
        self.appending = appending  # if extending localization.json
        self.localization_file_cached = access_localization_file()  # never read it again after startup

    def __repr__(self):
        return f"localization.Localizer ({self.language}, appending={self.appending}, {len(self.missing_lines)} missing lines)"

    @functools.lru_cache(maxsize=None)
    def text(self, english_text: str) -> str:
        # TODO: use manual language keys instead of text hashes (maybe)
        english_text_adler32 = hash_text(english_text)

        if self.appending:  # only used for development
            access_localization_file(append=(english_text_adler32, english_text))
            return english_text

        if english_text_adler32 not in self.localization_file_cached:  # exclude that because it causes DB.json spam
            if english_text not in self.missing_lines:
                self.missing_lines.append(english_text)

                db = utils.access_db()
                db['missing_localization'].append(english_text)
                utils.access_db(db)
                if self.log:
                    self.log.debug(f"\"{english_text}\" not in localization (language is {self.language}, called by {utils.get_caller_filename()})")

            # no available translation, so must default to the English text
            return english_text

        if self.language == 'English':
            return english_text
        else:
            return self.localization_file_cached[english_text_adler32][self.language]


def access_localization_file(append: Union[tuple, None] = None) -> dict:
    if os.path.isdir('resources'):
        localization_file_path = os.path.join('resources', 'localization.json')
    else:
        localization_file_path = 'localization.json'

    with open(localization_file_path, 'r', encoding='utf-8') as localization_file:
        localization_data = json.load(localization_file)

    if not append:
        return localization_data
    else:
        append_hash, append_text = append

        if append_hash not in localization_data:
            localization_data[append_hash] = {}
            localization_data[append_hash]['English'] = append_text
            print(f"Hash: {append_hash}, element {len(localization_data)}")

            for language in ['German', 'French', 'Spanish', 'Portuguese', 'Italian', 'Dutch', 'Polish', 'Russian', 'Korean', 'Chinese', 'Japanese']:
                localization_data[append_hash][language] = ""

            with open(localization_file_path, 'w', encoding='utf-8') as localization_file:
                json.dump(localization_data, localization_file, indent=4, ensure_ascii=False)
        else:
            print(f"Already exists with hash {append_hash}")


def hash_text(text: str) -> str:
    return str(zlib.adler32(text.replace('{tf2rpvnum}', '').encode('utf-8'))).ljust(10, '0')  # shoulda just used hash() from the start


if __name__ == '__main__':
    # manually add text
    manual_localizer = Localizer(language='English', appending=True)

    while True:
        manual_localizer.text(input(": "))
        manual_localizer.text.cache_clear()
