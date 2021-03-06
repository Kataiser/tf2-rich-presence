[![Github all releases](https://img.shields.io/github/downloads/Kataiser/tf2-rich-presence/total.svg)](https://GitHub.com/Kataiser/tf2-rich-presence/releases/)
[![GitHub release](https://img.shields.io/github/release/Kataiser/tf2-rich-presence.svg)](https://GitHub.com/Kataiser/tf2-rich-presence/releases/)
[![GitHub Release Date](https://img.shields.io/github/release-date/Kataiser/tf2-rich-presence.svg)](https://GitHub.com/Kataiser/tf2-rich-presence/releases/)
![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey?cacheSeconds=100000)
[![Kataiser on Steam](https://img.shields.io/badge/Steam-Kataiser-blue?logo=Steam)](https://steamcommunity.com/id/mechkataiser)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Kataiser-29ABE0?logo=Ko-fi)](https://ko-fi.com/kataiser)

[![GitHub commits since latest release](https://img.shields.io/github/commits-since/Kataiser/tf2-rich-presence/latest)](https://github.com/Kataiser/tf2-rich-presence/commits/master)
[![GitHub last commit](https://img.shields.io/github/last-commit/Kataiser/tf2-rich-presence.svg)](https://github.com/Kataiser/tf2-rich-presence/commits/master)
[![Updates](https://pyup.io/repos/github/Kataiser/tf2-rich-presence/shield.svg)](https://pyup.io/repos/github/Kataiser/tf2-rich-presence/)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/18a048d3a05e4815b247d886abef575f)](https://www.codacy.com/app/Kataiser/tf2-rich-presence?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Kataiser/tf2-rich-presence&amp;utm_campaign=Badge_Grade)
[![Github Actions build](https://img.shields.io/github/workflow/status/Kataiser/tf2-rich-presence/Tests%20&%20CD)](https://github.com/Kataiser/tf2-rich-presence/actions?query=workflow%3A%22Tests+%26+CD%22)
[![Coverage](https://codecov.io/gh/Kataiser/tf2-rich-presence/branch/master/graph/badge.svg?token=HOWNMW0tXB)](https://codecov.io/gh/Kataiser/tf2-rich-presence)

# TF2 Rich Presence
Discord Rich Presence for Team Fortress 2
- Detects current game state, queue info, playtime, and more
- Configurable, reliable, and performance-efficient
- Version 2 (GUI, map images, maybe more) coming soon™

![Preview image](preview.png)

(The actual program is nowhere near as nice looking as this, [v2 will be though](https://twitter.com/MechKataiser/status/1350588216043253763))

## Download
With 7-Zip's built-in extractor: [tf2_rich_presence_v1.15_self_extracting.exe](https://github.com/Kataiser/tf2-rich-presence/releases/download/v1.15/tf2_rich_presence_v1.15_self_extracting.exe) (8.8 MB)  
Extract it yourself: [tf2_rich_presence_v1.15.zip](https://github.com/Kataiser/tf2-rich-presence/releases/download/v1.15/tf2_rich_presence_v1.15.zip) (11.9 MB)  
Alternatively, get the latest autobuild (may be buggy): [tf2_rich_presence_dev.zip](https://nightly.link/Kataiser/tf2-rich-presence/workflows/Tests.CD/master/tf2_rich_presence_dev.zip)

## Installation and running
1. Extract `tf2_rich_presence_v1.15.zip` OR run `tf2_rich_presence_v1.15_self_extracting.exe`, whichever you downloaded.
2. Run `Launch TF2 with Rich Presence.exe`.
	- OR run `Launch Rich Presence alongside TF2.exe`. This one doesn't automatically start Team Fortress 2.
	- Both require Discord and Steam to be running as well and will wait until the game and both programs are running. 

For faster launching, you can add the first EXE to your taskbar/start menu/desktop/etc or to Steam as a non-Steam game. Note that having Python installed is not required.

## Changelogs
- [Changelogs.html](https://htmlpreview.github.io/?https://github.com/Kataiser/tf2-rich-presence/blob/master/Changelogs.html)
- [Releases](https://github.com/Kataiser/tf2-rich-presence/releases)

## Linux and MacOS support?
At the moment, both are considered unsupported. They probably work since [Jan200101](https://github.com/Jan200101) did some work on Linux a while ago, but the release builds are formatted for Windows. Contributors are very welcome! Also check out [cyclowns/tf2-discord](https://github.com/cyclowns/tf2-discord), which is confirmed to work on both Windows and Linux, or [EmeraldSnorlax/TF2-RPC](https://github.com/EmeraldSnorlax/TF2-RPC), which is a much less mature program but is built on Linux and theoretically cross-platform too. Alternatively, following most or all of the "building from source" instructions might work, or possibly running `python resources/launcher.py` in a --nocython build.

## VAC safe?
Almost certainly. If you don't want to risk it then fair enough, but I've run this on my main account for years and feel comfortable with it. The game's runtime and memory are never touched in any way to read its state. For transparency, here's the complete list of external files that are read from and/or written to: `\tf\console.log`, `\tf\cfg\*class*.cfg` and `steam_appid.txt` in TF2's install and `\userdata\*id*\config\localconfig.vdf` in Steam's. The game process is also queried for its start time and install path, and the server you're playing on is queried for player count or kill counts. RCON is not used.

## Malware detection
A minority of antivirus vendors see the launcher EXEs as trojans for some reason, which is a problem I haven't been able to solve. Assuming the batch to EXE converter I'm using is safe, these are entirely false positives. See [#126](https://github.com/Kataiser/tf2-rich-presence/issues/126) for more information.

## Building from source
For making and testing changes, or simply always running the most up-to-date code.
1. Either clone the repo or [download the source](https://github.com/Kataiser/tf2-rich-presence/archive/master.zip).
2. Copy the entire source to another location (sorry) and put the files outside of `TF2 Rich Presence` into that folder.
3. Make sure the `python` and `pip` commands point to Python 3.9.x (future versions should work too).
4. Install a C compiler (see [Installing Cython](http://docs.cython.org/en/latest/src/quickstart/install.html)). I personally use MinGW, but it's a pain on Windows. Alternatively, use the `--nocython` flag when building to disable compiling.
5. From within `TF2 Rich Presence`, run `pip install -r requirements.txt`.
6. Either run `python build.py` to compile and build, or `python launcher.py` to launch in debug mode.

## Version 2 goals
- ~~A GUI~~ (Done, ended up using discoIPC still)
	- I'm fairly confident I know how to implement this (it's a bit of work though)
	- Would require doing RPC with [pypresence](https://github.com/qwertyquerty/pypresence) due to a bug in [discoIPC](https://github.com/k3rn31p4nic/discoIPC)
	- Would also have the benefit of not requiring two (slow) Python interpreter launches
	- This is the only criteria I'll require for release v2.0, any of the others could be in later versions
- Run as a service
	- Idea basically stolen from [cyclowns/tf2-discord](https://github.com/cyclowns/tf2-discord)
	- Alternatively, minimize to taskbar (if possible)
- ~~Map-specific images, instead of gamemodes~~ (Done, currently at 150/150 assets though)
	- Would cause all sorts of problems, including removing the class icon style option
	- Discord art asset limit is 150, the rest of the program uses 47, and there are 118 vanilla maps in the game
	- So won't be able to get every map, can just limit to the most popular though
- A proper installer
	- Also maybe store DB.json and settings in AppData\Roaming
	- Make a [Chocolatey](https://chocolatey.org/) package as well, ideally would need to fix antivirus detection
	- Possibly include an autoupdater, either [Squirrel](https://github.com/Squirrel/Squirrel.Windows) or rolling my own
