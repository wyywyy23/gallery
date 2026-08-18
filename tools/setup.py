#!/usr/bin/env python

import json
import math
import os
import re
import sys

from PIL import Image, ImageOps

PATH = os.path.abspath(os.path.dirname(__file__) + "/../")
RELATIVE_PATH = "photos"
PHOTO_PATH = PATH + "/" + RELATIVE_PATH
COLOR_SAMPLE_SIZE = 64

try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE = Image.LANCZOS

# Unit-vector approximation of the blue/purple -> orange/red opponent axis in
# OKLab's a/b plane. Higher scores look perceptually warmer.
COLOR_AXIS_A = 0.47
COLOR_AXIS_B = 0.88


def is_original(path):
    return ".min." not in path and ".placeholder." not in path and is_image_path(path)


def is_not_min_path(path):
    return not is_min_path(path) and is_image_path(path)


def is_min_path(path):
    return ".min." in path and is_image_path(path)


def get_directories():
    items = sorted(os.listdir(PHOTO_PATH))
    return list(filter(lambda x: os.path.isdir(PHOTO_PATH + "/" + x), items))


def is_image_path(path):
    return re.search(r"\.(jpe?g|png|JPE?G|PNG)$", path)


def get_placeholder_path(path):
    return get_path(path, "placeholder")


def get_min_path(path):
    return get_path(path, "min")


def get_path(path, ext):
    return re.sub(r"\.(png|jpe?g|PNG|JPE?G)$", "." + ext + r".\1", path)


def srgb_to_linear(value):
    value = value / 255.0
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def rgb_to_oklab(pixel):
    red, green, blue = (srgb_to_linear(value) for value in pixel)
    light = 0.4122214708 * red + 0.5363325363 * green + 0.0514459929 * blue
    medium = 0.2119034982 * red + 0.6806995451 * green + 0.1073969566 * blue
    short = 0.0883024619 * red + 0.2817188376 * green + 0.6299787005 * blue

    light = max(light, 0) ** (1 / 3)
    medium = max(medium, 0) ** (1 / 3)
    short = max(short, 0) ** (1 / 3)

    return (
        0.2104542553 * light + 0.7936177850 * medium - 0.0040720468 * short,
        1.9779984951 * light - 2.4285922050 * medium + 0.4505937099 * short,
        0.0259040371 * light + 0.7827717662 * medium - 0.8086757660 * short,
    )


def color_sort_key(image):
    """Return a perceptual blue/purple-to-orange/red score for an image."""
    sample = ImageOps.exif_transpose(image).convert("RGB")
    sample.thumbnail((COLOR_SAMPLE_SIZE, COLOR_SAMPLE_SIZE), RESAMPLE)

    weighted_a = 0.0
    weighted_b = 0.0
    total_weight = 0.0
    for pixel in sample.getdata():
        lightness, axis_a, axis_b = rgb_to_oklab(pixel)
        chroma = math.hypot(axis_a, axis_b)

        # Saturated midtones carry more of a photo's perceived color than
        # neutral highlights or crushed shadows, while every pixel still gets
        # some weight so monochrome images remain stable.
        chroma_weight = 0.05 + min((chroma / 0.12) ** 2, 4.0)
        tone_weight = max(0.2, 1.0 - abs(lightness - 0.55) * 1.4)
        weight = chroma_weight * tone_weight

        weighted_a += axis_a * weight
        weighted_b += axis_b * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    average_a = weighted_a / total_weight
    average_b = weighted_b / total_weight
    return round(COLOR_AXIS_A * average_a + COLOR_AXIS_B * average_b, 6)


def get_images(path):
    items = sorted(os.listdir(PHOTO_PATH + "/" + path))
    filtered_items = list(filter(is_original, items))

    result = []
    for img in filtered_items:
        width, height = 0, 0
        has_compressed = False
        p = "./" + RELATIVE_PATH + "/" + path + "/" + img
        original_path = PHOTO_PATH + "/" + path + "/" + img
        with open(original_path, "rb") as f:
            im = Image.open(f)
            im = ImageOps.exif_transpose(im)
            width, height = im.size
        if os.path.isfile(get_min_path(p)):
            has_compressed = True
        color_source = get_min_path(original_path) if has_compressed else original_path
        with Image.open(color_source) as im:
            color_sort = color_sort_key(im)
        result.append(
            {
                "width": width,
                "height": height,
                "path": "./" + RELATIVE_PATH + "/" + path + "/" + img,
                "compressed_path": get_min_path(p),
                "compressed": has_compressed,
                "placeholder_path": get_placeholder_path(p),
                "color_sort": color_sort,
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
        """Done writing config.json."""
    )
    return 0


if __name__ == "__main__":
    sys.exit(run())
