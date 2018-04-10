import json

import requests
from bs4 import BeautifulSoup

gamemodes = {'Capture the Flag': 'ctf', 'Control Point': 'control-point', 'Attack/Defend': 'attack-defend', 'Attack/Defend (Medieval Mode)': 'medieval-mode',
             'Control Point (Domination)': 'control-point', 'Territorial Control': 'territorial-control', 'Payload': 'payload', 'Payload Race': 'payload-race',
             'King of the Hill': 'koth', 'Special Delivery': 'special-delivery', 'Mann vs. Machine': 'mvm', 'Robot Destruction': 'beta-map', 'Mannpower': 'mannpower',
             'PASS Time': 'passtime', 'Player Destruction': 'player-destruction', 'Attack/Defend(Medieval Mode)': 'attack-defend', 'Control Point(Domination)': 'control-point'}
map_gamemodes = {}

r = requests.get('https://wiki.teamfortress.com/wiki/List_of_maps')
soup = BeautifulSoup(r.text, 'lxml')

for tr in soup.find_all('tr'):
    map_file, map_name, map_mode = (None, None, None)

    for code in tr.find_all('code'):
        map_file = code.text

    for bold in tr.find_all('b'):
        map_name = bold.text

    for td in tr.find_all('td'):
        td_text = td.text[1:-1]
        if td_text in gamemodes.keys():
            map_mode = gamemodes[td_text]
            gamemode_fancy = td_text

    if map_mode and map_name:
        gamemode_fancy = gamemode_fancy.replace('d(M', 'd (M')
        gamemode_fancy = gamemode_fancy.replace('t(D', 't (D')
        map_gamemodes[map_file] = (map_name, map_mode, gamemode_fancy)

print(map_gamemodes)

with open('maps.json', 'w') as maps_db:
    json.dump(map_gamemodes, maps_db, indent=4)
