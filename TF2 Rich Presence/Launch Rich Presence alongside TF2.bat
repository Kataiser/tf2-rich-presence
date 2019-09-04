@echo off
REM Copyright (C) 2019  Kataiser
REM https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

TITLE TF2 Rich Presence {tf2rpvnum}

"%~dp0\resources\python\python.exe" -OO "%~dp0\resources\welcomer.py" --v 2
"%~dp0\resources\python\python.exe" -OO "%~dp0\resources\launcher.py" --m detect_system_language
"%~dp0\resources\python\python.exe" -OO "%~dp0\resources\launcher.py" --m updater

:start
"%~dp0\resources\python\python.exe" -OO "%~dp0\resources\launcher.py" --m main
goto start