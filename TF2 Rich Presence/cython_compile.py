# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import os
import shutil
from distutils.core import setup

from Cython.Build import cythonize


def main():
    # make sure to only run this from build.py or cython_compile.bat, in order to get the command line args

    targets = ('configs', 'console_log', 'custom_maps', 'detect_system_language', 'init', 'localization', 'logger', 'main', 'processes', 'settings', 'updater', 'utils', 'welcomer')
    og_cwd = os.getcwd()

    if not os.path.isdir('pyx'):
        os.mkdir('pyx')

    for target in targets:
        shutil.copy2(f'{target}.py', os.path.join('pyx', f'{target}.py'))
        os.chdir('pyx')
        setup(name=target, ext_modules=cythonize(f'{target}.py', nthreads=2, annotate=True))
        os.chdir(og_cwd)


if __name__ == '__main__':
    main()
