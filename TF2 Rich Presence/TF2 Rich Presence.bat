:: Copyright (C) 2018-2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
:: https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

:: This batch launcher is for debugging and functions identically to the corresponding EXE (unless modified).

@echo off
TITLE TF2 Rich Presence ({tf2rpvnum})

if not exist resources\ (
    cd ..
    if not exist resources\ (
        echo Resources folder missing, exiting
        goto bail
    )
)

start "" "resources\python-3.10.1-embed-win32\pythonw.exe" -I -B "resources\launcher.py"
goto close

:bail
pause

:close
