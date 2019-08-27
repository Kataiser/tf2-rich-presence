import functools
import json
import os
import zlib


class Localizer:
    def __init__(self, log=None, language=None):
        self.log = log
        self.language = language
        self.missing_lines = {}

    @functools.lru_cache(maxsize=None)
    def text(self, english_text: str) -> str:
        english_text_adler32 = str(zlib.adler32(english_text.replace('{tf2rpvnum}', '').encode('utf-8'))).ljust(10, '0')

        if english_text_adler32 not in load_language_file('English').keys():
            english_to_modify = load_language_file('English')
            english_to_modify[english_text_adler32] = english_text

            with open(get_language_file_path('English'), 'w') as english_json:
                english_dump = json.dumps(english_to_modify, sort_keys=True)
                english_json.write(english_dump.replace('": "', '": "\n')
                                               .replace('", "', '\n", "')
                                               .replace('"}', '\n"}')
                                               .replace('\\"', '"'))

        if self.language == 'English':
            return english_text
        else:
            try:
                return load_language_file(self.language)[english_text_adler32].lstrip().rstrip()
            except KeyError:
                if self.log:
                    if self.language not in self.missing_lines.keys():
                        self.missing_lines[self.language] = []

                    # don't do the same missing text error log than once
                    if english_text not in self.missing_lines[self.language]:
                        self.log.error(f"\"{english_text}\" not in {self.language}")
                        self.missing_lines[self.language].append(english_text)

                return english_text


@functools.lru_cache(maxsize=None)
def load_language_file(language: str) -> dict:
    with open(get_language_file_path(language), 'r', encoding='utf-8') as language_file:
        language_file_lines = language_file.readlines()

        for text_line_num in range(1, len(language_file_lines), 2):
            language_file_lines[text_line_num] = language_file_lines[text_line_num].replace('"', '\\"')

        language_file_read = ''.join(language_file_lines).replace('\n', '').replace('、', ',')
        return json.loads(language_file_read)


@functools.lru_cache(maxsize=None)
def get_language_file_path(language):
    if os.path.isdir('resources'):
        return os.path.join('resources', 'localization', f'{language}.json')
    else:
        return os.path.join('localization', f'{language}.json')


if __name__ == '__main__':
    # manually add text
    manual_localizer = Localizer(language='English')

    while True:
        manual_localizer.text(input(": "))
