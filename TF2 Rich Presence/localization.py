# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import functools
import inspect
import json
import os
import zlib


class Localizer:
    def __init__(self, log=None, language=None, appending=False):
        self.log = log
        self.language = language
        self.missing_lines = []
        self.appending = appending  # if extending localization.json

    @functools.lru_cache(maxsize=None)
    def text(self, english_text: str) -> str:
        english_text_adler32 = hash_text(english_text)

        if english_text_adler32 not in access_localization_file():  # exclude that because it causes DB.json spam
            if english_text not in self.missing_lines:
                self.missing_lines.append(english_text)

                db_path = os.path.join('resources', 'DB.json') if os.path.isdir('resources') else 'DB.json'
                with open(db_path, 'r+') as db_json:
                    db_data = json.load(db_json)
                    db_data['missing_localization'].append(english_text)
                    db_json.seek(0)
                    db_json.truncate(0)
                    json.dump(db_data, db_json, indent=4)

                if self.log:
                    frame = inspect.stack()[1]
                    module = inspect.getmodule(frame[0])
                    caller_filename = os.path.basename(module.__file__)
                    self.log.debug(f"\"{english_text}\" not in localization (language is {self.language}, called by {caller_filename})")

            if self.appending:  # only used for development
                access_localization_file(append=(english_text_adler32, english_text))

            # no available translation, so must default to the English text
            return english_text

        if self.language == 'English':
            return english_text
        else:
            return access_localization_file()[english_text_adler32][self.language]


@functools.lru_cache(maxsize=1)
def access_localization_file(append=None) -> dict:
    if os.path.isdir('resources'):
        localization_file_path = os.path.join('resources', 'localization.json')
    else:
        localization_file_path = 'localization.json'

    with open(localization_file_path, 'r', encoding='utf-8') as localization_file:
        localization_data = json.load(localization_file)

    if not append:
        return localization_data
    else:
        localization_data[append[0]] = {}
        localization_data[append[0]]['English'] = append[1]

        for language in ['German', 'French', 'Spanish', 'Portuguese', 'Italian', 'Dutch', 'Polish', 'Russian', 'Korean', 'Chinese', 'Japanese']:
            localization_data[append[0]][language] = ""

        with open(localization_file_path, 'w', encoding='utf-8') as localization_file:
            json.dump(localization_data, localization_file, indent=4, ensure_ascii=False)


def hash_text(text: str) -> str:
    return str(zlib.adler32(text.replace('{tf2rpvnum}', '').encode('utf-8'))).ljust(10, '0')  # shoulda just used hash() from the start


if __name__ == '__main__':
    # manually add text
    manual_localizer = Localizer(language='English', appending=True)

    while True:
        manual_localizer.text(input(": "))
