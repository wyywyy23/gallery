import os
import re
import shutil

PHOTO_PATH = os.path.dirname(__file__) + "/../photos/"


def is_image_path(path):
    return re.search(r"\.(jpe?g|png|JPE?G|PNG)$", path)


def is_tmp_path(path):
    return re.search(r"\.(te?mp)$", path)


def is_original(path):
    return ".min." not in path and ".placeholder." not in path


def get_path(path, ext):
    return re.sub(r"\.(png|jpe?g|PNG|JPE?G)$", "." + ext + ".\g<1>", path)


def main():
    for folder in os.listdir(PHOTO_PATH):
        # Ignore other files like .DS_Store
        if not os.path.isdir(PHOTO_PATH + folder):
            continue

        # Rename all files to tmp with sequencial numbering
        for i, f in enumerate(os.listdir(PHOTO_PATH + folder)):
            path = PHOTO_PATH + folder + "/" + f
            if is_image_path(path) and is_original(path):
                root_ext = os.path.splitext(path)
                tmp_path = f'{PHOTO_PATH}{folder}/{folder.replace(" ", "_").lower()}_{str(i+1).zfill(3)}{root_ext[1]}.tmp'
                shutil.move(path, tmp_path)

        # Remove tmp extention from all files
        for f in os.listdir(PHOTO_PATH + folder):
            path = PHOTO_PATH + folder + "/" + f
            if is_tmp_path(path):
                root_ext = os.path.splitext(path)
                new_path = root_ext[0]
                shutil.move(path, new_path)


if __name__ == "__main__":
    main()
