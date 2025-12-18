import os
import re
import shutil
import sys

PHOTO_PATH = os.path.dirname(__file__) + "/../photos/"


def is_image_path(path):
    return re.search(r"\.(jpe?g|png|JPE?G|PNG)$", path)


def get_min_path(path):
    return re.sub(r"\.(png|jpe?g|PNG|JPE?G)$", r".min.\1", path)


def get_placeholder_path(path):
    return re.sub(r"\.(png|jpe?g|PNG|JPE?G)$", r".placeholder.\1", path)


def get_path(path, ext):
    return re.sub(r"\.(png|jpe?g|PNG|JPE?G)$", "." + ext + r".\1", path)


def is_original(path):
    return ".min." not in path and ".placeholder." not in path


def main(ext):
    for folder in os.listdir(PHOTO_PATH):
        # Ignore other files like .DS_Store
        if not os.path.isdir(PHOTO_PATH + folder):
            continue

        for f in os.listdir(PHOTO_PATH + folder):
            path = PHOTO_PATH + folder + "/" + f
            if is_image_path(path) and is_original(path):
                min_path = get_path(path, ext)
                shutil.copy(path, min_path)


if __name__ == "__main__":
    main(sys.argv[1])
