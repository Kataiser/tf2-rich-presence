@echo off
REM Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
REM https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

TITLE TF2 Rich Presence ({tf2rpvnum})
"%~dp0\resources\python\python.exe" -OO "%~dp0\resources\launcher.py" --m init --welcome_version 1

:start
"%~dp0\resources\python\python.exe" -OO "%~dp0\resources\launcher.py" --m main
goto start