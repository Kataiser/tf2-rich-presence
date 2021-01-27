# Copyright (C) 2018-2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

from PIL import Image

import gamemodes


def main():
    modes = list(gamemodes.modes) + ['unknown']
    # these are to make the cropping a bit better
    fg_override_coords = {'jumping': 0, 'achievement': 0, 'attack-defend': 65, 'control-point': 245, 'ctf': 48, 'deathmatch': 0, 'deathrun': 45, 'koth': 28, 'medieval-mode': 20,
                          'mvm': 87, 'passtime': 70, 'payload': 0, 'payload-race': 480, 'surfing': 0, 'territorial-control': 92, 'trading': 52, 'mannpower': 381}

    for image_filename in modes:
        print(image_filename)
        image_loaded = Image.open(f'gamemode_images\\{image_filename}.png').convert('RGB')

        # backgrounds
        if image_loaded.size[0] > 500:
            image_scaled_bg = image_loaded.resize((500, 312), Image.LANCZOS)
            image_cropped_bg = image_scaled_bg.crop((0, 31, 500, 281))
            image_cropped_bg.save(f'gui_images\\bg_modes\\{image_filename}.webp', quality=75, method=6)
        else:
            crops = {320: (0, 20, 320, 180), 315: (0, 19, 315, 177), 360: (0, 10, 360, 190)}
            image_cropped_bg = image_loaded.crop(crops[image_loaded.size[0]])
            image_cropped_bg.save(f'gui_images\\bg_modes\\{image_filename}.webp', quality=75, method=6)

        if image_filename == 'unknown':
            continue  # don't need fg or discord images for this

        # crop into squares
        if image_filename in fg_override_coords:
            crop_left = fg_override_coords[image_filename]
            crop_right = fg_override_coords[image_filename] + image_loaded.size[1]
        else:
            crop_left = (image_loaded.size[0] / 2) - (image_loaded.size[1] / 2)
            crop_right = (image_loaded.size[0] / 2) + (image_loaded.size[1] / 2)
        image_cropped = image_loaded.crop((crop_left, 0, crop_right, (image_loaded.size[1])))

        # foregrounds
        image_scaled_fg = image_cropped.resize((240, 240), resample=Image.LANCZOS)
        image_scaled_fg.save(f'gui_images\\fg_modes\\{image_filename}.webp', quality=85, method=6)

        # Discord
        image_scaled_discord = image_cropped.resize((512, 512), resample=Image.LANCZOS)
        image_scaled_discord.save(f'gamemode_images_discord\\{image_filename}.png')


if __name__ == '__main__':
    main()
