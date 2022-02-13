:: Copyright (C) 2018-2022 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
:: https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

@echo off
TITLE TF2 Rich Presence ({tf2rpvnum})
cd "%~dp0"

if not exist resources\ (
    cd ..
    if not exist resources\ (
        echo Resources folder missing, exiting
        goto bail
    )
)

start "" "resources\python-3.10.2-embed-win32\pythonw.exe" -I -B "resources\launcher.py"
goto close

:bail
pause

:close
