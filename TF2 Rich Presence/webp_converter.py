import os

from PIL import Image


def main():
    while True:
        path = "gui_images\\" + input("Image or dir path: ")
        lossless = input("Lossless (y/n): ").lower()
        quality = int(input("Quality (0-100): "))  # see the PIL docs for webp saving

        if lossless not in ('y', 'n') or not (0 <= quality <= 100):
            raise SystemError("nah b")

        if os.path.isdir(path):
            for file_name in os.listdir(path):
                file_path = os.path.join(path, file_name)
                path_out = os.path.splitext(file_path)[0] + '.webp'
                Image.open(file_path).convert('RGBA').save(path_out, lossless=lossless == 'y', quality=quality, method=6)
                print(f"{file_path} -> {path_out}")
        else:
            path_out = os.path.splitext(path)[0] + '.webp'
            Image.open(path).convert('RGBA').save(path_out, lossless=lossless == 'y', quality=quality, method=6)
            print(f"{path} -> {path_out}")


if __name__ == '__main__':
    main()
