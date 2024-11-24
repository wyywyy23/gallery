import math
import os
import re

from PIL import Image, ImageOps

PHOTO_PATH = os.path.dirname(__file__) + "/../photos/"
WATERMARK_PATH = os.path.dirname(__file__) + "/../watermark.png"


def is_image_path(path):
    return re.search(r"\.(jpe?g|png|JPE?G|PNG)$", path)


def is_original(path):
    return ".min." not in path and ".placeholder." not in path


def main():
    for folder in os.listdir(PHOTO_PATH):
        # Ignore other files like .DS_Store
        if not os.path.isdir(PHOTO_PATH + folder):
            continue

        for file in os.listdir(PHOTO_PATH + folder):
            path = PHOTO_PATH + folder + "/" + file
            if is_image_path(path) and is_original(path):
                with open(path, "rb") as f:
                    im = Image.open(f)
                    im = ImageOps.exif_transpose(im)
                    width, height = im.size
                    with open(WATERMARK_PATH, "rb") as watermark_f:
                        watermark = Image.open(watermark_f)
                        watermark = ImageOps.exif_transpose(watermark)
                        width_wm, height_wm = watermark.size
                        ratio = width_wm / (max(width, height) * 0.1)
                        watermark = watermark.resize(
                            (int(width_wm / ratio), int(height_wm / ratio))
                        )
                        region = im.crop(
                            (
                                int(width / 2 - watermark.width / 2),
                                int(watermark.height / 2),
                                int(width / 2 - watermark.width / 2 + watermark.width),
                                int(watermark.height / 2 + watermark.height),
                            )
                        )
                        avg_intensity = sum(region.convert("L").getdata()) / (
                            watermark.width * watermark.height
                        )
                        wm_opacity = math.sqrt(avg_intensity / 255)
                        print(
                            f"Average intensity: {avg_intensity}, watermark opacity: {wm_opacity}"
                        )
                        watermark = watermark.convert("RGBA")
                        watermark_with_transparency = Image.new("RGBA", watermark.size)
                        for x in range(watermark.width):
                            for y in range(watermark.height):
                                r, g, b, a = watermark.getpixel((x, y))
                                watermark_with_transparency.putpixel(
                                    (x, y), (r, g, b, int(a * wm_opacity))
                                )
                        im = im.convert("RGBA")
                        im.paste(
                            watermark_with_transparency,
                            (
                                int(width / 2 - watermark_with_transparency.width / 2),
                                int(watermark_with_transparency.height / 2),
                            ),
                            watermark_with_transparency,
                        )
                        im = im.convert("RGB")
                        im.save(path)


if __name__ == "__main__":
    main()
