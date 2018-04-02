from bs4 import BeautifulSoup

gamemodes = {' Capture the Flag': 'ctf', ' Control Point': 'control-point', ' Attack/Defend': 'attack-defend', ' Attack/Defend (Medieval Mode)': 'medieval-mode',
             ' Control Point (Domination)': 'control-point', ' Territorial Control': 'territorial-control', ' Payload': 'payload', ' Payload Race': 'payload-race',
             ' King of the Hill': 'koth', ' Special Delivery': 'special-delivery', ' Mann vs. Machine': 'mvm', ' Robot Destruction': 'beta-map', ' Mannpower': 'mannpower',
             ' PASS Time': 'passtime', ' Player Destruction': 'player-destruction'}
map_gamemodes = {}

with open('List of maps - Official TF2 Wiki _ Official Team Fortress Wiki.html') as fp:
    soup = BeautifulSoup(fp, 'lxml')

for tr in soup.find_all('tr'):
    map_name, map_mode = (None, None)

    for code in tr.find_all('code'):
        map_name = code.text

    for td in tr.find_all('td'):
        td_text = td.text.rstrip('\n')
        if td_text in gamemodes.keys():
            map_mode = gamemodes[td_text]
            gamemode_fancy = td_text[1:]

    if map_mode and map_name:
        map_gamemodes[map_name] = (map_mode, gamemode_fancy)

print(map_gamemodes)
