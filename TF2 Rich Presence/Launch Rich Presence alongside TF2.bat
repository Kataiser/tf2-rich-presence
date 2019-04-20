@echo off
echo TF2 Rich Presence ({tf2rpvnum}) by Kataiser
echo https://github.com/Kataiser/tf2-rich-presence
echo.
echo Launching TF2 with Rich Presence alongside Team Fortress 2...
echo.

"%~dp0\resources\python\python.exe" "%~dp0\resources\launcher.py" updater

:start
"%~dp0\resources\python\python.exe" "%~dp0\resources\launcher.py" main

goto start