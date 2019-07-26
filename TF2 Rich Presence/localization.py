import functools
import json
import os
import zlib

import settings


class Localizer:
    def __init__(self, log=None, language_override=None):
        self.log = log
        self.language = language_override if language_override else settings.get('language')

    @functools.lru_cache(maxsize=None)
    def text(self, english_text):
        english_text_adler32 = str(zlib.adler32(english_text.replace('{tf2rpvnum}', '').encode('utf-8'))).ljust(10, '0')

        if english_text_adler32 not in load_language_file('English_modified').keys():
            english_to_modify = load_language_file('English_modified')
            english_to_modify[english_text_adler32] = english_text

            with open(get_language_file_path('English_modified'), 'w') as english_json:
                json.dump(english_to_modify, english_json, indent=4, sort_keys=True)

        if self.language == 'English':
            return english_text
        else:
            try:
                return load_language_file(self.language)[english_text_adler32]
            except KeyError:
                if self.log:
                    self.log.error(f"\"{english_text}\" not in {self.language}")


@functools.lru_cache(maxsize=None)
def load_language_file(language):
    with open(get_language_file_path(language), 'r', encoding='utf-8') as language_file:
        return json.load(language_file)


@functools.lru_cache(maxsize=None)
def get_language_file_path(language):
    if os.path.isdir('resources'):
        return os.path.join('resources', 'localization', f'{language}.json')
    else:
        return os.path.join('localization', f'{language}.json')


if __name__ == '__main__':
    pass
