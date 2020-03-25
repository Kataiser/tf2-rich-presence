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

    if not os.path.isdir('cython_build'):
        os.mkdir('cython_build')

    for target in targets:
        target_py = f'{target}.py'
        shutil.copy2(target_py, os.path.join('cython_build', target_py))
        os.chdir('cython_build')
        print(f"{target_py}: ", end='')
        setup(name=target, ext_modules=cythonize(target_py, nthreads=2, annotate=True))
        os.chdir(og_cwd)


if __name__ == '__main__':
    main()
