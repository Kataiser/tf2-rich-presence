# Copyright (C) 2019  Kataiser
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

from PIL import Image

import custom_maps


def main():
    for image_filename in custom_maps.gamemodes.keys():
        print(image_filename)
        try:
            image_loaded = Image.open('map_thumbs source/' + image_filename + '.png')
        except FileNotFoundError:
            image_loaded = Image.open('map_thumbs source/' + image_filename + '.jpg')

        size_x, size_y = image_loaded.size
        out_size = 512 if size_x <= 512 else 1024
        canvas = Image.new('RGBA', (out_size, out_size), color=(0, 0, 0, 0))
        new_height = round((size_y / size_x) * out_size)
        image_scaled = image_loaded.resize((out_size, new_height), Image.LANCZOS)

        if out_size == 512:
            paste_y = 32
        elif image_filename == 'beta-map':
            paste_y = 0
        else:
            paste_y = 64
        canvas.paste(image_scaled, (0, paste_y))
        canvas.save('map_thumbs/' + image_filename + '.png')


if __name__ == '__main__':
    main()
