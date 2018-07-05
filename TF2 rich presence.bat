@echo off

echo TF2 Rich Presence ({tf2rpvnum}) by Kataiser
echo https://github.com/Kataiser/tf2-rich-presence
echo

:start
"%~dp0\resources\python\python.exe" "%~dp0\resources\main.py"

goto start