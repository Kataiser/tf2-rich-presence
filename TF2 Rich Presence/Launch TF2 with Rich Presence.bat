@echo off
echo TF2 Rich Presence ({tf2rpvnum}) by Kataiser
echo https://github.com/Kataiser/tf2-rich-presence
echo.
echo Launching Team Fortress 2, with Rich Presence enabled, via your default browser...
echo.

start "" steam://rungameid/440
"%~dp0\resources\python\python.exe" "%~dp0\resources\updater.py"

:start
"%~dp0\resources\python\python.exe" "%~dp0\resources\main.py"

goto start