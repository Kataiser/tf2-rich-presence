:: Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
:: https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

:: These batch launchers are for debugging and function identically to their corresponding EXEs (unless modified).

@echo off
TITLE TF2 Rich Presence ({tf2rpvnum})

if not exist resources\ ( 
    cd ..
    if not exist resources\ ( 
        echo Resources folder missing, exiting
        goto bail
    )
)

start steam://rungameid/440
"resources\python-3.9.1-embed-win32\python.exe" -I "resources\launcher.py" --m init --welcome_version 0

:start
"resources\python-3.9.1-embed-win32\python.exe" -I "resources\launcher.py" --m main
goto start

:bail
pause