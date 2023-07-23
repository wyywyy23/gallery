#!/usr/bin/env python

from PIL import Image, ImageOps
import struct
import os
import sys
import json
import re

PATH = os.path.abspath(os.path.dirname(__file__) + "/../")
RELATIVE_PATH = "photos"
PHOTO_PATH = PATH + "/" + RELATIVE_PATH


def is_original(path):
    return ".min." not in path and ".placeholder." not in path and is_image_path(path)


def is_not_min_path(path):
    return not is_min_path(path) and is_image_path(path)


def is_min_path(path):
    return ".min." in path and is_image_path(path)


def get_directories():
    items = os.listdir(PHOTO_PATH)
    return list(filter(lambda x: os.path.isdir(PHOTO_PATH + "/" + x), items))


def is_image_path(path):
    return re.search(r"\.(jpe?g|png|JPE?G|PNG)$", path)


def get_placeholder_path(path):
    return get_path(path, "placeholder")


def get_min_path(path):
    return get_path(path, "min")


def get_path(path, ext):
    return re.sub(r"\.(png|jpe?g|PNG|JPE?G)$", "." + ext + ".\g<1>", path)


def get_images(path):
    items = os.listdir(PHOTO_PATH + "/" + path)
    filtered_items = list(filter(is_original, items))

    result = []
    for img in filtered_items:
        width, height = 0, 0
        has_compressed = False
        p = "./" + RELATIVE_PATH + "/" + path + "/" + img
        with open(PHOTO_PATH + "/" + path + "/" + img, "rb") as f:
            im = Image.open(f)
            im = ImageOps.exif_transpose(im)
            width, height = im.size
        if os.path.isfile(get_min_path(p)):
            has_compressed = True
        result.append(
            {
                "width": width,
                "height": height,
                "path": "./" + RELATIVE_PATH + "/" + path + "/" + img,
                "compressed_path": get_min_path(p),
                "compressed": has_compressed,
                "placeholder_path": get_placeholder_path(p),
            }
        )
    return result


def write_config(config):
    with open(PATH + "/config.json", "w") as f:
        f.write(json.dumps(config, indent=2, separators=(",", ": ")))


def run():
    print("Starting to collect all albums within the /photos directory...")
    config = {}
    dirs = sorted(get_directories(), reverse=True)
    print("Found {length} directories".format(length=len(dirs)))
    for i, path in enumerate(dirs):
        print(
            str(i + 1)
            + ': Processing photos for the album "{album}"'.format(album=path)
        )
        config[path] = get_images(path)

        print(
            '   Done processing {l} photos for "{album}"\n'.format(
                l=len(config[path]), album=path
            )
        )

    print("Done processing all {length} albums".format(length=len(dirs)))
    print("Writing files to {path} now...".format(path=PATH + "/config.json"))
    write_config(config)
    print(
        """Done writing! You may now safely close this window :)

Thank you for using gallery! Share your gallery on Github!
https://github.com/andyzg/gallery/issues/1"""
    )
    return 0


if __name__ == "__main__":
    sys.exit(run())
