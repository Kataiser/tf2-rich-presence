:: Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
:: https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

:: Note that these batch launchers don't work from the resources folder (intentionally) and must be moved
:: one folder up. They are for debugging and function identically to their corresponding EXEs (unless modified).

@echo off

if not exist resources\ ( 
    echo Resources folder missing, exiting
    goto bail
)

start "" "%~dp0\resources\python-3.7.9-embed-win32\pythonw.exe" -I -OO "%~dp0\resources\launcher.py" --m settings
goto close

:bail
pause

:close