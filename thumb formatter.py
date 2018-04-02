from PIL import Image

gamemodes = {'Capture the Flag': 'ctf', 'Control Point': 'control-point', 'Attack/Defend': 'attack-defend', 'Attack/Defend (Medieval Mode)': 'medieval-mode',
             'Control Point (Domination)': 'control-point', 'Territorial Control': 'territorial-control', 'Payload': 'payload', 'Payload Race': 'payload-race',
             'King of the Hill': 'koth', 'Special Delivery': 'special-delivery', 'Mann vs. Machine': 'mvm', 'Robot Destruction': 'beta-map', 'Mannpower': 'mannpower',
             'PASS Time': 'passtime', 'Player Destruction': 'player-destruction'}

for image_filename in gamemodes.values():
    image_loaded = Image.open('map_thumbs - Copy/' + image_filename + '.png')
    canvas = Image.new('RGBA', (512, 512), color=(0, 0, 0, 0))
    size_x, size_y = image_loaded.size
    new_height = round((size_y / size_x) * 512)
    image_scaled = image_loaded.resize((512, new_height), Image.LANCZOS)
    canvas.paste(image_scaled, (0, 32))
    canvas.save('map_thumbs/' + image_filename + '.png')
