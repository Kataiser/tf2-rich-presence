# Copyright (C) 2018-2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

import io
import os
import shutil
import time

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageEnhance, ImageStat

try:
    import requests_cache
except ImportError:
    requests_cache = None


def main():
    # downloads a screenshot of every map and then crops and resizes it for Discord and the GUI
    # maybe don't read this code if you don't need to

    if requests_cache:
        print("Using DL cache")
        requests_cache.install_cache('tf2maps_dl_cache')
    else:
        print("Not using DL cache, install requests_cache")

    if os.path.isdir('gui_images\\fg_maps'):
        shutil.rmtree('gui_images\\fg_maps')
    if os.path.isdir('map_pics_discord'):
        shutil.rmtree('map_pics_discord')

    time.sleep(0.1)
    os.mkdir('gui_images\\fg_maps')
    os.mkdir('map_pics_discord')

    map_datas = [('background01', '/wiki/Background01'), ('devtest', '/wiki/Devtest')]
    excluded = ('cp_5gorge', 'cp_granary', 'arena_nucleus', 'ctf_foundry', 'arena_sawmill', 'ctf_sawmill', 'arena_badlands', 'koth_badlands', 'tr_dustbowl', 'ctf_thundermountain',
                'ctf_well', 'arena_well')
    overrides = {'mvm_coaltown': '/wiki/File:Coal_Town_base.png', 'mvm_decoy': '/wiki/File:Decoy_left_lane.png', 'mvm_mannworks': '/wiki/File:Mannworks_left_lane.jpg'}

    list_page_r = requests.get('https://wiki.teamfortress.com/wiki/List_of_maps')
    list_page = BeautifulSoup(list_page_r.text, 'lxml')
    map_entries = list_page.find_all('table')[1].find_all('tr')[1:]

    for map_entry in map_entries:
        map_datas.append((map_entry.find('code').text, map_entry.find_all('a')[1].get('href')))

    for map_data in enumerate(map_datas):
        map_file = map_data[1][0]
        print(f"\n({map_data[0] + 1}/{len(map_datas)}) {map_file}", end=' ')

        if map_file in excluded:
            print("(skipped)", end='')
            continue

        map_page_r = requests.get(f'https://wiki.teamfortress.com{map_data[1][1]}')
        map_page = BeautifulSoup(map_page_r.text, 'lxml')
        found_image = False

        for table in map_page.find_all('table'):
            if table.get('class')[0] == 'infobox':
                if map_file in overrides:
                    image_page_url = overrides[map_file]
                else:
                    image_page_url = table.find('a').get('href')

                image_page_r = requests.get(f'https://wiki.teamfortress.com{image_page_url}')
                image_page = BeautifulSoup(image_page_r.text, 'lxml')

                for a2 in image_page.find_all('a'):
                    if a2.text == "Original file" or a2.text == image_page_url.split(':')[-1]:
                        found_image = True
                        image_url = f"https://wiki.teamfortress.com{a2.get('href')}"
                        print(image_url, end='')
                        image_dl = requests.get(image_url).content
                        image_loaded = Image.open(io.BytesIO(image_dl)).convert('RGB')
                        print(f" {len(image_dl)} b {image_loaded.size}", end='')
                        crop_left = (image_loaded.size[0] / 2) - (image_loaded.size[1] / 2)
                        crop_right = (image_loaded.size[0] / 2) + (image_loaded.size[1] / 2)
                        image_cropped = image_loaded.crop((crop_left, 0, crop_right, (image_loaded.size[1])))
                        color_mean = sum(ImageStat.Stat(image_cropped).mean)

                        if color_mean < 300:
                            brighten = 1 + ((300 - color_mean) / 300)
                            brightener = ImageEnhance.Brightness(image_cropped)
                            image_cropped = brightener.enhance(brighten)
                            print(f" {int(color_mean)}", end='')

                        image_scaled_gui = image_cropped.resize((240, 240), resample=Image.LANCZOS)
                        image_scaled_discord = image_cropped.resize((512, 512), resample=Image.LANCZOS)
                        image_scaled_gui.save(f'gui_images\\fg_maps\\{map_file}.webp', lossless=False, quality=85, method=6)
                        image_scaled_discord.save(f'map_pics_discord\\z_{map_file}.jpg', quality=95, optimize=True, progressive=True, subsampling=0)

                        break

                break

        if not found_image:
            raise SystemError


if __name__ == '__main__':
    main()
